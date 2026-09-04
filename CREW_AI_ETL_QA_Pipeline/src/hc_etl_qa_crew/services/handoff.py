"""Compact stage-to-stage handoffs.

Why this exists: CrewAI's ``Task.context`` forwards the *raw text* of every
upstream task. In a four-stage pipeline that compounds, and by stage three the
prompt carries the full JSON of the analysis and the plan, source quotes and
all. Large models cope; several do not, and return truncated or empty
completions.

So the pipeline hands each stage a deterministic summary rendered from the
*validated* upstream object instead. That is strictly better than the raw
text: it is smaller, it cannot contain anything the schema rejected, and it
carries exactly the ids the next stage is allowed to reference.
"""

from __future__ import annotations

from hc_etl_qa_crew.models import (
    AutomationCandidate,
    ReconcilePlan,
    SchemaAnalysis,
    TestCaseSuite,
)

#: Keep a single list from swamping the prompt on a very large run.
_MAX_ITEMS = 40
_MAX_CHARS = 240


def _clip(text: str, limit: int = _MAX_CHARS) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _bullets(title: str, values: list[str]) -> list[str]:
    if not values:
        return []
    return [f"{title}:", *[f"- {_clip(v)}" for v in values[:_MAX_ITEMS]]]


def analysis_handoff(analysis: SchemaAnalysis) -> str:
    """What the reconciliation strategist and the case writer need from stage 1."""
    lines = [
        "## VALIDATED SCHEMA & TRANSFORM ANALYSIS (from the previous task)",
        f"Pipeline: {analysis.pipeline_name} — {_clip(analysis.summary)}",
        f"Fact table: {analysis.fact_table}",
        f"Dimension tables: {', '.join(analysis.dimension_tables) or '(none)'}",
    ]

    lines.append("")
    lines.append("Requirements (use these ids exactly, never invent one):")
    for entity in analysis.entities[:_MAX_ITEMS]:
        if entity.entity_type == "requirement":
            lines.append(
                f"- {entity.id} [{entity.provenance.value}] "
                f"{_clip(entity.text)} (table: {entity.table_name or '—'})"
            )
    if not any(e.entity_type == "requirement" for e in analysis.entities):
        lines.append("- (none extracted)")

    lines.append("")
    lines.append("Data-quality rules (use these ids exactly):")
    for entity in analysis.entities[:_MAX_ITEMS]:
        if entity.entity_type == "data_quality":
            lines.append(
                f"- {entity.id} [{entity.severity.value}] "
                f"{_clip(entity.text)} (table: {entity.table_name or '—'})"
            )
    if not any(e.entity_type == "data_quality" for e in analysis.entities):
        lines.append("- (none stated; do not invent any)")

    for title, values in (
        ("Risks", analysis.risks),
        ("Missing information (do not fill these in with guesses)",
         analysis.missing_information),
    ):
        block = _bullets(title, values)
        if block:
            lines.extend(["", *block])
    return "\n".join(lines)


def recon_handoff(plan: ReconcilePlan) -> str:
    """What the case writer needs from stage 2: strategies and quality rules."""
    lines = [
        "## VALIDATED RECONCILIATION & QUALITY STRATEGY (from the previous task)",
        f"Pipeline: {plan.pipeline_name} — {_clip(plan.summary)}",
        "",
        "Reconciliation strategies:",
    ]
    for strategy in plan.strategies[:_MAX_ITEMS]:
        lines.append(
            f"- {strategy.id} [{strategy.recon_type.value}] {_clip(strategy.name)}: "
            f"{_clip(strategy.description)}"
        )
    if not plan.strategies:
        lines.append("- (none)")

    lines.append("")
    lines.append("Quality rules to enforce in test cases:")
    for rule in plan.quality_rules[:_MAX_ITEMS]:
        lines.append(
            f"- {rule.id} [{rule.dimension.value}, {rule.severity.value}] "
            f"{_clip(rule.name)} on {rule.table_name}.{rule.column_name or '*'} "
            f"(threshold: {rule.threshold or '—'})"
        )
    if not plan.quality_rules:
        lines.append("- (none stated; do not invent any)")
    return "\n".join(lines)


def cases_handoff(suite: TestCaseSuite) -> str:
    """What the pytest coder needs from stage 3.

    Only the automatable cases. Sending the manual-only ones would just invite
    the coder to automate something a human already judged un-automatable.
    """
    automatable = [
        case
        for case in suite.test_cases
        if case.automation_candidate in (AutomationCandidate.YES, AutomationCandidate.PARTIAL)
    ]
    manual = [c.id for c in suite.test_cases if c not in automatable]

    lines = [
        "## VALIDATED TEST CASES (from the previous task)",
        f"{len(suite.test_cases)} test cases, {len(automatable)} marked for automation.",
        "",
        "Automate ONLY these:",
    ]
    if not automatable:
        lines.append("- (none: no test case was marked Yes or Partial)")

    for case in automatable[:_MAX_ITEMS]:
        refs = ", ".join([*case.requirement_ids, *case.data_quality_ids])
        lines += [
            "",
            f"### {case.id} [{case.automation_candidate.value}, {case.priority}, "
            f"{case.test_type.value}] {_clip(case.title)}",
            f"traces to: {refs}",
            f"table: {case.table_name or '—'}; column: {case.column_name or '—'}",
        ]
        if case.preconditions:
            lines.append(f"preconditions: {_clip('; '.join(case.preconditions))}")
        if case.test_data:
            lines.append(f"test data: {_clip('; '.join(case.test_data))}")
        for step in case.steps[:15]:
            expected = f" -> {_clip(step.expected, 120)}" if step.expected else ""
            lines.append(f"  {step.number}. {_clip(step.action, 160)}{expected}")
        if case.expected_result:
            lines.append(f"expected result: {_clip(case.expected_result)}")
        if case.assumptions_or_blockers:
            lines.append(
                f"blockers: {_clip('; '.join(case.assumptions_or_blockers))}"
            )

    if manual:
        lines += ["", f"Do NOT automate (marked No): {', '.join(manual[:_MAX_ITEMS])}"]
    return "\n".join(lines)
