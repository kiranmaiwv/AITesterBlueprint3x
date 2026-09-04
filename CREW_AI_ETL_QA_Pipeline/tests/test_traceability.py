"""Tests for deterministic traceability and coverage math."""

from __future__ import annotations

from hc_etl_qa_crew.models import (
    AutomationCandidate,
    AutomationReadiness,
    CoverageStatus,
    PytestBundle,
    PytestFile,
    SchemaAnalysis,
    SchemaEntity,
    TestCase,
    TestCaseSuite,
    TestStep,
)
from hc_etl_qa_crew.services.traceability import build_coverage


def _analysis() -> SchemaAnalysis:
    return SchemaAnalysis(
        pipeline_name="claims_etl_v1",
        fact_table="fact_claim_line",
        dimension_tables=["dim_member", "dim_provider"],
        entities=[
            SchemaEntity(
                id="REQ-001",
                entity_type="requirement",
                text="fact joins to member",
                table_name="fact_claim_line",
                source_quote="member_sk",
            ),
            SchemaEntity(
                id="REQ-002",
                entity_type="requirement",
                text="fact joins to provider",
                table_name="fact_claim_line",
                source_quote="provider_sk",
            ),
            SchemaEntity(
                id="DQ-001",
                entity_type="data_quality",
                text="member_sk not null",
                table_name="fact_claim_line",
                source_quote="not null",
            ),
        ],
    )


def _case(case_id, req_ids, dq_ids, automation=AutomationCandidate.YES) -> TestCase:
    return TestCase(
        id=case_id,
        pipeline_name="claims_etl_v1",
        title="case",
        table_name="fact_claim_line",
        column_name="member_sk",
        requirement_ids=req_ids,
        data_quality_ids=dq_ids,
        steps=[TestStep(number=1, action="run", expected="0")],
        expected_result="clean",
        automation_candidate=automation,
        automation_rationale="sql",
    )


def _suite(*cases) -> TestCaseSuite:
    return TestCaseSuite(pipeline_name="claims_etl_v1", test_cases=list(cases))


def _bundle(case_id: str, readiness: AutomationReadiness = AutomationReadiness.READY) -> PytestBundle:
    return PytestBundle(
        pipeline_name="claims_etl_v1",
        files=[PytestFile(path="tests/test_claims.py", content="def test_x():\n    pass\n")],
        traces=[
            {
                "test_name": "test_x",
                "test_case_id": case_id,
                "pipeline_name": "claims_etl_v1",
                "requirement_ids": ["REQ-001"],
                "data_quality_ids": ["DQ-001"],
            }
        ],
        readiness=readiness,
        missing_information=[] if readiness is AutomationReadiness.READY else ["dsn"],
    )


def test_coverage_counts_when_everything_is_covered() -> None:
    analysis = _analysis()
    suite = _suite(
        _case("CLAIMS_ETL_V1-TC-001", ["REQ-001"], ["DQ-001"]),
        _case("CLAIMS_ETL_V1-TC-002", ["REQ-002"], []),
    )
    # Both cases are automated and the bundle is READY.
    traces = [
        {
            "test_name": "test_one",
            "test_case_id": "CLAIMS_ETL_V1-TC-001",
            "pipeline_name": "claims_etl_v1",
            "requirement_ids": ["REQ-001"],
            "data_quality_ids": ["DQ-001"],
        },
        {
            "test_name": "test_two",
            "test_case_id": "CLAIMS_ETL_V1-TC-002",
            "pipeline_name": "claims_etl_v1",
            "requirement_ids": ["REQ-002"],
            "data_quality_ids": [],
        },
    ]
    bundle = PytestBundle(
        pipeline_name="claims_etl_v1",
        files=[PytestFile(path="tests/test_claims.py", content="def test_x():\n    pass\n")],
        traces=traces,
        readiness=AutomationReadiness.READY,
    )
    coverage = build_coverage(analysis, suite, bundle)
    assert coverage.total_requirements == 2
    assert coverage.covered_requirements == 2
    assert coverage.requirement_coverage_pct == 100.0
    assert coverage.covered_data_quality == 1
    assert coverage.total_test_cases == 2
    assert coverage.automated_test_cases == 2


