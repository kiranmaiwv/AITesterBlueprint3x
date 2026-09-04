"""Task construction.

Each task declares its Pydantic output type via ``output_pydantic`` and
receives the earlier tasks as explicit ``context``, so CrewAI passes validated
upstream output forward instead of the agents re-deriving it.
"""

from __future__ import annotations

from crewai import Agent, Task

from hc_etl_qa_crew.models import (
    PytestBundle,
    ReconcilePlan,
    SchemaAnalysis,
    StarSchemaSnapshot,
    TestCaseSuite,
)

from .prompts import task_prompt


def _test_filename(pipeline_name: str) -> str:
    return f"test_{pipeline_name.lower().replace('-', '_')}.py"


def build_analysis_task(agent: Agent, snapshot_model: StarSchemaSnapshot) -> Task:
    prompt = task_prompt("analysis")
    return Task(
        description=prompt["description"].format(
            pipeline_name=snapshot_model.pipeline_name,
            source=snapshot_model.source.value,
            snapshot_text=snapshot_model.to_prompt_text(),
        ),
        expected_output=prompt["expected_output"].format(
            pipeline_name=snapshot_model.pipeline_name
        ),
        agent=agent,
        output_pydantic=SchemaAnalysis,
    )


def build_recon_task(
    agent: Agent,
    pipeline_name: str,
    context: list[Task],
    requirement_ids: list[str] | None = None,
    data_quality_ids: list[str] | None = None,
) -> Task:
    prompt = task_prompt("reconciliation")
    return Task(
        description=prompt["description"].format(
            pipeline_name=pipeline_name,
            requirement_ids=", ".join(requirement_ids or []) or "(none extracted)",
            data_quality_ids=(
                ", ".join(data_quality_ids or []) or "(none stated in the analysis)"
            ),
        ),
        expected_output=prompt["expected_output"].format(pipeline_name=pipeline_name),
        agent=agent,
        context=context,
        output_pydantic=ReconcilePlan,
    )


def build_test_cases_task(
    agent: Agent,
    pipeline_name: str,
    context: list[Task],
    requirement_ids: list[str],
    data_quality_ids: list[str],
) -> Task:
    prompt = task_prompt("test_cases")
    return Task(
        description=prompt["description"].format(
            pipeline_name=pipeline_name,
            requirement_ids=", ".join(requirement_ids) or "(none extracted)",
            data_quality_ids=(
                ", ".join(data_quality_ids) or "(none stated in the snapshot)"
            ),
        ),
        expected_output=prompt["expected_output"].format(pipeline_name=pipeline_name),
        agent=agent,
        context=context,
        output_pydantic=TestCaseSuite,
    )


def build_pytest_task(agent: Agent, pipeline_name: str, context: list[Task]) -> Task:
    prompt = task_prompt("pytest")
    return Task(
        description=prompt["description"].format(
            pipeline_name=pipeline_name,
            test_filename=_test_filename(pipeline_name),
        ),
        expected_output=prompt["expected_output"].format(pipeline_name=pipeline_name),
        agent=agent,
        context=context,
        output_pydantic=PytestBundle,
    )
