"""Reusable Streamlit widgets: header, configuration panel, input, progress."""

from __future__ import annotations

from typing import Any

import streamlit as st

from hc_etl_qa_crew.config import DataSourceMode, Settings
from hc_etl_qa_crew.models import PipelineResult, PipelineStatus, StageName, StageStatus

STATUS_ICON = {
    StageStatus.PENDING.value: "⚪",
    StageStatus.RUNNING.value: "🔵",
    StageStatus.COMPLETED.value: "🟢",
    StageStatus.WARNING.value: "🟡",
    StageStatus.FAILED.value: "🔴",
}

PIPELINE_BADGE = {
    PipelineStatus.COMPLETED: ("Completed", "🟢"),
    PipelineStatus.COMPLETED_WITH_WARNINGS: ("Completed with warnings", "🟡"),
    PipelineStatus.FAILED: ("Failed", "🔴"),
    PipelineStatus.RUNNING: ("Running", "🔵"),
    PipelineStatus.PENDING: ("Pending", "⚪"),
}


def inject_theme() -> None:
    """Teal/blue healthcare data theme, applied on top of the Streamlit config."""
    st.markdown(
        """
        <style>
        .qa-hero {
            background: linear-gradient(135deg, #064e3b 0%, #0f766e 55%, #14b8a6 100%);
            padding: 1.6rem 1.9rem; border-radius: 14px; color: #ffffff;
            margin-bottom: 1.2rem;
        }
        .qa-hero h1 { color:#fff; margin:0 0 .35rem 0; font-size:2.05rem; letter-spacing:-.5px; }
        .qa-hero p  { color:#d1fae5; margin:0; font-size:1.02rem; }
        .qa-badge {
            display:inline-block; padding:.16rem .6rem; border-radius:999px;
            font-size:.76rem; font-weight:600; letter-spacing:.3px;
            border:1px solid rgba(255,255,255,.35); margin-right:.4rem;
        }
        .qa-badge-live   { background:#0e7490; color:#fff; }
        .qa-badge-demo   { background:#b45309; color:#fff; }
        .qa-badge-ready  { background:#15803d; color:#fff; }
        .qa-badge-needs  { background:#b45309; color:#fff; }
        .qa-stage {
            border-left:3px solid #0f766e; padding:.28rem .7rem; margin:.18rem 0;
            background:rgba(15,118,110,.06); border-radius:0 6px 6px 0; font-size:.9rem;
        }
        div[data-testid="stMetricValue"] { font-size:1.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(settings: Settings) -> None:
    st.markdown(
        f"""
        <div class="qa-hero">
          <h1>{settings.app_name}</h1>
          <p>Turn a healthcare star-schema ETL load into schema analysis,
             reconciliation strategy, data-quality test cases, and pytest + SQL
             automation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_config_panel(settings: Settings) -> None:
    """Redacted readiness only. No secret is ever displayed or collected here."""
    status = settings.status()

    st.sidebar.subheader("Configuration")
    for label, key in (
        ("LLM", "llm"),
        ("Data source", "data_source"),
    ):
        block = status[key]
        icon = "🟢" if block["ready"] else "🔴"
        with st.sidebar.expander(f"{icon} {label}", expanded=not block["ready"]):
            for name, value in block.items():
                if name == "ready":
                    continue
                st.caption(f"**{name}**: {value}")

    pipeline = status["pipeline"]
    st.sidebar.caption(f"Output `{pipeline['output_dir']}`")
    if settings.demo_mode:
        st.sidebar.warning(
            "DEMO MODE is on. Data is read from local fixtures, not a warehouse."
        )

    problems = settings.blocking_problems()
    if problems:
        st.sidebar.error("Not ready to run:\n\n" + "\n\n".join(f"- {p}" for p in problems))
    else:
        st.sidebar.success("Ready to run.")

    st.sidebar.caption(
        "Secrets come from environment variables or `.streamlit/secrets.toml`. "
        "They are never entered in the UI and never displayed."
    )


def render_input_area(settings: Settings) -> str:
    """The pipeline input box and a read-only data-source note."""
    left, right = st.columns([3, 2], gap="large")

    with left:
        pipelines = st.text_area(
            "Star-schema ETL pipeline",
            key="pipeline_input",
            value="claims_etl_v1",
            height=88,
            placeholder="claims_etl_v1",
            help=(
                "One registered pipeline per line. The demo registers "
                "'claims_etl_v1' (1 fact + 5 dimensions). Duplicates are "
                "removed."
            ),
        )
        st.caption(
            "The button below runs the four-agent QA crew over this pipeline. "
            "It **generates** the analysis, strategy, test cases and pytest "
            "automation (an LLM call per stage, so it takes a few minutes). "
            "To *execute* the generated tests, run "
            "`python scripts/run_generated_tests.py` afterwards."
        )

    with right:
        mode_label = (
            "Fixture (demo dataset)"
            if settings.data_source_mode is DataSourceMode.FIXTURE
            else "Live warehouse"
        )
        st.caption(f"**Data source mode:** {mode_label}")
        st.caption("Controlled by `DATA_SOURCE_MODE` in the environment.")

    with st.expander("Advanced settings"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.caption(f"Model: `{settings.llm_model}`")
            st.caption(f"Temperature: `{settings.llm_temperature}`")
        with col_b:
            st.caption(f"Max pipelines: `{settings.pipeline_max_runs}`")
            st.caption("Retries per stage: `1 repair attempt`")
        with col_c:
            st.caption(f"Run timeout: `{settings.pipeline_run_timeout_seconds}s`")
            st.caption(f"Output dir: `{settings.output_dir}`")
        st.caption(
            "These come from the environment. Change them in `.env` or "
            "`.streamlit/secrets.toml` and restart."
        )

    return pipelines


def render_parse_feedback(parsed: Any, settings: Settings) -> None:
    if parsed.duplicates:
        st.info(f"Removed {len(parsed.duplicates)} duplicate(s): {', '.join(parsed.duplicates)}")
    if parsed.invalid:
        st.warning(
            "Ignored entries that are not registered pipelines: "
            + ", ".join(parsed.invalid)
        )
    if parsed.dropped_over_limit:
        st.warning(
            f"Only the first {settings.pipeline_max_runs} pipelines are processed. "
            f"Dropped: {', '.join(parsed.dropped_over_limit)}"
        )


def source_badge(result: PipelineResult) -> str:
    if not result.source:
        return ""
    css = {
        "fixture": "qa-badge-live",
        "live": "qa-badge-live",
        "DEMO_FIXTURE": "qa-badge-demo",
    }.get(result.source.value, "qa-badge-live")
    return f'<span class="qa-badge {css}">Source: {result.source.value}</span>'


def readiness_badge(result: PipelineResult) -> str:
    if not result.pytest:
        return ""
    value = result.pytest.readiness.value
    css = "qa-badge-ready" if value == "READY" else "qa-badge-needs"
    return f'<span class="qa-badge {css}">Automation: {value}</span>'


def render_stage_list(stages: dict[str, dict[str, Any]]) -> None:
    """Render the visible agent stages for one pipeline during a run."""
    for stage in StageName:
        info = stages.get(stage.value, {})
        status = info.get("status", StageStatus.PENDING.value)
        message = info.get("message", "")
        icon = STATUS_ICON.get(status, "⚪")
        detail = f" — {message}" if message else ""
        st.markdown(
            f'<div class="qa-stage">{icon} <strong>{stage.value}</strong>{detail}</div>',
            unsafe_allow_html=True,
        )
