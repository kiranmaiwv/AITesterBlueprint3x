"""Pipeline orchestration tests using the fixture gateway (no network, no LLM)."""

from __future__ import annotations

import os
from datetime import datetime

from hc_etl_qa_crew.config import Settings
from hc_etl_qa_crew.exceptions import DataError
from hc_etl_qa_crew.models import (
    PipelineStatus,
    StageName,
)
from hc_etl_qa_crew.schema_registry.star_schema import FACT_TABLE
from hc_etl_qa_crew.services.pipeline import QAPipeline, new_run_id


def _settings(tmp_path) -> Settings:
    # Fixture mode: no live warehouse, no LLM key needed to reach the
    # 'LLM not configured' gate deterministically.
    old = dict(os.environ)
    os.environ["HC_ETL_QA_CREW_SKIP_DOTENV"] = "1"
    os.environ["DEMO_MODE"] = "false"
    os.environ["DATA_SOURCE_MODE"] = "fixture"
    os.environ.pop("LLM_API_KEY", None)
    os.environ.pop("DEEPSEEK_API_KEY", None)
    os.environ["OUTPUT_DIR"] = str(tmp_path / "outputs")
    settings = Settings.load()
    # Restore env so other tests are not affected.
    os.environ.clear()
    os.environ.update(old)
    return settings


def test_run_id_shape() -> None:
    run_id = new_run_id(datetime(2026, 1, 15, 3, 0, 0))
    assert run_id.startswith("RUN-20260115-")
    assert len(run_id) == len("RUN-20260115-030000")


def test_pipeline_fetch_fails_when_gateway_fails(tmp_path) -> None:
    settings = _settings(tmp_path)

    class BrokenGateway:
        def fetch_snapshot(self, table):  # noqa: ARG002
            raise DataError("warehouse is on fire")

    pipeline = QAPipeline(settings, gateway=BrokenGateway())
    run = pipeline.run(["claims_etl_v1"])
    assert run.results[0].status is PipelineStatus.FAILED
    assert "warehouse is on fire" in run.results[0].error
    # Artifacts are still written for a failed fetch (manifest only).
    assert run.results[0].artifacts


def test_pipeline_stops_cleanly_when_llm_missing(tmp_path) -> None:
    """With no LLM key, the pipeline must stop after fetch with a clear error."""
    settings = _settings(tmp_path)
    assert settings.llm_api_key == ""
    pipeline = QAPipeline(settings)
    run = pipeline.run(["claims_etl_v1"])
    result = run.results[0]
    assert result.status is PipelineStatus.FAILED
    assert "LLM is not configured" in result.error
    assert result.snapshots  # the star schema was read before the gate
    assert len(result.snapshots) == 6  # 1 fact + 5 dims
    assert result.snapshots[0].table_name == FACT_TABLE.name


def test_pipeline_writes_run_level_artifacts(tmp_path) -> None:
    settings = _settings(tmp_path)
    pipeline = QAPipeline(settings)
    run = pipeline.run(["claims_etl_v1"], run_id="RUN-TEST-000001")
    assert run.run_id == "RUN-TEST-000001"
    summary = tmp_path / "outputs" / "RUN-TEST-000001" / "run_summary.md"
    manifest = tmp_path / "outputs" / "RUN-TEST-000001" / "manifest.json"
    assert summary.exists()
    assert manifest.exists()


def test_pipeline_snapshot_stage_is_reported(tmp_path) -> None:
    settings = _settings(tmp_path)
    seen: dict[str, str] = {}

    def on_progress(pipeline_name: str, event) -> None:  # noqa: ARG001
        seen[event.stage.value] = event.status.value

    pipeline = QAPipeline(settings, progress=on_progress)
    pipeline.run(["claims_etl_v1"])
    assert seen.get(StageName.FETCH.value) == "COMPLETED"
    assert seen.get(StageName.ARTIFACTS.value) in (None, "COMPLETED")
