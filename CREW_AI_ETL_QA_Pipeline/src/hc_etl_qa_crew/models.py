"""Pydantic models: the contract between every pipeline stage.

These are the internal source of truth. Renderers in
:mod:`hc_etl_qa_crew.services.artifacts` turn validated objects into Markdown,
CSV, JSON and pytest files. Raw LLM Markdown is never used as the source of
truth for anything.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------


class DataSource(StrEnum):
    """Where a snapshot came from. Never guessed; recorded by the gateway."""

    FIXTURE = "fixture"
    LIVE_WAREHOUSE = "live"
    DEMO_FIXTURE = "DEMO_FIXTURE"


class TableKind(StrEnum):
    FACT = "fact"
    DIMENSION = "dimension"


class Provenance(StrEnum):
    """Where a piece of information came from.

    The anti-hallucination rules hang off this: anything not EXPLICIT must be
    visibly labelled in the artifacts.
    """

    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"
    MISSING = "MISSING"
    ASSUMPTION_REQUIRING_CONFIRMATION = "ASSUMPTION_REQUIRING_CONFIRMATION"


class Severity(StrEnum):
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    WARNING = "warning"

    @classmethod
    def _missing_(cls, value: object) -> Severity | None:
        text = str(value).strip().lower()
        for member in cls:
            if member.value in text or text in member.value:
                return member
        return None


class ReconciliationType(StrEnum):
    ROW_COUNT = "row_count"
    SUM = "sum"
    RECORD = "record"
    SCHEMA = "schema"


class Granularity(StrEnum):
    FULL_REFRESH = "full_refresh"
    INCREMENTAL = "incremental"
    CDC = "cdc"
    SCD = "scd"
    SOURCE_TO_TARGET = "source_to_target"


class QualityDimension(StrEnum):
    COMPLETENESS = "completeness"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"
    TIMELINESS = "timeliness"
    CONSISTENCY = "consistency"
    ACCURACY = "accuracy"
    REFERENTIAL_INTEGRITY = "referential_integrity"
    RECONCILIATION = "reconciliation"

    @classmethod
    def _missing_(cls, value: object) -> QualityDimension | None:
        text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        for member in cls:
            if member.value in text or text in member.value:
                return member
        return None


class TestType(StrEnum):
    # Browser/UI-style categories (legacy, tolerated for compatibility).
    HAPPY_PATH = "happy_path"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    VALIDATION = "validation"
    ERROR_HANDLING = "error_handling"
    STATE_TRANSITION = "state_transition"
    PERMISSIONS = "permissions"
    API_CONTRACT = "api_contract"
    ACCESSIBILITY = "accessibility"
    CROSS_BROWSER = "cross_browser"
    REGRESSION = "regression"
    RECOVERY = "recovery"
    # Data-pipeline categories. A QA crew for a star-schema ETL answers with
    # these, not browser jargon, so they must be first-class values.
    DATA_INTEGRITY = "data_integrity"
    ROW_COUNT = "row_count"
    RECONCILIATION = "reconciliation"
    UNIQUENESS = "uniqueness"
    COMPLETENESS = "completeness"
    SCHEMA = "schema"
    DATA_QUALITY = "data_quality"
    TIMELINESS = "timeliness"
    CONSISTENCY = "consistency"
    ACCURACY = "accuracy"

    @classmethod
    def _missing_(cls, value: object) -> TestType | None:
        text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        for member in cls:
            if member.value in text or text in member.value:
                return member
        if "error" in text or "exception" in text:
            return cls.ERROR_HANDLING
        if "happy" in text or "positive" in text or "success" in text:
            return cls.HAPPY_PATH
        if "integrity" in text or "referential" in text:
            return cls.DATA_INTEGRITY
        if "row" in text and "count" in text:
            return cls.ROW_COUNT
        if "recon" in text:
            return cls.RECONCILIATION
        if "unique" in text:
            return cls.UNIQUENESS
        if "complete" in text or "null" in text:
            return cls.COMPLETENESS
        if "schema" in text or "column" in text or "ddl" in text:
            return cls.SCHEMA
        if "data_quality" in text or "dq" in text or "quality" in text:
            return cls.DATA_QUALITY
        return None


class AutomationCandidate(StrEnum):
    YES = "Yes"
    NO = "No"
    PARTIAL = "Partial"

    @classmethod
    def _missing_(cls, value: object) -> AutomationCandidate | None:
        text = str(value).strip().lower()
        if text.startswith(("y", "true", "auto")):
            return cls.YES
        if text.startswith(("n", "false", "manual")):
            return cls.NO
        if text.startswith(("p", "partial")):
            return cls.PARTIAL
        return None


class AutomationReadiness(StrEnum):
    READY = "READY"
    NEEDS_CONFIGURATION = "NEEDS_CONFIGURATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class PipelineStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"


class StageName(StrEnum):
    FETCH = "Data Fetch"
    ANALYSIS = "Schema & Transform Analyst"
    RECONCILIATION = "Reconciliation Strategist"
    TEST_CASES = "Test Case Writer"
    PYTEST = "pytest Coder"
    ARTIFACTS = "Artifacts"


class StageStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    WARNING = "WARNING"
    FAILED = "FAILED"


class CoverageStatus(StrEnum):
    COVERED = "COVERED"
    PARTIAL = "PARTIAL"
    UNCOVERED = "UNCOVERED"


#: Stable id shapes. The pipeline name is claims_etl_v1, so ids read
#: ``claims_etl_v1-REQ-001``, ``...-DQ-001`` (data-quality rule),
#: ``...-TC-001`` (test case) and ``...-PY-001`` (pytest function).
REQ_ID_RE = re.compile(r"^REQ-\d{3,}$")
DQ_ID_RE = re.compile(r"^DQ-\d{3,}$")
TC_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]+-TC-\d{3,}$")
PY_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]+-PY-\d{3,}$")

#: Everything generated by a fixture demo run is labelled with this.
DEMO_SOURCE = DataSource.DEMO_FIXTURE


# --------------------------------------------------------------------------
# Snapshot produced by the gateway (never by an LLM)
# --------------------------------------------------------------------------


class QualityProbe(BaseModel):
    """One measured fact about a table, produced deterministically."""

    name: str
    sql: str = ""
    observed_value: str = ""


class TableSnapshot(BaseModel):
    """A validated snapshot of one table. Built by the gateway, not an agent."""

    table_name: str
    source: DataSource = DataSource.FIXTURE
    column_names: list[str] = Field(default_factory=list)
    row_count: int = 0
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)
    probes: list[QualityProbe] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=datetime.now)

    def to_prompt_text(self) -> str:
        """Flatten to the text handed to the Schema Analyst agent.

        Wrapped in an explicit untrusted-data marker: warehouse content is
        business data, never instructions.
        """
        lines = [
            f"Table: {self.table_name}",
            f"Source: {self.source.value}",
            f"Row count: {self.row_count}",
            f"Columns ({len(self.column_names)}): {', '.join(self.column_names)}",
            "",
            "Sample rows (first up to 8):",
        ]
        if self.sample_rows:
            header = " | ".join(str(k) for k in self.sample_rows[0])
            lines.append(f"| {header} |")
            for row in self.sample_rows[:8]:
                values = " | ".join(_display(v) for v in row.values())
                lines.append(f"| {values} |")
        else:
            lines.append("(no sample rows available)")
        return "\n".join(lines)


def _display(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    return str(value)


# --------------------------------------------------------------------------
# Run / pipeline input (deterministic)
# --------------------------------------------------------------------------


class StarSchemaSnapshot(BaseModel):
    """The full set of snapshots for one pipeline run."""

    pipeline_name: str = "claims_etl_v1"
    fact_table: str = "fact_claim_line"
    dimension_tables: list[str] = Field(default_factory=list)
    tables: list[TableSnapshot] = Field(default_factory=list)
    source: DataSource = DataSource.FIXTURE
    fetched_at: datetime = Field(default_factory=datetime.now)

    def snapshot(self, table_name: str) -> TableSnapshot | None:
        for table in self.tables:
            if table.table_name == table_name:
                return table
        return None

    def to_prompt_text(self) -> str:
        lines = [
            "## DATA SNAPSHOT (deterministic, read-only)",
            f"Pipeline: {self.pipeline_name}",
            f"Fact table: {self.fact_table}",
            f"Dimension tables: {', '.join(self.dimension_tables)}",
            "",
        ]
        for table in self.tables:
            lines.append(table.to_prompt_text())
            lines.append("")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Stage 1 - Schema & transform analysis
# --------------------------------------------------------------------------


class EntityType(StrEnum):
    """The kind of a SchemaEntity, normalized to two canonical values.

    LLMs answer with synonyms (``schema_requirement``, ``dq_rule``, even the
    bare prefix ``REQ``), so validation coerces rather than rejects.
    """

    REQUIREMENT = "requirement"
    DATA_QUALITY = "data_quality"

    @classmethod
    def _missing_(cls, value: object) -> EntityType | None:
        text = str(value).strip().lower().replace("_", "-").replace(" ", "-")
        if text.startswith(("req", "requirement", "schema-requirement")):
            return cls.REQUIREMENT
        if text.startswith(("dq", "data-quality", "quality", "data_quality")):
            return cls.DATA_QUALITY
        return None


class SchemaEntity(BaseModel):
    id: str = Field(description="Stable identifier, e.g. REQ-001 or DQ-001")
    entity_type: EntityType = EntityType.REQUIREMENT
    text: str
    provenance: Provenance = Provenance.EXPLICIT
    source_quote: str = ""
    table_name: str = ""
    severity: Severity = Severity.MAJOR

    @field_validator("id")
    @classmethod
    def _check_id(cls, value: str) -> str:
        value = value.strip().upper()
        if not (REQ_ID_RE.match(value) or DQ_ID_RE.match(value)):
            raise ValueError(
                f"Analysis id must look like REQ-001 or DQ-001, got {value!r}"
            )
        return value

    @model_validator(mode="after")
    def _type_matches_id_prefix(self) -> SchemaEntity:
        """A REQ-* id must be a requirement; a DQ-* id must be a quality rule."""
        if self.id.startswith("REQ-") and self.entity_type is not EntityType.REQUIREMENT:
            raise ValueError(
                f"{self.id} has entity_type={self.entity_type.value!r}, expected 'requirement'"
            )
        if self.id.startswith("DQ-") and self.entity_type is not EntityType.DATA_QUALITY:
            raise ValueError(
                f"{self.id} has entity_type={self.entity_type.value!r}, expected 'data_quality'"
            )
        return self


class FieldProfile(BaseModel):
    column_name: str
    table_name: str = ""
    data_type: str = ""
    nulls_observed: int = 0
    distinct_observed: int = 0
    min_value: str = ""
    max_value: str = ""


class TransformRule(BaseModel):
    id: str = Field(description="Stable identifier, e.g. TR-001")
    source_table: str
    target_table: str
    rule_type: str = "mapping"
    logic: str
    risk: Severity = Severity.MAJOR

    @field_validator("id")
    @classmethod
    def _check_tr_id(cls, value: str) -> str:
        value = value.strip().upper()
        if not value.startswith("TR-") or not value[3:].isdigit():
            raise ValueError(f"Transform rule id must look like TR-001, got {value!r}")
        return value


class SchemaAnalysis(BaseModel):
    """Validated output of Agent 1."""

    pipeline_name: str
    summary: str = ""
    fact_table: str = ""
    dimension_tables: list[str] = Field(default_factory=list)
    source_system: str = ""
    load_frequency: str = ""
    entities: list[SchemaEntity] = Field(default_factory=list)
    transform_rules: list[TransformRule] = Field(default_factory=list)
    field_profiles: list[FieldProfile] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    source: DataSource = DataSource.FIXTURE

    @field_validator("load_frequency", "source_system", "summary", mode="before")
    @classmethod
    def _stringify(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @property
    def requirement_ids(self) -> list[str]:
        return [e.id for e in self.entities if e.entity_type == "requirement"]

    @property
    def data_quality_ids(self) -> list[str]:
        return [e.id for e in self.entities if e.entity_type == "data_quality"]


# --------------------------------------------------------------------------
# Shared coercions for LLM output.
#
# Agents routinely answer string fields with objects or lists and list fields
# with a bare string. Instead of failing a whole stage over a shape quirk,
# every contract below stringifies scalars and normalizes list-ish input.
# --------------------------------------------------------------------------


def _as_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_text_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for item in value:
            text = _as_text(item)
            if text:
                out.append(text)
        return out
    text = _as_text(value)
    return [text] if text else []


class ReconciliationStrategy(BaseModel):
    id: str = Field(description="e.g. REC-001")
    name: str
    description: str = ""
    recon_type: ReconciliationType = ReconciliationType.ROW_COUNT
    source_table: str = ""
    target_table: str = ""
    match_key: list[str] = Field(default_factory=list)
    measure_columns: list[str] = Field(default_factory=list)
    tolerance_pct: float = 0.0
    schedule: str = ""

    @field_validator(
        "name", "description", "source_table", "target_table", "schedule",
        mode="before",
    )
    @classmethod
    def _text(cls, value: object) -> str:
        return _as_text(value)

    @field_validator("match_key", "measure_columns", mode="before")
    @classmethod
    def _texts(cls, value: object) -> list[str]:
        return _as_text_list(value)


class QualityRule(BaseModel):
    id: str = Field(description="e.g. DQ-001")
    name: str
    description: str = ""
    dimension: QualityDimension = QualityDimension.COMPLETENESS
    table_name: str = ""
    column_name: str = ""
    threshold: str = ""
    severity: Severity = Severity.MAJOR

    @field_validator(
        "name", "description", "table_name", "column_name", "threshold",
        mode="before",
    )
    @classmethod
    def _text(cls, value: object) -> str:
        return _as_text(value)


class ReconcilePlan(BaseModel):
    """Validated output of Agent 2."""

    pipeline_name: str
    summary: str = ""
    strategies: list[ReconciliationStrategy] = Field(default_factory=list)
    quality_rules: list[QualityRule] = Field(default_factory=list)
    environment_strategy: list[str] = Field(default_factory=list)
    execution_order: list[str] = Field(default_factory=list)
    entry_exit_criteria: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)

    @field_validator("pipeline_name", "summary", mode="before")
    @classmethod
    def _text(cls, value: object) -> str:
        return _as_text(value)

    @field_validator(
        "environment_strategy", "execution_order", "entry_exit_criteria",
        "risks", "dependencies", "assumptions", "missing_information",
        mode="before",
    )
    @classmethod
    def _texts(cls, value: object) -> list[str]:
        return _as_text_list(value)


# --------------------------------------------------------------------------
# Stage 3 - Data-quality test cases
# --------------------------------------------------------------------------


class TestStep(BaseModel):
    number: int = Field(ge=1)
    action: str
    expected: str = ""

    @field_validator("action", "expected", mode="before")
    @classmethod
    def _stringify(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()


class TestCase(BaseModel):
    id: str = Field(description="e.g. claims_etl_v1-TC-001")
    pipeline_name: str
    title: str
    objective: str = ""
    priority: str = "P1"
    test_type: TestType = TestType.HAPPY_PATH
    quality_dimension: QualityDimension = QualityDimension.COMPLETENESS
    table_name: str = ""
    column_name: str = ""
    requirement_ids: list[str] = Field(default_factory=list)
    data_quality_ids: list[str] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    test_data: list[str] = Field(default_factory=list)
    steps: list[TestStep] = Field(default_factory=list)
    expected_result: str = ""
    sql_template: str = ""
    automation_candidate: AutomationCandidate = AutomationCandidate.YES
    automation_rationale: str = ""
    tags: list[str] = Field(default_factory=list)
    assumptions_or_blockers: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _check_id(cls, value: str) -> str:
        value = value.strip().upper()
        if not TC_ID_RE.match(value):
            raise ValueError(
                f"Test case id must look like claims_etl_v1-TC-001, got {value!r}"
            )
        return value

    @field_validator(
        "title", "objective", "priority", "table_name", "column_name",
        "expected_result", "sql_template", "automation_rationale",
        mode="before",
    )
    @classmethod
    def _stringify_text(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator(
        "requirement_ids", "data_quality_ids", "preconditions", "test_data",
        "tags", "assumptions_or_blockers",
        mode="before",
    )
    @classmethod
    def _stringify_lists(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, (list, tuple)):
            out: list[str] = []
            for item in value:
                if item is None:
                    continue
                text = str(item).strip()
                if text:
                    out.append(text)
            return out
        return [str(value)]

    @model_validator(mode="after")
    def _needs_steps_and_trace(self) -> TestCase:
        if not self.steps:
            raise ValueError(f"Test case {self.id} has no steps")
        if (
            not self.requirement_ids
            and not self.data_quality_ids
            and self.quality_dimension is not QualityDimension.RECONCILIATION
        ):
            raise ValueError(
                f"Test case {self.id} must trace to at least one REQ-* or DQ-* id"
            )
        return self


class TestCaseSuite(BaseModel):
    """Validated output of Agent 3."""

    pipeline_name: str
    test_cases: list[TestCase]
    coverage_notes: str = ""

    @model_validator(mode="after")
    def _unique_ids(self) -> TestCaseSuite:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for case in self.test_cases:
            if case.id in seen:
                duplicates.add(case.id)
            seen.add(case.id)
        if duplicates:
            raise ValueError(f"Duplicate test case ids: {sorted(duplicates)}")
        if not self.test_cases:
            raise ValueError("A test case suite must contain at least one test case")
        return self


# --------------------------------------------------------------------------
# Stage 4 - pytest bundle
# --------------------------------------------------------------------------


class PytestFile(BaseModel):
    path: str = Field(description="Relative path, e.g. tests/test_claims_etl_v1.py")
    content: str
    kind: str = Field(default="test", description="test | conftest | helper")

    @field_validator("path", "content", "kind", mode="before")
    @classmethod
    def _text(cls, value: object) -> str:
        return _as_text(value)

    @field_validator("path")
    @classmethod
    def _safe_relative_path(cls, value: str) -> str:
        value = value.strip().replace("\\", "/").lstrip("/")
        if not value:
            raise ValueError("Pytest file path must not be empty")
        if ".." in value.split("/"):
            raise ValueError(f"Pytest file path must not traverse upwards: {value!r}")
        if not value.endswith(".py"):
            raise ValueError(f"Pytest file must be .py, got {value!r}")
        return value


class AutomatedTestTrace(BaseModel):
    test_name: str
    test_case_id: str
    pipeline_name: str
    requirement_ids: list[str] = Field(default_factory=list)
    data_quality_ids: list[str] = Field(default_factory=list)
    file_path: str = ""

    @field_validator("test_name", "test_case_id", "pipeline_name", "file_path", mode="before")
    @classmethod
    def _text(cls, value: object) -> str:
        return _as_text(value)

    @field_validator("requirement_ids", "data_quality_ids", mode="before")
    @classmethod
    def _texts(cls, value: object) -> list[str]:
        return _as_text_list(value)


class PytestBundle(BaseModel):
    """Validated output of Agent 4."""

    pipeline_name: str
    files: list[PytestFile] = Field(default_factory=list)
    traces: list[AutomatedTestTrace] = Field(default_factory=list)
    readiness: AutomationReadiness = AutomationReadiness.NEEDS_CONFIGURATION
    setup_notes: str = ""
    missing_information: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)

    @field_validator("pipeline_name", "setup_notes", mode="before")
    @classmethod
    def _text(cls, value: object) -> str:
        return _as_text(value)

    @field_validator("missing_information", "assumptions", mode="before")
    @classmethod
    def _texts(cls, value: object) -> list[str]:
        return _as_text_list(value)

    @model_validator(mode="after")
    def _ready_needs_evidence(self) -> PytestBundle:
        if self.readiness is AutomationReadiness.READY and self.missing_information:
            raise ValueError(
                "readiness=READY is not allowed while missing_information is non-empty"
            )
        if self.readiness is not AutomationReadiness.NOT_APPLICABLE and not self.files:
            raise ValueError("A pytest bundle must contain at least one file")
        if self.readiness is AutomationReadiness.NOT_APPLICABLE and self.traces:
            raise ValueError(
                "readiness=NOT_APPLICABLE means nothing was automated, so there "
                "can be no traces"
            )
        return self


# --------------------------------------------------------------------------
# Traceability and run bookkeeping (computed in Python, never by the LLM)
# --------------------------------------------------------------------------


class TraceabilityRow(BaseModel):
    requirement_id: str
    requirement_text: str = ""
    data_quality_id: str = ""
    data_quality_text: str = ""
    test_case_ids: list[str] = Field(default_factory=list)
    automated_test_case_ids: list[str] = Field(default_factory=list)
    coverage_status: CoverageStatus = CoverageStatus.UNCOVERED
    reason: str = ""


class CoverageReport(BaseModel):
    pipeline_name: str
    rows: list[TraceabilityRow] = Field(default_factory=list)
    total_requirements: int = 0
    covered_requirements: int = 0
    partially_covered_requirements: int = 0
    uncovered_requirements: int = 0
    total_data_quality: int = 0
    covered_data_quality: int = 0
    total_test_cases: int = 0
    automated_test_cases: int = 0
    orphan_requirement_ids: list[str] = Field(default_factory=list)
    orphan_data_quality_ids: list[str] = Field(default_factory=list)
    orphan_test_case_ids: list[str] = Field(default_factory=list)
    unknown_reference_ids: list[str] = Field(default_factory=list)

    @property
    def requirement_coverage_pct(self) -> float:
        if not self.total_requirements:
            return 0.0
        return round(100.0 * self.covered_requirements / self.total_requirements, 1)

    @property
    def automation_pct(self) -> float:
        if not self.total_test_cases:
            return 0.0
        return round(100.0 * self.automated_test_cases / self.total_test_cases, 1)


class StageEvent(BaseModel):
    stage: StageName
    status: StageStatus = StageStatus.PENDING
    message: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.finished_at:
            return round((self.finished_at - self.started_at).total_seconds(), 2)
        return None


class PipelineResult(BaseModel):
    """Everything produced for one pipeline run, successful or not."""

    pipeline_name: str
    status: PipelineStatus = PipelineStatus.PENDING
    source: DataSource | None = None
    snapshots: list[TableSnapshot] = Field(default_factory=list)
    analysis: SchemaAnalysis | None = None
    recon_plan: ReconcilePlan | None = None
    test_cases: TestCaseSuite | None = None
    pytest: PytestBundle | None = None
    coverage: CoverageReport | None = None
    stages: list[StageEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: str = ""
    artifact_dir: str = ""
    artifacts: dict[str, str] = Field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.finished_at:
            return round((self.finished_at - self.started_at).total_seconds(), 2)
        return None

    def stage(self, name: StageName) -> StageEvent:
        for event in self.stages:
            if event.stage is name:
                return event
        event = StageEvent(stage=name)
        self.stages.append(event)
        return event

    def snapshot(self, table_name: str) -> TableSnapshot | None:
        for table in self.snapshots:
            if table.table_name == table_name:
                return table
        return None


class RunSummary(BaseModel):
    run_id: str
    requested_pipelines: list[str] = Field(default_factory=list)
    invalid_inputs: list[str] = Field(default_factory=list)
    duplicates_removed: list[str] = Field(default_factory=list)
    results: list[PipelineResult] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    output_dir: str = ""

    @property
    def completed(self) -> list[PipelineResult]:
        return [r for r in self.results if r.status is PipelineStatus.COMPLETED]

    @property
    def completed_with_warnings(self) -> list[PipelineResult]:
        return [r for r in self.results if r.status is PipelineStatus.COMPLETED_WITH_WARNINGS]

    @property
    def failed(self) -> list[PipelineResult]:
        return [r for r in self.results if r.status is PipelineStatus.FAILED]

    @property
    def successful(self) -> bool:
        """A run succeeds when at least one pipeline produced a full artifact set."""
        return bool(self.completed or self.completed_with_warnings)
