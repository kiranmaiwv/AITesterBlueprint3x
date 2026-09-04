"""Builds one isolated crew per pipeline run.

A fresh Crew, fresh Agents and fresh Tasks are constructed for every run.
Nothing is shared between runs, so requirement ids or context from one
pipeline cannot leak into another.
"""

from __future__ import annotations

from dataclasses import dataclass

from crewai import Crew, Process, Task

from hc_etl_qa_crew.config import Settings
from hc_etl_qa_crew.models import StarSchemaSnapshot
from hc_etl_qa_crew.tools.data_tool import InspectDataTool

from .agents import (
    build_pytest_coder,
    build_recon_strategist,
    build_schema_analyst,
    build_test_case_writer,
)
from .tasks import (
    build_analysis_task,
    build_pytest_task,
    build_recon_task,
    build_test_cases_task,
)


@dataclass
class PipelineCrew:
    """A crew plus the individual tasks, so stage outputs stay addressable."""

    crew: Crew
    analysis_task: Task
    recon_task: Task
    cases_task: Task
    pytest_task: Task

    @property
    def tasks(self) -> list[Task]:
        return [self.analysis_task, self.recon_task, self.cases_task, self.pytest_task]


def build_pipeline_crew(
    settings: Settings,
    snapshot_model: StarSchemaSnapshot,
    data_tool: InspectDataTool | None = None,
) -> PipelineCrew:
    """Assemble the four-agent sequential crew for exactly one pipeline run.

    The analyst gets the read-only data tool; every later agent works from
    validated output only. A fresh crew is built per run, so nothing carries
    between pipelines.
    """
    # The snapshot text is already the full, deterministic picture of every
    # table, so the analyst does NOT get a live tool by default. Attaching a
    # tool forces CrewAI into a tool-calling loop that several providers
    # answer with empty completions on long structured generations. Pass an
    # explicit ``data_tool`` when a real re-read capability is wanted.
    analyst = build_schema_analyst(settings, data_tool)
    strategist = build_recon_strategist(settings)
    case_writer = build_test_case_writer(settings)
    coder = build_pytest_coder(settings)

    analysis_task = build_analysis_task(analyst, snapshot_model)
    recon_task = build_recon_task(strategist, snapshot_model.pipeline_name, [analysis_task])
    cases_task = build_test_cases_task(
        case_writer,
        snapshot_model.pipeline_name,
        [analysis_task, recon_task],
        [],
        [],
    )
    pytest_task = build_pytest_task(
        coder, snapshot_model.pipeline_name, [analysis_task, recon_task, cases_task]
    )

    crew = Crew(
        agents=[analyst, strategist, case_writer, coder],
        tasks=[analysis_task, recon_task, cases_task, pytest_task],
        process=Process.sequential,  # each stage needs the validated one before it
        verbose=False,
        memory=False,  # no cross-run memory, by design
    )
    return PipelineCrew(crew, analysis_task, recon_task, cases_task, pytest_task)
