"""Tests for prompt loading, agent/task construction and callbacks."""

from __future__ import annotations

import pytest

from hc_etl_qa_crew.crew.callbacks import ProgressReporter, new_stage_set
from hc_etl_qa_crew.crew.prompts import agent_prompt, load_prompts, task_prompt
from hc_etl_qa_crew.exceptions import ConfigurationError
from hc_etl_qa_crew.models import StageEvent, StageName, StageStatus


def test_agents_yaml_has_four_agents() -> None:
    data = load_prompts("agents")
    assert set(data) == {
        "schema_analyst",
        "recon_strategist",
        "test_case_writer",
        "pytest_coder",
    }


def test_tasks_yaml_has_four_tasks() -> None:
    data = load_prompts("tasks")
    assert set(data) == {"analysis", "reconciliation", "test_cases", "pytest"}


def test_agent_prompt_has_required_fields() -> None:
    for key in ("schema_analyst", "pytest_coder"):
        prompt = agent_prompt(key)
        assert {"role", "goal", "backstory"} <= set(prompt)
        assert prompt["role"].strip()


def test_task_prompt_has_required_fields() -> None:
    for key in ("analysis", "pytest"):
        prompt = task_prompt(key)
        assert {"description", "expected_output"} <= set(prompt)


def test_task_prompts_mention_pipeline_placeholder() -> None:
    # The format placeholders the task builders rely on must exist.
    for key in ("analysis", "reconciliation", "test_cases", "pytest"):
        description = task_prompt(key)["description"]
        assert "{pipeline_name}" in description, key


def test_missing_prompt_file_raises() -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_prompts("does_not_exist")


# --------------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------------
def test_new_stage_set_has_six_stages() -> None:
    stages = new_stage_set()
    assert len(stages) == 6
    assert [s.stage for s in stages] == list(StageName)


def test_progress_reporter_emits_transitions() -> None:
    events: list[tuple[str, StageEvent]] = []

    def sink(pipeline_name: str, event: StageEvent) -> None:
        events.append((pipeline_name, event))

    reporter = ProgressReporter(sink)
    event = StageEvent(stage=StageName.ANALYSIS)
    reporter.start("claims_etl_v1", event, "running the analysis")
    assert event.status is StageStatus.RUNNING
    assert event.started_at is not None
    reporter.finish("claims_etl_v1", event, StageStatus.COMPLETED, "done")
    assert event.status is StageStatus.COMPLETED
    assert event.finished_at is not None
    assert len(events) == 2
    assert events[0][0] == "claims_etl_v1"


def test_progress_reporter_survives_broken_sink() -> None:
    def broken(pipeline_name: str, event: StageEvent) -> None:  # noqa: ARG001
        raise RuntimeError("ui exploded")

    reporter = ProgressReporter(broken)
    event = StageEvent(stage=StageName.FETCH)
    reporter.start("claims_etl_v1", event)  # must not raise


def test_progress_reporter_fail() -> None:
    reporter = ProgressReporter(None)
    event = StageEvent(stage=StageName.PYTEST)
    reporter.fail("claims_etl_v1", event, "no good")
    assert event.status is StageStatus.FAILED
    assert event.message == "no good"
