"""Tests for model contracts: ids, trace requirements and readiness rules."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hc_etl_qa_crew.models import (
    PytestBundle,
    PytestFile,
    SchemaAnalysis,
    SchemaEntity,
    StarSchemaSnapshot,
    TableSnapshot,
    TestCase,
    TestCaseSuite,
    TestStep,
    TestType,
    TransformRule,
)


def _analysis() -> SchemaAnalysis:
    return SchemaAnalysis(
        pipeline_name="claims_etl_v1",
        summary="Demo claims load",
        fact_table="fact_claim_line",
        dimension_tables=["dim_member"],
        entities=[
            SchemaEntity(
                id="REQ-001",
                entity_type="requirement",
                text="Fact rows must reference an existing member",
                table_name="fact_claim_line",
            ),
            SchemaEntity(
                id="DQ-001",
                entity_type="data_quality",
                text="member_sk must never be null",
                table_name="fact_claim_line",
            ),
        ],
    )


def _case(**overrides) -> TestCase:
    base = {
        "id": "CLAIMS_ETL_V1-TC-001",
        "pipeline_name": "claims_etl_v1",
        "title": "Orphan member rows are rejected",
        "objective": "Ensures referential integrity",
        "table_name": "fact_claim_line",
        "column_name": "member_sk",
        "requirement_ids": ["REQ-001"],
        "data_quality_ids": ["DQ-001"],
        "steps": [TestStep(number=1, action="Run the FK check query", expected="0 rows")],
        "expected_result": "No orphan rows",
        "sql_template": "SELECT * FROM fact_claim_line f LEFT JOIN dim_member m ON f.member_sk=m.member_sk WHERE m.member_sk IS NULL",
    }
    base.update(overrides)
    return TestCase(**base)


# --------------------------------------------------------------------------
# Schema analysis entities
# --------------------------------------------------------------------------
def test_requirement_id_pattern() -> None:
    SchemaEntity(id="REQ-001", entity_type="requirement", text="x")
    with pytest.raises(ValidationError):
        SchemaEntity(id="REQ-01", entity_type="requirement", text="x")
    with pytest.raises(ValidationError):
        SchemaEntity(id="TC-001", entity_type="requirement", text="x")


def test_dq_id_pattern() -> None:
    SchemaEntity(id="DQ-001", entity_type="data_quality", text="x")
    with pytest.raises(ValidationError):
        SchemaEntity(id="REQ-001", entity_type="data_quality", text="x")  # REQ must be a requirement
    with pytest.raises(ValidationError):
        SchemaEntity(id="DQ-001", entity_type="requirement", text="x")  # DQ must be a rule


def test_entity_type_accepts_llm_synonyms() -> None:
    # Models answer with these variants; validation must coerce, not reject.
    assert SchemaEntity(id="REQ-001", entity_type="schema_requirement", text="x").entity_type.value == "requirement"
    assert SchemaEntity(id="REQ-001", entity_type="REQ", text="x").entity_type.value == "requirement"
    assert SchemaEntity(id="DQ-001", entity_type="data_quality", text="x").entity_type.value == "data_quality"
    assert SchemaEntity(id="DQ-001", entity_type="DQ", text="x").entity_type.value == "data_quality"
    assert SchemaEntity(id="DQ-001", entity_type="dq_rule", text="x").entity_type.value == "data_quality"


def test_analysis_coerces_load_frequency_and_summary() -> None:
    analysis = SchemaAnalysis(
        pipeline_name="claims_etl_v1",
        summary={"text": "nope"},  # wrong shape; must stringify, not crash
        load_frequency=["daily"],  # wrong shape
        dimension_tables=["dim_member"],
    )
    assert analysis.summary == "{'text': 'nope'}"
    assert analysis.load_frequency == "['daily']"


def test_test_case_coerces_scalar_and_list_fields() -> None:
    case = _case(
        table_name={"name": "fact_claim_line"},
        column_name=["member_sk"],
        requirement_ids="REQ-001",  # bare string must become a list
        tags=[None, "fk", {"x": 1}],
        test_type="data integrity",
        quality_dimension="referential integrity",
        automation_candidate="yes",
    )
    assert case.table_name == "{'name': 'fact_claim_line'}"  # stringified
    assert case.column_name == "['member_sk']"  # stringified
    assert case.requirement_ids == ["REQ-001"]
    assert "fk" in case.tags
    assert case.test_type.value == "data_integrity"
    assert case.quality_dimension.value == "referential_integrity"
    assert case.automation_candidate.value == "Yes"


def test_test_type_accepts_data_pipeline_vocabulary() -> None:
    # The ETL QA agents describe test_type with warehouse vocabulary, not
    # browser jargon. All of these must coerce to a valid member.
    assert TestType("data_quality").value == "data_quality"
    assert TestType("dq").value == "data_quality"
    assert TestType("row_count").value == "row_count"
    assert TestType("row count").value == "row_count"
    assert TestType("reconciliation").value == "reconciliation"
    assert TestType("uniqueness").value == "uniqueness"
    assert TestType("null check").value == "completeness"
    assert TestType("schema").value == "schema"
    assert TestType("data integrity").value == "data_integrity"


def test_analysis_id_properties() -> None:
    analysis = _analysis()
    assert analysis.requirement_ids == ["REQ-001"]
    assert analysis.data_quality_ids == ["DQ-001"]


# --------------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------------
def test_test_case_must_have_steps() -> None:
    with pytest.raises(ValidationError):
        _case(steps=[])


def test_test_case_must_trace_to_something() -> None:
    with pytest.raises(ValidationError):
        _case(requirement_ids=[], data_quality_ids=[])


def test_test_case_id_pattern() -> None:
    _case(id="CLAIMS_ETL_V1-TC-099")
    with pytest.raises(ValidationError):
        _case(id="CLAIMS_ETL_V1-TC-1")
    with pytest.raises(ValidationError):
        _case(id="TC-001")


def test_suite_requires_unique_ids() -> None:
    with pytest.raises(ValidationError, match="Duplicate test case ids"):
        TestCaseSuite(
            pipeline_name="claims_etl_v1",
            test_cases=[_case(), _case(id="CLAIMS_ETL_V1-TC-001")],
        )


def test_suite_requires_at_least_one_case() -> None:
    with pytest.raises(ValidationError, match="at least one test case"):
        TestCaseSuite(pipeline_name="claims_etl_v1", test_cases=[])


# --------------------------------------------------------------------------
# Pytest bundle
# --------------------------------------------------------------------------
def test_pytest_bundle_ready_cannot_have_missing_info() -> None:
    with pytest.raises(ValidationError):
        PytestBundle(
            pipeline_name="claims_etl_v1",
            files=[PytestFile(path="tests/test_claims_etl_v1.py", content="def test_x():\n    pass")],
            traces=[],
            readiness="READY",
            missing_information=["need a DSN"],
        )


def test_pytest_bundle_requires_files_unless_na() -> None:
    from hc_etl_qa_crew.models import AutomationReadiness

    with pytest.raises(ValidationError):
        PytestBundle(
            pipeline_name="claims_etl_v1",
            files=[],
            readiness=AutomationReadiness.NEEDS_CONFIGURATION,
        )
    # NOT_APPLICABLE with no files and no traces is valid.
    PytestBundle(
        pipeline_name="claims_etl_v1",
        files=[],
        readiness=AutomationReadiness.NOT_APPLICABLE,
    )


def test_pytest_file_rejects_traversal_and_non_py() -> None:
    with pytest.raises(ValidationError):
        PytestFile(path="../evil.py", content="")
    with pytest.raises(ValidationError):
        PytestFile(path="test.js", content="")
    PytestFile(path="tests/test_claims_etl_v1.py", content="")


# --------------------------------------------------------------------------
# Transform rule ids
# --------------------------------------------------------------------------
def test_transform_rule_requires_tr_prefix() -> None:
    TransformRule(id="TR-001", source_table="s", target_table="t", logic="copy")
    with pytest.raises(ValidationError):
        TransformRule(id="REQ-001", source_table="s", target_table="t", logic="copy")


# --------------------------------------------------------------------------
# Snapshots
# --------------------------------------------------------------------------
def test_table_snapshot_prompt_text_marks_source() -> None:
    snapshot = TableSnapshot(
        table_name="dim_member",
        source="DEMO_FIXTURE",
        column_names=["member_sk"],
        row_count=1,
        sample_rows=[{"member_sk": 1}],
    )
    text = snapshot.to_prompt_text()
    assert "DEMO_FIXTURE" in text
    assert "dim_member" in text
    assert "1" in text


def test_star_schema_snapshot_lookup() -> None:
    snapshot = TableSnapshot(table_name="dim_member", source="DEMO_FIXTURE")
    star = StarSchemaSnapshot(
        pipeline_name="claims_etl_v1",
        fact_table="fact_claim_line",
        dimension_tables=["dim_member"],
        tables=[snapshot],
    )
    assert star.snapshot("dim_member") is snapshot
    assert star.snapshot("nope") is None
    assert "claims_etl_v1" in star.to_prompt_text()
