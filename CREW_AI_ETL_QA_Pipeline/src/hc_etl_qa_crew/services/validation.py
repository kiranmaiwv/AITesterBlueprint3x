"""Deterministic post-stage validation.

Pydantic proves the shape is right. These checks prove the *content* hangs
together: no duplicate ids, no dangling references, no empty sections, no
coverage claim that the artifacts do not support.

Every check returns warnings (the run continues, flagged) or errors (the run
cannot proceed).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hc_etl_qa_crew.models import (
    AutomationCandidate,
    AutomationReadiness,
    PytestBundle,
    ReconcilePlan,
    SchemaAnalysis,
    TestCaseSuite,
)

#: Patterns that must never appear in generated pytest code.
FORBIDDEN_CODE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("time.sleep", "hard sleep is banned; pytest waits on state"),
    ("sleep(", "hard sleep is banned"),
    ("subprocess", "subprocess execution is banned in generated tests"),
    ("os.system", "os.system is banned in generated tests"),
    ("eval(", "eval is banned in generated tests"),
    ("exec(", "exec is banned in generated tests"),
    ("xpath=", "XPath has no meaning in SQL tests"),
)

#: Rough secret detectors for generated code. Deliberately blunt.
SECRET_CODE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("password:", "possible hard-coded password"),
    ("password =", "possible hard-coded password"),
    ("api_key", "possible hard-coded API key"),
    ("apiKey:", "possible hard-coded API key"),
    ("Bearer ey", "possible hard-coded bearer token"),
    ("sk-", "possible hard-coded secret key"),
)


@dataclass
class ValidationResult:
    """Outcome of one validation pass."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def merge(self, other: ValidationResult) -> ValidationResult:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self


# --------------------------------------------------------------------------
def validate_analysis(analysis: SchemaAnalysis, pipeline_name: str) -> ValidationResult:
    result = ValidationResult()

    if analysis.pipeline_name.strip().lower() != pipeline_name.strip().lower():
        result.errors.append(
            f"Analysis is for {analysis.pipeline_name!r} but this run is {pipeline_name!r}"
        )

    req_ids = [e.id for e in analysis.entities if e.entity_type == "requirement"]
    dq_ids = [e.id for e in analysis.entities if e.entity_type == "data_quality"]
    result.merge(_duplicate_check(req_ids, "requirement"))
    result.merge(_duplicate_check(dq_ids, "data-quality rule"))

    if not analysis.entities:
        result.errors.append("No requirements or data-quality rules were extracted")

    for entity in analysis.entities:
        if entity.provenance.value == "EXPLICIT" and not entity.source_quote.strip():
            result.warnings.append(
                f"{entity.id} is marked EXPLICIT but carries no source quote"
            )

    if not dq_ids and not analysis.missing_information:
        result.warnings.append(
            "No data-quality rule was extracted and no missing_information "
            "entry explains why"
        )
    return result


# --------------------------------------------------------------------------
def validate_recon_plan(
    plan: ReconcilePlan, analysis: SchemaAnalysis, pipeline_name: str
) -> ValidationResult:
    result = ValidationResult()

    if plan.pipeline_name.strip().lower() != pipeline_name.strip().lower():
        result.errors.append(
            f"Reconciliation plan is for {plan.pipeline_name!r} but this run is {pipeline_name!r}"
        )

    if not plan.strategies:
        result.warnings.append("The reconciliation plan lists no strategies")
    if not plan.quality_rules:
        result.warnings.append("The reconciliation plan lists no quality rules")

    known = {r.id for r in analysis.entities}
    for rule in plan.quality_rules:
        if rule.id.strip().upper() not in known:
            result.warnings.append(
                f"Quality rule {rule.id} is not defined in the schema analysis"
            )
    return result


