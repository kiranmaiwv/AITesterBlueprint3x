"""Tests for deterministic artifact renderers, manifests, ZIP and file writing."""

from __future__ import annotations

import json
import zipfile

from hc_etl_qa_crew.models import (
    AutomationReadiness,
    PipelineResult,
    PipelineStatus,
    PytestBundle,
    PytestFile,
    RunSummary,
    SchemaAnalysis,
    SchemaEntity,
    TestCase,
    TestCaseSuite,
    TestStep,
)
from hc_etl_qa_crew.services import artifacts as artifacts_service
from hc_etl_qa_crew.services.artifacts import (
    build_run_manifest,
    build_ticket_manifest,
    build_zip,
    render_recon_plan_md,
    render_run_summary_md,
    render_schema_analysis_md,
    render_test_cases_csv,
    render_test_cases_md,
    render_traceability_csv,
    write_run_artifacts,
    write_ticket_artifacts,
)
from hc_etl_qa_crew.services.traceability import build_coverage


def _analysis() -> SchemaAnalysis:
    return SchemaAnalysis(
        pipeline_name="claims_etl_v1",
        summary="demo claims load",
        fact_table="fact_claim_line",
        dimension_tables=["dim_member", "dim_provider"],
        entities=[
            SchemaEntity(
                id="REQ-001",
                entity_type="requirement",
                text="fact rows join to member",
                table_name="fact_claim_line",
            ),
            SchemaEntity(
                id="DQ-001",
                entity_type="data_quality",
                text="member_sk not null",
                table_name="fact_claim_line",
            ),
        ],
    )


def _case() -> TestCase:
    return TestCase(
        id="CLAIMS_ETL_V1-TC-001",
        pipeline_name="claims_etl_v1",
        title="No orphan members",
        objective="FK integrity",
        table_name="fact_claim_line",
        column_name="member_sk",
        requirement_ids=["REQ-001"],
        data_quality_ids=["DQ-001"],
        steps=[TestStep(number=1, action="run the check", expected="0 rows")],
        expected_result="no orphan rows",
        sql_template="SELECT * FROM fact_claim_line f LEFT JOIN dim_member m ON f.member_sk=m.member_sk WHERE m.member_sk IS NULL",
    )


def _suite() -> TestCaseSuite:
    return TestCaseSuite(pipeline_name="claims_etl_v1", test_cases=[_case()])


def _bundle() -> PytestBundle:
    return PytestBundle(
        pipeline_name="claims_etl_v1",
        files=[
            PytestFile(
                path="tests/test_claims_etl_v1.py",
                content=(
                    "import pytest\n"
                    "def test_no_orphan_members():\n"
                    "    assert True\n"
                ),
            )
        ],
        traces=[
            {
                "test_name": "test_no_orphan_members",
                "test_case_id": "CLAIMS_ETL_V1-TC-001",
                "pipeline_name": "claims_etl_v1",
                "requirement_ids": ["REQ-001"],
                "data_quality_ids": ["DQ-001"],
            }
        ],
        readiness=AutomationReadiness.READY,
        setup_notes="export ETL_TEST_DATABASE_URL=...; pytest tests",
    )


def _result() -> PipelineResult:
    analysis = _analysis()
    suite = _suite()
    bundle = _bundle()
    result = PipelineResult(
        pipeline_name="claims_etl_v1",
        status=PipelineStatus.COMPLETED,
        analysis=analysis,
        test_cases=suite,
        pytest=bundle,
        coverage=build_coverage(analysis, suite, bundle),
        started_at=None,
    )
    return result


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------
def test_schema_analysis_md_contains_sections() -> None:
    md = render_schema_analysis_md(_analysis())
    assert "Schema & Transform Analysis" in md
    assert "REQ-001" in md
    assert "DQ-001" in md
    assert "fact_claim_line" in md


def test_recon_plan_md_renders() -> None:
    from hc_etl_qa_crew.models import ReconcilePlan, ReconciliationStrategy

    plan = ReconcilePlan(
        pipeline_name="claims_etl_v1",
        summary="reconcile the load",
        strategies=[
            ReconciliationStrategy(
                id="REC-001",
                name="row count",
                recon_type="row_count",
                source_table="stg_claims",
                target_table="fact_claim_line",
                tolerance_pct=0.0,
            )
        ],
    )
    md = render_recon_plan_md(plan)
    assert "REC-001" in md
    assert "row count" in md


def test_test_cases_md_contains_sql_template() -> None:
    md = render_test_cases_md(_suite())
    assert "CLAIMS_ETL_V1-TC-001" in md
    assert "sql" in md.lower()
    assert "LEFT JOIN dim_member" in md