def test_coverage_reports_uncovered_requirement() -> None:
    analysis = _analysis()
    suite = _suite(
        # Manual-only case: covered but never automatable.
        _case(
            "CLAIMS_ETL_V1-TC-001",
            ["REQ-001"],
            ["DQ-001"],
            automation=AutomationCandidate.NO,
        ),
    )
    coverage = build_coverage(analysis, suite)
    assert coverage.orphan_requirement_ids == ["REQ-002"]
    assert coverage.covered_requirements == 1
    assert coverage.uncovered_requirements == 1
    assert coverage.requirement_coverage_pct == 50.0


def test_coverage_partial_when_automation_missing() -> None:
    analysis = _analysis()
    suite = _suite(
        _case("CLAIMS_ETL_V1-TC-001", ["REQ-001"], ["DQ-001"], automation=AutomationCandidate.YES),
    )
    # No bundle at all: nothing is automated.
    coverage = build_coverage(analysis, suite)
    assert coverage.partially_covered_requirements == 1
    assert coverage.automated_test_cases == 0
    statuses = {r.coverage_status for r in coverage.rows}
    assert CoverageStatus.PARTIAL in statuses


def test_manual_cases_count_as_covered() -> None:
    analysis = _analysis()
    suite = _suite(
        _case(
            "CLAIMS_ETL_V1-TC-001",
            ["REQ-001"],
            ["DQ-001"],
            automation=AutomationCandidate.NO,
        ),
    )
    coverage = build_coverage(analysis, suite)
    assert coverage.covered_requirements == 1


def test_automated_but_not_ready_counts_as_covered() -> None:
    """Automation exists; the suite merely needs config. That is COVERED, not
    PARTIAL — PARTIAL is reserved for genuinely missing automation."""
    analysis = _analysis()
    suite = _suite(
        _case("CLAIMS_ETL_V1-TC-001", ["REQ-001"], ["DQ-001"], automation=AutomationCandidate.YES),
    )
    bundle = _bundle("CLAIMS_ETL_V1-TC-001", readiness=AutomationReadiness.NEEDS_CONFIGURATION)
    coverage = build_coverage(analysis, suite, bundle)
    assert coverage.partially_covered_requirements == 0
    assert coverage.covered_requirements == 1
    reasons = {r.reason for r in coverage.rows if r.requirement_id == "REQ-001"}
    assert any("not yet execution-ready" in r for r in reasons)


def test_orphan_and_unknown_references_are_listed() -> None:
    analysis = _analysis()
    suite = _suite(
        _case("CLAIMS_ETL_V1-TC-001", ["REQ-001", "REQ-999"], ["DQ-001"]),
    )
    coverage = build_coverage(analysis, suite)
    assert "REQ-999" in coverage.unknown_reference_ids
    assert coverage.orphan_test_case_ids == []
    # A case tracing only to nothing real is orphaned:
    suite2 = _suite(_case("CLAIMS_ETL_V1-TC-002", ["NOPE"], []))
    coverage2 = build_coverage(analysis, suite2)
    assert coverage2.orphan_test_case_ids == ["CLAIMS_ETL_V1-TC-002"]


def test_unlinked_dq_gets_its_own_row() -> None:
    analysis = _analysis()
    # DQ-001 is not linked to any requirement via source_quote commas; it is a
    # top-level rule on the fact table, so it still gets a traceability row.
    suite = _suite(_case("CLAIMS_ETL_V1-TC-001", ["REQ-001"], ["DQ-001"]))
    coverage = build_coverage(analysis, suite)
    dq_rows = [r for r in coverage.rows if r.data_quality_id == "DQ-001"]
    assert dq_rows
    assert coverage.total_data_quality == 1
    assert coverage.covered_data_quality == 1


def test_row_reason_spells_out_missing_automation() -> None:
    analysis = _analysis()
    suite = _suite(_case("CLAIMS_ETL_V1-TC-001", ["REQ-001"], ["DQ-001"]))
    coverage = build_coverage(analysis, suite)
    reasons = {r.reason for r in coverage.rows if r.requirement_id == "REQ-001"}
    assert any("automation is missing" in r for r in reasons)