# --------------------------------------------------------------------------
def validate_test_cases(
    suite: TestCaseSuite, analysis: SchemaAnalysis, pipeline_name: str
) -> ValidationResult:
    result = ValidationResult()
    key = pipeline_name.strip().lower()

    if suite.pipeline_name.strip().lower() != key:
        result.errors.append(
            f"Test suite is for {suite.pipeline_name!r} but this run is {key!r}"
        )

    result.merge(_duplicate_check([c.id for c in suite.test_cases], "test case"))

    known_req = {e.id for e in analysis.entities if e.entity_type == "requirement"}
    known_dq = {e.id for e in analysis.entities if e.entity_type == "data_quality"}
    known = known_req | known_dq

    for case in suite.test_cases:
        if not case.id.startswith("CLAIMS_ETL_V1-TC-"):
            result.warnings.append(
                f"Test case id {case.id} does not start with CLAIMS_ETL_V1-TC-"
            )
        refs = [r.strip().upper() for r in (*case.requirement_ids, *case.data_quality_ids)]
        unknown = [r for r in refs if r not in known]
        if unknown:
            result.errors.append(
                f"{case.id} references ids that do not exist in the analysis: "
                + ", ".join(sorted(set(unknown)))
            )
        if not case.expected_result.strip():
            result.warnings.append(f"{case.id} has no expected result")
        if (
            case.automation_candidate is not AutomationCandidate.NO
            and not case.automation_rationale.strip()
        ):
            result.warnings.append(
                f"{case.id} is an automation candidate but gives no rationale"
            )

    # Every data-quality rule needs at least one positive case.
    covered: set[str] = set()
    for case in suite.test_cases:
        covered.update(r.strip().upper() for r in case.data_quality_ids)
    for dq_id in sorted(known_dq - covered):
        result.warnings.append(f"{dq_id} has no test case covering it")
    return result


# --------------------------------------------------------------------------
def validate_pytest(
    bundle: PytestBundle, suite: TestCaseSuite, pipeline_name: str
) -> ValidationResult:
    result = ValidationResult()
    key = pipeline_name.strip().lower()

    if bundle.pipeline_name.strip().lower() != key:
        result.errors.append(
            f"Pytest bundle is for {bundle.pipeline_name!r} but this run is {key!r}"
        )

    if not bundle.files:
        result.errors.append("The pytest bundle contains no files")

    case_ids = {c.id for c in suite.test_cases}
    automatable = {
        c.id
        for c in suite.test_cases
        if c.automation_candidate in (AutomationCandidate.YES, AutomationCandidate.PARTIAL)
    }

    for trace in bundle.traces:
        tc_id = trace.test_case_id.strip().upper()
        if tc_id not in case_ids:
            result.errors.append(
                f"Automated test {trace.test_name!r} traces to unknown test case {tc_id}"
            )
        elif tc_id not in automatable:
            result.warnings.append(
                f"{tc_id} was automated but is marked automation_candidate=No"
            )

    traced = {t.test_case_id.strip().upper() for t in bundle.traces}
    for missing in sorted(automatable - traced):
        result.warnings.append(f"{missing} is an automation candidate but was not automated")

    for file in bundle.files:
        lowered = file.content.lower()
        for needle, message in FORBIDDEN_CODE_PATTERNS:
            if needle.lower() in lowered:
                result.errors.append(f"{file.path}: {message}")
        for needle, message in SECRET_CODE_PATTERNS:
            if needle.lower() in lowered:
                result.warnings.append(f"{file.path}: {message}")
        if file.kind == "test" and "def test_" not in file.content:
            result.errors.append(
                f"{file.path}: contains no test_ functions, so pytest cannot collect it. "
                "If nothing is automatable, return an empty file list with "
                "readiness=NOT_APPLICABLE instead of an empty test module."
            )
        if file.kind == "test" and "import pytest" not in file.content:
            result.warnings.append(f"{file.path}: does not import pytest")

    has_placeholder = any(
        marker in f.content.upper() for f in bundle.files for marker in ("TODO", "PLACEHOLDER")
    )
    if bundle.readiness is AutomationReadiness.READY and has_placeholder:
        result.errors.append(
            "readiness=READY but the generated code still contains TODO/PLACEHOLDER markers"
        )
    if (
        bundle.readiness is AutomationReadiness.NEEDS_CONFIGURATION
        and not bundle.missing_information
    ):
        result.warnings.append(
            "readiness=NEEDS_CONFIGURATION but missing_information is empty"
        )
    return result


# --------------------------------------------------------------------------
def _duplicate_check(ids: list[str], label: str) -> ValidationResult:
    result = ValidationResult()
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in ids:
        normalized = value.strip().upper()
        if normalized in seen:
            duplicates.add(normalized)
        seen.add(normalized)
    if duplicates:
        result.errors.append(f"Duplicate {label} ids: {', '.join(sorted(duplicates))}")
    return result
