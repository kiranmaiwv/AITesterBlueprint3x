"""Results rendering: one tab per pipeline, six tabs inside each."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from hc_etl_qa_crew.models import AutomationCandidate, PipelineResult, PipelineStatus, RunSummary
from hc_etl_qa_crew.services import artifacts as artifacts_service

from .components import PIPELINE_BADGE, readiness_badge, source_badge
from .state import cached_zip


def render_run(run: RunSummary) -> None:
    _render_run_header(run)

    if not run.results:
        st.info("No pipelines were processed.")
        return

    labels = [
        f"{PIPELINE_BADGE[r.status][1]} {r.pipeline_name}" for r in run.results
    ]
    for tab, result in zip(st.tabs(labels), run.results, strict=True):
        with tab:
            _render_pipeline(run, result)


# --------------------------------------------------------------------------
def _render_run_header(run: RunSummary) -> None:
    st.subheader("Run summary")
    cols = st.columns(5)
    cols[0].metric("Run ID", run.run_id.replace("RUN-", ""))
    cols[1].metric("Pipelines", len(run.results))
    cols[2].metric("Completed", len(run.completed))
    cols[3].metric("With warnings", len(run.completed_with_warnings))
    cols[4].metric("Failed", len(run.failed))

    rows = [
        {
            "Pipeline": r.pipeline_name,
            "Status": PIPELINE_BADGE[r.status][0],
            "Source": r.source.value if r.source else "—",
            "Automation": r.pytest.readiness.value if r.pytest else "—",
            "Requirements": r.coverage.total_requirements if r.coverage else 0,
            "DQ rules": r.coverage.total_data_quality if r.coverage else 0,
            "Test cases": r.coverage.total_test_cases if r.coverage else 0,
            "Req coverage %": r.coverage.requirement_coverage_pct if r.coverage else 0.0,
            "Duration (s)": r.duration_seconds or 0.0,
        }
        for r in run.results
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    if not run.successful:
        st.error("No pipeline completed. Nothing was generated for this run.")

    zip_bytes = cached_zip(f"{run.run_id}::all", lambda: artifacts_service.build_zip(run))
    st.download_button(
        "Download all artifacts (ZIP)",
        data=zip_bytes,
        file_name=f"{run.run_id}_etl_qa_artifacts.zip",
        mime="application/zip",
        type="primary",
    )
    st.caption(f"Artifacts on disk: `{run.output_dir}`")


# --------------------------------------------------------------------------
def _render_pipeline(run: RunSummary, result: PipelineResult) -> None:
    label, icon = PIPELINE_BADGE[result.status]
    st.markdown(
        f"### {icon} {result.pipeline_name} — {label}<br>"
        f"{source_badge(result)}{readiness_badge(result)}",
        unsafe_allow_html=True,
    )

    if result.status is PipelineStatus.FAILED:
        st.error(result.error or "This pipeline failed for an unknown reason.")

    if result.warnings:
        with st.expander(f"{len(result.warnings)} warning(s)", expanded=False):
            for warning in result.warnings:
                st.warning(warning)

    tabs = st.tabs(
        [
            "Schema Analysis",
            "Reconciliation",
            "Test Cases",
            "pytest",
            "Traceability",
            "Run Details",
        ]
    )
    with tabs[0]:
        _render_schema_analysis(result)
    with tabs[1]:
        _render_reconciliation(result)
    with tabs[2]:
        _render_test_cases(result)
    with tabs[3]:
        _render_pytest(result)
    with tabs[4]:
        _render_traceability(result)
    with tabs[5]:
        _render_run_details(run, result)


def _render_schema_analysis(result: PipelineResult) -> None:
    if not result.analysis:
        st.info("No schema analysis was produced for this pipeline.")
        return
    analysis = result.analysis
    reqs = [e for e in analysis.entities if e.entity_type == "requirement"]
    dqs = [e for e in analysis.entities if e.entity_type == "data_quality"]
    cols = st.columns(4)
    cols[0].metric("Requirements", len(reqs))
    cols[1].metric("DQ rules", len(dqs))
    cols[2].metric("Missing info items", len(analysis.missing_information))
    cols[3].metric("Open questions", len(analysis.open_questions))

    if analysis.missing_information:
        st.warning(
            "**Missing information** (nothing was invented to fill these):\n\n"
            + "\n".join(f"- {m}" for m in analysis.missing_information)
        )
    st.markdown(artifacts_service.render_schema_analysis_md(analysis))
    _download(
        "Download schema_analysis.md",
        artifacts_service.render_schema_analysis_md(analysis),
        f"{result.pipeline_name}_schema_analysis.md",
        "text/markdown",
    )
    _download(
        "Download schema_analysis.json",
        json.dumps(analysis.model_dump(mode="json"), indent=2),
        f"{result.pipeline_name}_schema_analysis.json",
        "application/json",
    )


def _render_reconciliation(result: PipelineResult) -> None:
    if not result.recon_plan:
        st.info("No reconciliation strategy was produced for this pipeline.")
        return
    markdown = artifacts_service.render_recon_plan_md(result.recon_plan)
    st.markdown(markdown)
    _download(
        "Download reconciliation_strategy.md",
        markdown,
        f"{result.pipeline_name}_reconciliation_strategy.md",
        "text/markdown",
    )


def _render_test_cases(result: PipelineResult) -> None:
    suite = result.test_cases
    if not suite:
        st.info("No test cases were produced for this pipeline.")
        return

    frame = pd.DataFrame(
        [
            {
                "ID": c.id,
                "Title": c.title,
                "Priority": c.priority,
                "Type": c.test_type.value,
                "Dimension": c.quality_dimension.value,
                "Table": c.table_name,
                "Column": c.column_name,
                "Automation": c.automation_candidate.value,
                "Requirements": ", ".join(c.requirement_ids),
                "DQ rules": ", ".join(c.data_quality_ids),
                "Steps": len(c.steps),
                "Expected result": c.expected_result,
            }
            for c in suite.test_cases
        ]
    )

    filters = st.columns(5)
    search = filters[0].text_input("Search", key=f"search_{result.pipeline_name}")
    priority = filters[1].multiselect(
        "Priority", sorted(frame["Priority"].unique()), key=f"prio_{result.pipeline_name}"
    )
    dimension = filters[2].multiselect(
        "Dimension", sorted(frame["Dimension"].unique()), key=f"dim_{result.pipeline_name}"
    )
    automation = filters[3].multiselect(
        "Automation",
        sorted(frame["Automation"].unique()),
        key=f"auto_{result.pipeline_name}",
    )
    requirement_options = sorted(
        {
            r
            for c in suite.test_cases
            for r in (*c.requirement_ids, *c.data_quality_ids)
        }
    )
    requirement = filters[4].multiselect(
        "Requirement / DQ", requirement_options, key=f"req_{result.pipeline_name}"
    )

    view = frame
    if search:
        needle = search.lower()
        view = view[
            view.apply(lambda row: needle in " ".join(map(str, row.values)).lower(), axis=1)
        ]
    if priority:
        view = view[view["Priority"].isin(priority)]
    if dimension:
        view = view[view["Dimension"].isin(dimension)]
    if automation:
        view = view[view["Automation"].isin(automation)]
    if requirement:
        view = view[
            view.apply(
                lambda row: any(
                    r in f"{row['Requirements']}, {row['DQ rules']}" for r in requirement
                ),
                axis=1,
            )
        ]

    st.caption(f"Showing {len(view)} of {len(frame)} test cases")
    st.dataframe(view, width="stretch", hide_index=True)

    with st.expander("Full test case detail (Markdown)"):
        st.markdown(artifacts_service.render_test_cases_md(suite))

    _download(
        "Download test_cases.md",
        artifacts_service.render_test_cases_md(suite),
        f"{result.pipeline_name}_test_cases.md",
        "text/markdown",
    )
    _download(
        "Download test_cases.csv",
        artifacts_service.render_test_cases_csv(suite),
        f"{result.pipeline_name}_test_cases.csv",
        "text/csv",
    )


def _render_pytest(result: PipelineResult) -> None:
    bundle = result.pytest
    if not bundle:
        st.info("No pytest automation was produced for this pipeline.")
        return

    if bundle.readiness.value == "READY":
        st.success("Automation readiness: READY — no placeholders remain.")
    else:
        st.warning(
            f"Automation readiness: {bundle.readiness.value} — this code imports "
            "cleanly but is not execution-ready."
        )
    if bundle.missing_information:
        st.error(
            "**Required before this suite can run:**\n\n"
            + "\n".join(f"- {m}" for m in bundle.missing_information)
        )
    if bundle.assumptions:
        st.info("**Assumptions:**\n\n" + "\n".join(f"- {a}" for a in bundle.assumptions))
    if bundle.setup_notes:
        with st.expander("Setup notes", expanded=False):
            st.markdown(bundle.setup_notes)

    for file in bundle.files:
        st.markdown(f"**`{file.path}`**")
        st.code(file.content, language="python")
        st.download_button(
            f"Download {file.path.split('/')[-1]}",
            data=file.content,
            file_name=file.path.split("/")[-1],
            mime="text/plain",
            key=f"dl_{result.pipeline_name}_{file.path}",
        )

    _download(
        "Download pytest_automation.md",
        artifacts_service.render_pytest_md(bundle),
        f"{result.pipeline_name}_pytest_automation.md",
        "text/markdown",
    )


def _render_traceability(result: PipelineResult) -> None:
    coverage = result.coverage
    if not coverage:
        st.info("No traceability matrix was produced for this pipeline.")
        return

    cols = st.columns(4)
    cols[0].metric("Requirement coverage", f"{coverage.requirement_coverage_pct}%")
    cols[1].metric("Automated test cases", f"{coverage.automation_pct}%")
    cols[2].metric(
        "Covered DQ rules", f"{coverage.covered_data_quality}/{coverage.total_data_quality}"
    )
    cols[3].metric("Uncovered requirements", coverage.uncovered_requirements)

    frame = pd.DataFrame(
        [
            {
                "Requirement": row.requirement_id,
                "DQ rule": row.data_quality_id or "—",
                "Test cases": ", ".join(row.test_case_ids) or "—",
                "Automated": ", ".join(row.automated_test_case_ids) or "—",
                "Coverage": row.coverage_status.value,
                "Reason": row.reason,
            }
            for row in coverage.rows
        ]
    )
    st.dataframe(frame, width="stretch", hide_index=True)

    for label, values in (
        ("Requirements with no test case", coverage.orphan_requirement_ids),
        ("DQ rules with no test case", coverage.orphan_data_quality_ids),
        ("Test cases that trace to nothing", coverage.orphan_test_case_ids),
        ("References to ids that do not exist", coverage.unknown_reference_ids),
    ):
        if values:
            st.warning(f"**{label}:** {', '.join(values)}")

    _download(
        "Download traceability_matrix.csv",
        artifacts_service.render_traceability_csv(coverage),
        f"{result.pipeline_name}_traceability_matrix.csv",
        "text/csv",
    )


def _render_run_details(run: RunSummary, result: PipelineResult) -> None:
    cols = st.columns(3)
    cols[0].metric("Source", result.source.value if result.source else "—")
    cols[1].metric("Duration", f"{result.duration_seconds or 0}s")
    cols[2].metric("Status", PIPELINE_BADGE[result.status][0])

    if result.snapshots:
        with st.expander("Table snapshots (row counts)", expanded=False):
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Table": s.table_name,
                            "Source": s.source.value,
                            "Rows": s.row_count,
                            "Columns": len(s.column_names),
                        }
                        for s in result.snapshots
                    ]
                ),
                width="stretch",
                hide_index=True,
            )

    st.markdown("**Stages**")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Stage": s.stage.value,
                    "Status": s.status.value,
                    "Message": s.message,
                    "Started": s.started_at.strftime("%H:%M:%S") if s.started_at else "—",
                    "Duration (s)": s.duration_seconds if s.duration_seconds is not None else "—",
                }
                for s in result.stages
            ]
        ),
        width="stretch",
        hide_index=True,
    )

    manifest = artifacts_service.build_ticket_manifest(result)
    with st.expander("manifest.json"):
        st.json(manifest)
    _download(
        "Download manifest.json",
        json.dumps(manifest, indent=2),
        f"{result.pipeline_name}_manifest.json",
        "application/json",
    )

    if result.status is not PipelineStatus.FAILED:
        zip_bytes = cached_zip(
            f"{run.run_id}::{result.pipeline_name}",
            lambda: artifacts_service.build_zip(run, [result.pipeline_name]),
        )
        st.download_button(
            f"Download {result.pipeline_name} artifacts (ZIP)",
            data=zip_bytes,
            file_name=f"{run.run_id}_{result.pipeline_name}.zip",
            mime="application/zip",
            key=f"zip_{result.pipeline_name}",
        )

    if result.test_cases and any(
        c.automation_candidate is AutomationCandidate.NO for c in result.test_cases.test_cases
    ):
        manual = [
            c.id
            for c in result.test_cases.test_cases
            if c.automation_candidate is AutomationCandidate.NO
        ]
        st.caption(f"Manual-only test cases: {', '.join(manual)}")


def _download(label: str, data: str, filename: str, mime: str) -> None:
    st.download_button(label, data=data, file_name=filename, mime=mime, key=f"dl_{filename}")