def test_pytest_md_contains_generated_files() -> None:
    md = artifacts_service.render_pytest_md(_bundle())
    assert "pytest Automation" in md
    assert "test_claims_etl_v1.py" in md
    assert "test_no_orphan_members" in md


def test_run_summary_md_lists_statuses() -> None:
    run = RunSummary(
        run_id="RUN-1",
        requested_pipelines=["claims_etl_v1"],
        results=[_result()],
    )
    md = render_run_summary_md(run)
    assert "RUN-1" in md
    assert "claims_etl_v1" in md
    assert "COMPLETED" in md


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------
def test_test_cases_csv_header_and_row() -> None:
    csv_text = render_test_cases_csv(_suite())
    assert "test_case_id" in csv_text
    assert "CLAIMS_ETL_V1-TC-001" in csv_text
    assert "member_sk" in csv_text


def test_traceability_csv_has_rows() -> None:
    coverage = build_coverage(_analysis(), _suite(), _bundle())
    csv_text = render_traceability_csv(coverage)
    assert "requirement_id" in csv_text
    assert "REQ-001" in csv_text


# --------------------------------------------------------------------------
# Manifests
# --------------------------------------------------------------------------
def test_ticket_manifest_counts() -> None:
    result = _result()
    manifest = build_ticket_manifest(result)
    assert manifest["pipeline_name"] == "claims_etl_v1"
    assert manifest["status"] == "COMPLETED"
    assert manifest["counts"]["requirements"] == 2
    assert manifest["counts"]["test_cases"] == 1
    assert manifest["automation_readiness"] == "READY"


def test_run_manifest_nests_pipelines() -> None:
    run = RunSummary(
        run_id="RUN-1",
        requested_pipelines=["claims_etl_v1"],
        results=[_result()],
    )
    manifest = build_run_manifest(run)
    assert manifest["successful"] is True
    assert manifest["pipelines"][0]["pipeline_name"] == "claims_etl_v1"
    assert manifest["totals"]["completed"] == 1


# --------------------------------------------------------------------------
# Writing to disk
# --------------------------------------------------------------------------
def test_write_ticket_artifacts_creates_files(tmp_path) -> None:
    result = _result()
    written = write_ticket_artifacts(result, tmp_path)
    assert "schema_analysis.md" in written
    assert "test_cases.csv" in written
    assert "manifest.json" in written
    assert (tmp_path / "claims_etl_v1" / "schema_analysis.md").exists()
    assert (tmp_path / "claims_etl_v1" / "manifest.json").exists()
    assert result.artifact_dir


def test_write_run_artifacts_creates_summary(tmp_path) -> None:
    run = RunSummary(run_id="RUN-1", requested_pipelines=["claims_etl_v1"], results=[_result()])
    run_dir = write_run_artifacts(run, tmp_path)
    assert (run_dir / "run_summary.md").exists()
    assert (run_dir / "manifest.json").exists()


def test_write_ticket_artifacts_sanitizes_path_traversal(tmp_path) -> None:
    result = PipelineResult(
        pipeline_name="claims_etl_v1",
        status=PipelineStatus.FAILED,
        error="boom",
    )
    written = write_ticket_artifacts(result, tmp_path)
    assert "manifest.json" in written
    assert (tmp_path / "claims_etl_v1" / "manifest.json").exists()


# --------------------------------------------------------------------------
# ZIP
# --------------------------------------------------------------------------
def test_build_zip_round_trip(tmp_path) -> None:
    run = RunSummary(run_id="RUN-1", requested_pipelines=["claims_etl_v1"], results=[_result()])
    data = build_zip(run)
    archive_path = tmp_path / "out.zip"
    archive_path.write_bytes(data)
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        joined = "\n".join(names)
        assert "run_summary.md" in joined
        assert "schema_analysis.md" in joined
        assert "test_claims_etl_v1.py" in joined


def test_build_zip_filters_by_pipeline() -> None:
    run = RunSummary(run_id="RUN-1", requested_pipelines=["claims_etl_v1"], results=[_result()])
    data = build_zip(run, pipelines=["claims_etl_v1"])
    assert b"claims_etl_v1" in data


def test_snapshot_json_round_trip(tmp_path) -> None:
    from hc_etl_qa_crew.data_gateway.fixture_provider import FixtureDataProvider
    from hc_etl_qa_crew.schema_registry.star_schema import FACT_TABLE

    provider = FixtureDataProvider()
    snapshot = provider.fetch_snapshot(FACT_TABLE)
    payload = json.loads(snapshot.model_dump_json())
    assert payload["table_name"] == "fact_claim_line"
    assert payload["row_count"] == 100
