"""End-to-end smoke test over the local fixtures.

Runs the real four-agent pipeline against the deterministic demo dataset with
DEMO_MODE forced on, so it exercises the LLM and every renderer without
touching a live warehouse.

    python scripts/demo_smoke.py [PIPELINE ...]
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hc_etl_qa_crew.config import Settings  # noqa: E402
from hc_etl_qa_crew.models import StageEvent  # noqa: E402
from hc_etl_qa_crew.services.pipeline import QAPipeline  # noqa: E402


def main(pipelines: list[str]) -> int:
    # Progress must appear as it happens, including when stdout is redirected
    # to a file, otherwise a long run looks hung.
    sys.stdout.reconfigure(line_buffering=True)
    os.environ["DEMO_MODE"] = "true"
    os.environ["DATA_SOURCE_MODE"] = "fixture"
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s - %(message)s")

    settings = Settings.load(ROOT / ".env")
    print(f"model={settings.llm_model} demo={settings.demo_mode} output={settings.output_dir}")
    if not settings.llm_ready():
        print("LLM_API_KEY is not set; cannot run the smoke test.")
        return 2

    def on_progress(key: str, event: StageEvent) -> None:
        print(f"  [{key}] {event.stage.value}: {event.status.value} {event.message[:80]}")

    run = QAPipeline(settings, progress=on_progress).run(pipelines)

    print("\n=== RESULT ===")
    print(f"run_id={run.run_id} successful={run.successful}")
    for result in run.results:
        source = result.source.value if result.source else "-"
        print(f"\n{result.pipeline_name}: {result.status.value} source={source}")
        if result.error:
            print(f"  error: {result.error}")
        if result.analysis:
            reqs = [e for e in result.analysis.entities if e.entity_type == "requirement"]
            dqs = [e for e in result.analysis.entities if e.entity_type == "data_quality"]
            print(f"  requirements={len(reqs)} data_quality_rules={len(dqs)}")
        if result.recon_plan:
            print(
                f"  strategies={len(result.recon_plan.strategies)} "
                f"quality_rules={len(result.recon_plan.quality_rules)}"
            )
        if result.test_cases:
            print(f"  test_cases={len(result.test_cases.test_cases)}")
        if result.pytest:
            print(
                f"  pytest_files={len(result.pytest.files)} "
                f"readiness={result.pytest.readiness.value}"
            )
        if result.coverage:
            print(
                f"  requirement_coverage={result.coverage.requirement_coverage_pct}% "
                f"automation={result.coverage.automation_pct}%"
            )
        for warning in result.warnings[:6]:
            print(f"  warn: {warning}")

    print(f"\nartifacts: {run.output_dir}")
    return 0 if run.successful else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["claims_etl_v1"]))
