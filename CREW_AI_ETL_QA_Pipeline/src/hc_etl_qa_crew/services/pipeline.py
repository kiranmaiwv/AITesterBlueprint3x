"""Per-pipeline orchestration.

Execution model: the four tasks are built once per pipeline run with explicit
``context`` links, then run one stage at a time. CrewAI resolves ``context``
from the Task objects themselves, so running them stage by stage still passes
validated upstream output forward, while giving us a gate between every stage
where deterministic validation and a single repair attempt can happen.

Isolation: every pipeline run gets fresh Agents, Tasks and a fresh Crew, and
crew memory is off. Nothing carries from one run to the next.

Why a deterministic loop rather than ``Crew.kickoff_for_each``: that method
reuses one crew across every input, which is exactly the sharing this design
forbids, and it gives no gate between stages for validation or repair. A plain
loop over pipelines is simpler to reason about and keeps continue-on-error
behaviour explicit.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, ValidationError

from hc_etl_qa_crew.config import Settings, StructuredOutputMode
from hc_etl_qa_crew.crew.callbacks import ProgressCallback, ProgressReporter, new_stage_set
from hc_etl_qa_crew.crew.factory import build_pipeline_crew
from hc_etl_qa_crew.data_gateway.gateway import DataGateway
from hc_etl_qa_crew.exceptions import DataError, PipelineError, StructuredOutputError
from hc_etl_qa_crew.models import (
    PipelineResult,
    PipelineStatus,
    PytestBundle,
    ReconcilePlan,
    RunSummary,
    SchemaAnalysis,
    StageName,
    StageStatus,
    StarSchemaSnapshot,
    TableSnapshot,
    TestCaseSuite,
)
from hc_etl_qa_crew.schema_registry.star_schema import DIMENSION_TABLES, FACT_TABLE

from . import artifacts as artifacts_service
from .handoff import analysis_handoff, cases_handoff, recon_handoff
from .structured import (
    is_empty_response,
    json_mode_instruction,
    looks_truncated,
    parse_model,
    schema_rejected,
)
from .traceability import build_coverage
from .validation import (
    ValidationResult,
    validate_analysis,
    validate_pytest,
    validate_recon_plan,
    validate_test_cases,
)

logger = logging.getLogger(__name__)

TModel = TypeVar("TModel", bound=BaseModel)

#: Below this, a truncated response is not an over-long answer, it is a dropped
#: stream. Telling the model to "write less" then is incoherent (the target
#: would exceed what it actually produced) and does not address the cause.
LENGTHY_RESPONSE_CHARS = 3000

#: Hard ceiling on provider calls for one stage attempt. The ladder plus
#: empty-response retries could otherwise multiply out to something that takes
#: half an hour on a slow provider. Two of these can run per stage (the
#: original attempt and the single repair), so a stage costs at most 8 calls.
MAX_CALLS_PER_ATTEMPT = 4


def new_run_id(now: datetime | None = None) -> str:
    return f"RUN-{(now or datetime.now()).strftime('%Y%m%d-%H%M%S')}"


class QAPipeline:
    """Runs the four-agent pipeline over one or many star-schema pipelines."""

    def __init__(
        self,
        settings: Settings,
        gateway: DataGateway | None = None,
        progress: ProgressCallback | None = None,
    ):
        self.settings = settings
        self.gateway = gateway or DataGateway(settings)
        self.reporter = ProgressReporter(progress)
        # Whether this provider can enforce a JSON schema server-side. In
        # `auto` it starts optimistic and is switched off permanently the first
        # time the provider rejects one, so we never pay for that call twice.
        # Setting LLM_STRUCTURED_OUTPUT=prompt skips that probe entirely, which
        # is worth doing on a provider you already know cannot do it.
        self._schema_enforcement = (
            settings.llm_structured_output is not StructuredOutputMode.PROMPT
        )
        # Ask the provider for guaranteed-valid JSON when the schema cannot be
        # enforced. DeepSeek supports response_format=json_object and is
        # markedly more reliable with it than with free text.
        self._json_object_mode = True

    # ------------------------------------------------------------------
    def run(
        self,
        pipeline_names: Sequence[str],
        invalid_inputs: Sequence[str] | None = None,
        duplicates: Sequence[str] | None = None,
        run_id: str | None = None,
    ) -> RunSummary:
        """Process every pipeline, continuing past individual failures."""
        run = RunSummary(
            run_id=run_id or new_run_id(),
            requested_pipelines=[p.strip().lower() for p in pipeline_names],
            invalid_inputs=list(invalid_inputs or []),
            duplicates_removed=list(duplicates or []),
            started_at=datetime.now(),
        )

        output_dir = Path(self.settings.output_dir)
        run_dir = output_dir / run.run_id

        for name in run.requested_pipelines:
            result = PipelineResult(pipeline_name=name, stages=new_stage_set())
            run.results.append(result)
            try:
                self._run_pipeline(result)
            except Exception as exc:  # noqa: BLE001 - one run must not kill the batch
                logger.exception("pipeline %s failed", name)
                result.status = PipelineStatus.FAILED
                result.error = self.settings.redact(f"{type(exc).__name__}: {exc}")
            finally:
                result.finished_at = datetime.now()
                try:
                    artifacts_service.write_ticket_artifacts(result, run_dir)
                except Exception as exc:  # noqa: BLE001
                    logger.exception("could not write artifacts for %s", name)
                    result.warnings.append(
                        self.settings.redact(f"Artifact writing failed: {exc}")
                    )

        run.finished_at = datetime.now()
        artifacts_service.write_run_artifacts(run, output_dir)
        return run

    # ------------------------------------------------------------------
    def _run_pipeline(self, result: PipelineResult) -> None:
        name = result.pipeline_name
        result.started_at = datetime.now()
        result.status = PipelineStatus.RUNNING
        deadline = time.monotonic() + self.settings.pipeline_run_timeout_seconds

        # --- stage 0: fetch snapshots --------------------------------------
        fetch_stage = result.stage(StageName.FETCH)
        self.reporter.start(
            name, fetch_stage, f"Reading the star schema for {name}"
        )
        try:
            snapshots = self._fetch_all_snapshots()
        except DataError as exc:
            message = self.settings.redact(str(exc))
            detail = getattr(exc, "provider_errors", {})
            if detail:
                message += " (" + "; ".join(f"{k}: {v}" for k, v in detail.items()) + ")"
            self.reporter.fail(name, fetch_stage, message)
            result.status = PipelineStatus.FAILED
            result.error = message
            return
        result.snapshots = snapshots
        result.source = snapshots[0].source if snapshots else None
        self.reporter.finish(
            name,
            fetch_stage,
            StageStatus.COMPLETED,
            f"Read {len(snapshots)} tables via {snapshots[0].source.value}",
        )

        if not self.settings.llm_ready():
            message = "LLM is not configured, so no artifacts can be generated."
            result.status = PipelineStatus.FAILED
            result.error = message
            for stage_name in (
                StageName.ANALYSIS,
                StageName.RECONCILIATION,
                StageName.TEST_CASES,
                StageName.PYTEST,
            ):
                self.reporter.fail(name, result.stage(stage_name), message)
            return

        snapshot_model = StarSchemaSnapshot(
            pipeline_name=name,
            fact_table=FACT_TABLE.name,
            dimension_tables=[t.name for t in DIMENSION_TABLES],
            tables=snapshots,
            source=snapshots[0].source,
        )
        pipeline_crew = build_pipeline_crew(self.settings, snapshot_model)

        # --- stage 1: schema & transform analysis --------------------------
        analysis = self._stage(
            result,
            StageName.ANALYSIS,
            pipeline_crew.analysis_task,
            SchemaAnalysis,
            lambda obj: validate_analysis(obj, name),
            deadline,
        )

        # Ids only exist after analysis; refresh the prompts so the
        # reconciliation and test-case agents are told exactly which ids they
        # may reference (and may not invent).
        self._inject_known_ids(pipeline_crew.recon_task, analysis)
        self._inject_known_ids(pipeline_crew.cases_task, analysis)

        handoff = analysis_handoff(analysis)
        self._hand_off(pipeline_crew.recon_task, handoff)
        self._hand_off(pipeline_crew.cases_task, handoff)
        self._hand_off(pipeline_crew.pytest_task, handoff)

        # --- stage 2: reconciliation strategy ------------------------------
        recon = self._stage(
            result,
            StageName.RECONCILIATION,
            pipeline_crew.recon_task,
            ReconcilePlan,
            lambda obj: validate_recon_plan(obj, analysis, name),
            deadline,
        )

        self._hand_off(pipeline_crew.cases_task, recon_handoff(recon))

        # --- stage 3: data-quality test cases ------------------------------
        suite = self._stage(
            result,
            StageName.TEST_CASES,
            pipeline_crew.cases_task,
            TestCaseSuite,
            lambda obj: validate_test_cases(obj, analysis, name),
            deadline,
        )

        self._hand_off(pipeline_crew.pytest_task, cases_handoff(suite))

        # --- stage 4: pytest coder -----------------------------------------
        bundle = self._stage(
            result,
            StageName.PYTEST,
            pipeline_crew.pytest_task,
            PytestBundle,
            lambda obj: validate_pytest(obj, suite, name),
            deadline,
        )

        result.analysis = analysis
        result.recon_plan = recon
        result.test_cases = suite
        result.pytest = bundle

        # --- artifacts and coverage ----------------------------------------
        artifact_stage = result.stage(StageName.ARTIFACTS)
        self.reporter.start(name, artifact_stage, "Computing coverage")
        result.coverage = build_coverage(analysis, suite, bundle)
        self._warn_on_coverage(result)
        self.reporter.finish(
            name,
            artifact_stage,
            StageStatus.COMPLETED,
            f"{result.coverage.total_test_cases} test cases, "
            f"{result.coverage.requirement_coverage_pct}% requirement coverage",
        )

        result.status = (
            PipelineStatus.COMPLETED_WITH_WARNINGS
            if result.warnings
            else PipelineStatus.COMPLETED
        )

    # ------------------------------------------------------------------
    def _fetch_all_snapshots(self) -> list[TableSnapshot]:
        """Fetch the fact table and every dimension, in registry order."""
        snapshots: list[TableSnapshot] = []
        for table in (FACT_TABLE, *DIMENSION_TABLES):
            snapshot = self.gateway.fetch_snapshot(table)
            snapshots.append(snapshot)
        return snapshots

    # ------------------------------------------------------------------
    def _stage(
        self,
        result: PipelineResult,
        stage_name: StageName,
        task: Task,
        model: type[TModel],
        validator: Any,
        deadline: float,
    ) -> TModel:
        """Run one stage, validate it, and allow exactly one repair attempt."""
        name = result.pipeline_name
        stage = result.stage(stage_name)
        self.reporter.start(name, stage, f"{stage_name.value} running")

        if time.monotonic() > deadline:
            message = (
                f"Pipeline timeout of {self.settings.pipeline_run_timeout_seconds}s "
                f"reached before {stage_name.value}"
            )
            self.reporter.fail(name, stage, message)
            raise PipelineError(message)

        obj, validation = self._execute_and_validate(task, model, validator)

        if obj is None or not validation.ok:
            problems = validation.errors or ["structured output could not be parsed"]
            logger.info("repairing stage %s for %s: %s", stage_name.value, name, problems)
            self.reporter.start(
                name, stage, f"{stage_name.value} output rejected, one repair attempt"
            )
            self._append_repair_instruction(task, problems)
            obj, validation = self._execute_and_validate(task, model, validator)

        if obj is None:
            message = "; ".join(validation.errors) or "no valid structured output"
            self.reporter.fail(name, stage, self.settings.redact(message))
            raise StructuredOutputError(
                f"{stage_name.value} did not return a valid {model.__name__}: {message}"
            )
        if not validation.ok:
            message = "; ".join(validation.errors)
            self.reporter.fail(name, stage, self.settings.redact(message))
            raise PipelineError(f"{stage_name.value} failed validation: {message}")

        for warning in validation.warnings:
            result.warnings.append(f"[{stage_name.value}] {warning}")

        status = StageStatus.WARNING if validation.warnings else StageStatus.COMPLETED
        self.reporter.finish(
            name,
            stage,
            status,
            f"{stage_name.value} completed"
            + (f" with {len(validation.warnings)} warning(s)" if validation.warnings else ""),
        )
        return obj

    # ------------------------------------------------------------------
    def _execute_and_validate(
        self, task: Task, model: type[TModel], validator: Any
    ) -> tuple[TModel | None, ValidationResult]:
        """Run a single task in an isolated crew and validate its output.

        Tries provider-enforced schema output first. If the provider says it
        cannot do that, falls back to prompted JSON for this and every later
        stage, which is a downgrade in enforcement but not in validation: the
        result is still parsed into the same Pydantic model here.
        """
        # Attempt ladder, most enforced first:
        #   (schema)  provider enforces the JSON schema
        #   (json)    provider guarantees valid JSON, schema lives in the prompt
        #   (plain)   free text, schema lives in the prompt
        # A provider that refuses one rung is never asked for it again.
        ladder: list[tuple[bool, bool]] = []
        if self._schema_enforcement:
            ladder.append((True, False))
        if self._json_object_mode:
            ladder.append((False, True))
        ladder.append((False, False))

        empty_attempts = 0
        max_empty_attempts = max(1, self.settings.pipeline_max_retries)
        index = 0
        calls = 0

        while index < len(ladder):
            if calls >= MAX_CALLS_PER_ATTEMPT:
                logger.warning(
                    "stage hit the %s-call ceiling without a usable response",
                    MAX_CALLS_PER_ATTEMPT,
                )
                return None, ValidationResult(
                    errors=[
                        f"the provider did not return a usable {model.__name__} in "
                        f"{calls} attempts (empty or unparseable each time)"
                    ]
                )
            enforce, json_object = ladder[index]
            index += 1
            calls += 1
            try:
                self._kickoff_single(task, enforce_schema=enforce, json_object=json_object)
            except Exception as exc:  # noqa: BLE001 - LLM failures are stage failures
                strict = self.settings.llm_structured_output is StructuredOutputMode.SCHEMA
                if enforce and schema_rejected(exc) and not strict:
                    logger.warning(
                        "provider cannot enforce a JSON schema (%s); "
                        "switching to prompted JSON for the rest of this run",
                        type(exc).__name__,
                    )
                    self._schema_enforcement = False
                    continue
                if json_object and schema_rejected(exc):
                    logger.warning(
                        "provider rejected response_format=json_object; "
                        "falling back to plain prompted JSON"
                    )
                    self._json_object_mode = False
                    continue
                if is_empty_response(exc):
                    if empty_attempts < max_empty_attempts:
                        empty_attempts += 1
                        logger.warning(
                            "provider returned an empty completion, retry %s/%s",
                            empty_attempts,
                            max_empty_attempts,
                        )
                        time.sleep(min(2**empty_attempts, 8))
                        ladder.insert(index, (enforce, json_object))
                        continue
                    if index < len(ladder):
                        # Retrying the same rung is not working. A less
                        # constrained request sometimes succeeds where a
                        # format-constrained one keeps coming back empty, so
                        # step down instead of giving up.
                        logger.warning(
                            "still empty after %s retries; stepping down to a less "
                            "constrained request",
                            max_empty_attempts,
                        )
                        empty_attempts = 0
                        continue
                logger.warning("task execution failed: %s", exc)
                return None, ValidationResult(
                    errors=[self.settings.redact(f"{type(exc).__name__}: {exc}")]
                )

            obj = _extract_model(task, model)
            if obj is None:
                raw = getattr(getattr(task, "output", None), "raw", "") or ""
                if looks_truncated(raw) and len(raw) >= LENGTHY_RESPONSE_CHARS:
                    # A long cut-off response means the model wrote too much.
                    # A qualitative "be shorter" is ignored (measured: it came
                    # back three times longer), so give a concrete target.
                    target = len(raw) // 2
                    reason = (
                        f"your previous {model.__name__} response was cut off before the "
                        f"JSON finished ({len(raw)} characters, incomplete). The response "
                        f"MUST be under {target} characters this time, roughly HALF the "
                        "length. Cut the number of items first, then shorten every field "
                        "to one short sentence. Drop optional fields entirely. A partial "
                        "object is discarded, so completeness beats detail."
                    )
                elif looks_truncated(raw):
                    # Short truncation: the stream was dropped, not overlong.
                    # Asking for less would be incoherent, so ask for the same
                    # object again, complete.
                    reason = (
                        f"your previous {model.__name__} response stopped after only "
                        f"{len(raw)} characters, before the JSON was finished. That is an "
                        "incomplete transmission, not a content problem. Return the SAME "
                        "object again, complete from the opening brace to the closing "
                        "brace, and make sure the JSON is balanced before you stop."
                    )
                else:
                    reason = f"output did not parse into {model.__name__}"
                return None, ValidationResult(errors=[reason])
            try:
                return obj, validator(obj)
            except ValidationError as exc:
                return None, ValidationResult(errors=[str(exc)])

        return None, ValidationResult(errors=["no execution mode produced output"])

    def _kickoff_single(
        self, task: Task, enforce_schema: bool = True, json_object: bool = False
    ) -> None:
        """Execute exactly one task, keeping its declared context intact.

        With ``enforce_schema=False`` the Pydantic type is detached from the
        task and its JSON schema is appended to the prompt instead, which is
        what providers without native schema support need.

        ``json_object=True`` additionally asks the provider for
        ``response_format={"type": "json_object"}``: weaker than a schema, but
        it guarantees parseable JSON. It is skipped for an agent that has
        tools, because a tool call is not a JSON object and forcing the format
        would break the agent loop.
        """
        agent: Agent | None = task.agent
        if agent is None:
            raise PipelineError("Task has no agent assigned")

        model = task.output_pydantic
        original_description = task.description
        prompted = not enforce_schema and model is not None
        use_json_object = json_object and prompted and not getattr(agent, "tools", None)
        original_format = getattr(agent.llm, "response_format", None)

        if prompted:
            task.output_pydantic = None
            task.description = original_description + json_mode_instruction(model)
        if use_json_object:
            agent.llm.response_format = {"type": "json_object"}

        try:
            Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False,
                memory=False,
            ).kickoff()
        finally:
            if prompted:
                # Restore, so the schema is still known for parsing and for a
                # later repair attempt.
                task.output_pydantic = model
                task.description = original_description
            if use_json_object:
                agent.llm.response_format = original_format

    # ------------------------------------------------------------------
    @staticmethod
    def _append_repair_instruction(task: Task, problems: list[str]) -> None:
        """Add a single, bounded repair note. Never stacks up over attempts."""
        marker = "\n\n### CORRECTION REQUIRED (single retry)\n"
        base = task.description.split(marker)[0]
        bullets = "\n".join(f"- {p}" for p in problems[:10])
        task.description = (
            f"{base}{marker}"
            "Your previous attempt was rejected by deterministic validation:\n"
            f"{bullets}\n"
            "Fix exactly these problems and return the same structured object. "
            "Do not invent new content to satisfy a check: if information is "
            "genuinely missing, record it in the missing-information field "
            "instead of fabricating it."
        )

    @staticmethod
    def _hand_off(task: Task, block: str) -> None:
        """Append a validated upstream summary and drop the raw context.

        ``Task.context`` would forward the full raw text of every earlier task.
        We send a deterministic summary of the validated object instead, so the
        prompt stays bounded and cannot carry anything validation rejected.
        """
        task.description = f"{task.description}\n\n{block}"
        task.context = []

    @staticmethod
    def _inject_known_ids(task: Task, analysis: SchemaAnalysis) -> None:
        """Replace the id placeholders once the analysis has produced them."""
        req = ", ".join(analysis.requirement_ids) or "(none extracted)"
        dqs = ", ".join(analysis.data_quality_ids) or "(none stated in the snapshot)"
        description = task.description
        description = description.replace("(none extracted)", req, 1)
        description = description.replace("(none stated in the snapshot)", dqs, 1)
        description = description.replace("(none stated in the analysis)", dqs, 1)
        task.description = description

    def _warn_on_coverage(self, result: PipelineResult) -> None:
        coverage = result.coverage
        if coverage is None:
            return
        if coverage.orphan_requirement_ids:
            result.warnings.append(
                "[Coverage] Requirements with no test case: "
                + ", ".join(coverage.orphan_requirement_ids)
            )
        if coverage.orphan_data_quality_ids:
            result.warnings.append(
                "[Coverage] Data-quality rules with no test case: "
                + ", ".join(coverage.orphan_data_quality_ids)
            )
        if coverage.orphan_test_case_ids:
            result.warnings.append(
                "[Coverage] Test cases that trace to nothing: "
                + ", ".join(coverage.orphan_test_case_ids)
            )
        if coverage.unknown_reference_ids:
            result.warnings.append(
                "[Coverage] References to ids that do not exist: "
                + ", ".join(coverage.unknown_reference_ids)
            )


def _extract_model(task: Task, model: type[TModel]) -> TModel | None:
    """Pull the validated Pydantic object out of a finished task."""
    output = getattr(task, "output", None)
    if output is None:
        return None
    candidate = getattr(output, "pydantic", None)
    if isinstance(candidate, model):
        return candidate
    # The runtime did not attach the model, which is normal in prompted-JSON
    # mode. Parse it ourselves.
    payload = getattr(output, "json_dict", None)
    if isinstance(payload, dict):
        try:
            return model.model_validate(payload)
        except ValidationError:
            pass
    raw = getattr(output, "raw", None)
    if isinstance(raw, str):
        return parse_model(raw, model)
    return None
