"""Tests for deterministic post-stage validation."""

from __future__ import annotations

from hc_etl_qa_crew.models import (
    AutomationCandidate,
    AutomationReadiness,
    PytestBundle,
    PytestFile,
    SchemaAnalysis,
    SchemaEntity,
    TestCase,
    TestCaseSuite,
    TestStep,
)
from hc_etl_qa_crew.services.validation import (
    ValidationResult,
    validate_analysis,
    validate_pytest,
    validate_test_cases,
)


def _analysis() -> SchemaAnalysis:
    return SchemaAnalysis(
        pipeline_name="claims_etl_v1",
        fact_table="fact_claim_line",
        dimension_tables=["dim_member"],
        entities=[
            SchemaEntity(
                id="REQ-001",
                entity_type="requirement",
                text="Fact rows must join to a member",
                table_name="fact_claim_line",
                source_quote="member_sk",
            ),
            SchemaEntity(
                id="DQ-001",
                entity_type="data_quality",
                text="member_sk must not be null",
                table_name="fact_claim_line",
                source_quote="not null",
            ),
        ],
    )


def _case(case_id="CLAIMS_ETL_V1-TC-001", **overrides) -> TestCase:
    base = {
        "id": case_id,
        "pipeline_name": "claims_etl_v1",
        "title": "no orphan members",
        "table_name": "fact_claim_line",
        "column_name": "member_sk",
        "requirement_ids": ["REQ-001"],
        "data_quality_ids": ["DQ-001"],
        "steps": [TestStep(number=1, action="run check", expected="0 rows")],
        "expected_result": "clean",
        "automation_candidate": AutomationCandidate.YES,
        "automation_rationale": "deterministic SQL",
    }
    base.update(overrides)
    return TestCase(**base)


def _suite(cases) -> TestCaseSuite:
    return TestCaseSuite(pipeline_name="claims_etl_v1", test_cases=cases)


# --------------------------------------------------------------------------
def test_validation_result_merge() -> None:
    left = ValidationResult(errors=["a"], warnings=["w"])
    left.merge(ValidationResult(errors=["b"]))
    assert left.errors == ["a", "b"]
    assert left.warnings == ["w"]
    assert not left.ok


# --------------------------------------------------------------------------
def test_validate_analysis_ok() -> None:
    result = validate_analysis(_analysis(), "claims_etl_v1")
    assert result.ok
    assert result.errors == []


def test_validate_analysis_wrong_pipeline() -> None:
    result = validate_analysis(_analysis(), "other_v1")
    assert not result.ok
    assert any("other_v1" in e for e in result.errors)


def test_validate_analysis_duplicate_requirement_ids() -> None:
    analysis = _analysis()
    analysis.entities.append(
        SchemaEntity(
            id="REQ-001",
            entity_type="requirement",
            text="duplicate",
            table_name="fact_claim_line",
        )
    )
    result = validate_analysis(analysis, "claims_etl_v1")
    assert not result.ok
    assert any("Duplicate requirement" in e for e in result.errors)


def test_validate_analysis_empty_entities() -> None:
    analysis = _analysis()
    analysis.entities = []
    result = validate_analysis(analysis, "claims_etl_v1")
    assert not result.ok
    assert any("No requirements or data-quality rules" in e for e in result.errors)


def test_validate_analysis_explicit_without_quote_is_warning() -> None:
    analysis = _analysis()
    analysis.entities[0].source_quote = ""
    result = validate_analysis(analysis, "claims_etl_v1")
    assert result.ok  # warnings only
    assert any("source quote" in w for w in result.warnings)


def test_validate_analysis_no_dq_and_no_explanation_warns() -> None:
    analysis = _analysis()
    analysis.entities = [analysis.entities[0]]  # keep only REQ-001
    result = validate_analysis(analysis, "claims_etl_v1")
    assert result.ok
    assert any("No data-quality rule" in w for w in result.warnings)


# --------------------------------------------------------------------------
def test_validate_test_cases_ok() -> None:
    result = validate_test_cases(_suite([_case()]), _analysis(), "claims_etl_v1")
    assert result.ok


def test_validate_test_cases_unknown_reference_is_error() -> None:
    case = _case(data_quality_ids=["DQ-999"])
    result = validate_test_cases(_suite([case]), _analysis(), "claims_etl_v1")
    assert not result.ok
    assert any("DQ-999" in e for e in result.errors)


def test_validate_test_cases_duplicate_ids() -> None:
    # The model itself forbids duplicates at construction, so build a valid
    # suite and inject a duplicate afterwards to exercise the service check.
    suite = _suite([_case(), _case(case_id="CLAIMS_ETL_V1-TC-002")])
    suite.test_cases[1].id = "CLAIMS_ETL_V1-TC-001"
    result = validate_test_cases(suite, _analysis(), "claims_etl_v1")
    assert not result.ok
    assert any("Duplicate test case" in e for e in result.errors)


def test_validate_test_cases_uncovered_dq_warns() -> None:
    case = _case(data_quality_ids=[])
    # REQ-001 still traced; DQ-001 has no case
    result = validate_test_cases(_suite([case]), _analysis(), "claims_etl_v1")
    assert result.ok
    assert any("DQ-001 has no test case" in w for w in result.warnings)


def test_validate_test_cases_no_rationale_for_automation_warns() -> None:
    case = _case(automation_rationale="")
    result = validate_test_cases(_suite([case]), _analysis(), "claims_etl_v1")
    assert result.ok
    assert any("automation candidate but gives no rationale" in w for w in result.warnings)


def test_validate_test_cases_wrong_pipeline() -> None:
    suite = _suite([_case()])
    suite.pipeline_name = "other"
    result = validate_test_cases(suite, _analysis(), "claims_etl_v1")
    assert not result.ok


# --------------------------------------------------------------------------
def _bundle(**overrides) -> PytestBundle:
    base = {
        "pipeline_name": "claims_etl_v1",
        "files": [
            PytestFile(
                path="tests/test_claims_etl_v1.py",
                content=(
                    "import pytest\n"
                    "def test_no_orphan_members():\n    assert True\n"
                ),
                kind="test",
            )
        ],
        "traces": [
            {
                "test_name": "test_no_orphan_members",
                "test_case_id": "CLAIMS_ETL_V1-TC-001",
                "pipeline_name": "claims_etl_v1",
                "requirement_ids": ["REQ-001"],
                "data_quality_ids": ["DQ-001"],
            }
        ],
        "readiness": AutomationReadiness.NEEDS_CONFIGURATION,
        "missing_information": ["connection string"],
    }
    base.update(overrides)
    return PytestBundle(**base)


def test_validate_pytest_ok() -> None:
    suite = _suite([_case()])
    result = validate_pytest(_bundle(), suite, "claims_etl_v1")
    assert result.ok


def test_validate_pytest_trace_to_unknown_case_is_error() -> None:
    bundle = _bundle()
    bundle.traces[0].test_case_id = "CLAIMS_ETL_V1-TC-999"
    result = validate_pytest(bundle, _suite([_case()]), "claims_etl_v1")
    assert not result.ok
    assert any("unknown test case" in e for e in result.errors)


def test_validate_pytest_automates_manual_case_warns() -> None:
    case = _case(automation_candidate=AutomationCandidate.NO)
    bundle = _bundle()
    result = validate_pytest(bundle, _suite([case]), "claims_etl_v1")
    assert result.ok
    assert any("marked automation_candidate=No" in w for w in result.warnings)


def test_validate_pytest_forbids_sleep_and_subprocess() -> None:
    case = _case()
    suite = _suite([case])
    bad_content = (
        "import pytest, time\n"
        "def test_no_orphan_members():\n"
        "    time.sleep(5)\n"
    )
    bundle = _bundle(
        files=[PytestFile(path="tests/test_claims_etl_v1.py", content=bad_content, kind="test")]
    )
    result = validate_pytest(bundle, suite, "claims_etl_v1")
    assert not result.ok
    assert any("hard sleep" in e for e in result.errors)


def test_validate_pytest_no_test_functions_is_error() -> None:
    bundle = _bundle(
        files=[PytestFile(path="tests/test_claims_etl_v1.py", content="import pytest\n", kind="test")]
    )
    result = validate_pytest(bundle, _suite([_case()]), "claims_etl_v1")
    assert not result.ok
    assert any("no test_ functions" in e for e in result.errors)


def test_validate_pytest_ready_with_placeholder_is_error() -> None:
    case = _case()
    suite = _suite([case])
    content = (
        "import pytest\n"
        "def test_no_orphan_members():\n"
        "    # TODO: fill the DSN\n"
        "    assert True\n"
    )
    bundle = _bundle(
        files=[PytestFile(path="tests/test_claims_etl_v1.py", content=content, kind="test")],
        readiness=AutomationReadiness.READY,
        missing_information=[],
    )
    result = validate_pytest(bundle, suite, "claims_etl_v1")
    assert not result.ok
    assert any("TODO/PLACEHOLDER" in e for e in result.errors)


def test_validate_pytest_secret_detection_warns() -> None:
    content = (
        "import pytest\n"
        "def test_no_orphan_members():\n"
        "    password = 'hunter2'\n"
        "    assert True\n"
    )
    bundle = _bundle(
        files=[PytestFile(path="tests/test_claims_etl_v1.py", content=content, kind="test")]
    )
    result = validate_pytest(bundle, _suite([_case()]), "claims_etl_v1")
    assert result.ok
    assert any("password" in w for w in result.warnings)
