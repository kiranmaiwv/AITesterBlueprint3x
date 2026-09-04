"""Deterministic traceability and coverage.

Coverage numbers are computed in Python from the validated objects. An agent
is never asked how well it covered the data-quality rules, because an agent
has an obvious incentive to say "fully".
"""

from __future__ import annotations

from hc_etl_qa_crew.models import (
    AutomationCandidate,
    CoverageReport,
    CoverageStatus,
    PytestBundle,
    SchemaAnalysis,
    TestCaseSuite,
    TraceabilityRow,
)


def build_coverage(
    analysis: SchemaAnalysis,
    suite: TestCaseSuite | None,
    bundle: PytestBundle | None = None,
) -> CoverageReport:
    """Map requirements and data-quality rules onto test cases and automation."""
    cases = list(suite.test_cases) if suite else []
    req_ids = {e.id for e in analysis.entities if e.entity_type == "requirement"}
    dq_ids = {e.id for e in analysis.entities if e.entity_type == "data_quality"}
    req_text = {e.id: e.text for e in analysis.entities if e.entity_type == "requirement"}
    dq_text = {e.id: e.text for e in analysis.entities if e.entity_type == "data_quality"}

    automated_case_ids = {t.test_case_id.strip().upper() for t in (bundle.traces if bundle else [])}
    intended_automation = {
        c.id
        for c in cases
        if c.automation_candidate in (AutomationCandidate.YES, AutomationCandidate.PARTIAL)
    }

    cases_by_req: dict[str, list[str]] = {r: [] for r in req_ids}
    cases_by_dq: dict[str, list[str]] = {d: [] for d in dq_ids}
    unknown_refs: set[str] = set()

    for case in cases:
        for rid in case.requirement_ids:
            key = rid.strip().upper()
            if key in cases_by_req:
                cases_by_req[key].append(case.id)
            else:
                unknown_refs.add(key)
        for did in case.data_quality_ids:
            key = did.strip().upper()
            if key in cases_by_dq:
                cases_by_dq[key].append(case.id)
            else:
                unknown_refs.add(key)

    # Data-quality rules inherit onto the requirements that reference them.
    dq_by_req: dict[str, list[str]] = {r: [] for r in req_ids}
    for entity in analysis.entities:
        if entity.entity_type != "data_quality":
            continue
        for rid in entity.source_quote.split(","):  # soft link, not validated upstream
            rid = rid.strip().upper()
            if rid in dq_by_req:
                dq_by_req[rid].append(entity.id)

    rows: list[TraceabilityRow] = []
    covered_reqs = partial_reqs = 0

    for entity in analysis.entities:
        if entity.entity_type == "data_quality":
            continue
        linked_dqs = dq_by_req.get(entity.id, [])
        row_specs = (
            [(d, dq_text.get(d, "")) for d in linked_dqs] if linked_dqs else [("", "")]
        )

        req_case_ids: set[str] = set(cases_by_req.get(entity.id, []))
        for dq_id, _ in row_specs:
            if dq_id:
                req_case_ids.update(cases_by_dq.get(dq_id, []))

        for dq_id, dq_body in row_specs:
            row_cases = sorted(
                set(cases_by_req.get(entity.id, []))
                | set(cases_by_dq.get(dq_id, []) if dq_id else [])
            )
            row_automated = sorted(c for c in row_cases if c in automated_case_ids)
            status, reason = _status_for(
                row_cases, row_automated, intended_automation, bundle
            )
            rows.append(
                TraceabilityRow(
                    requirement_id=entity.id,
                    requirement_text=req_text.get(entity.id, ""),
                    data_quality_id=dq_id,
                    data_quality_text=dq_body,
                    test_case_ids=row_cases,
                    automated_test_case_ids=row_automated,
                    coverage_status=status,
                    reason=reason,
                )
            )

        overall_cases = sorted(req_case_ids)
        overall_automated = sorted(c for c in overall_cases if c in automated_case_ids)
        overall_status, _ = _status_for(
            overall_cases, overall_automated, intended_automation, bundle
        )
        if overall_status is CoverageStatus.COVERED:
            covered_reqs += 1
        elif overall_status is CoverageStatus.PARTIAL:
            partial_reqs += 1

    # Data-quality rules that are not attached to any requirement still need a row.
    orphan_dqs = [
        d.id
        for d in analysis.entities
        if d.entity_type == "data_quality"
        and not any(r.strip().upper() in req_ids for r in d.source_quote.split(","))
    ]
    for dq_id in orphan_dqs:
        row_cases = sorted(set(cases_by_dq.get(dq_id, [])))
        row_automated = sorted(c for c in row_cases if c in automated_case_ids)
        status, reason = _status_for(row_cases, row_automated, intended_automation, bundle)
        rows.append(
            TraceabilityRow(
                requirement_id="(unlinked)",
                requirement_text="",
                data_quality_id=dq_id,
                data_quality_text=dq_text.get(dq_id, ""),
                test_case_ids=row_cases,
                automated_test_case_ids=row_automated,
                coverage_status=status,
                reason=reason or "Data-quality rule is not linked to any requirement",
            )
        )

    covered_dqs = sum(1 for d in dq_ids if cases_by_dq.get(d))
    orphan_cases = [
        c.id
        for c in cases
        if not any(r.strip().upper() in req_ids for r in c.requirement_ids)
        and not any(d.strip().upper() in dq_ids for d in c.data_quality_ids)
    ]

    return CoverageReport(
        pipeline_name=analysis.pipeline_name,
        rows=rows,
        total_requirements=len(req_ids),
        covered_requirements=covered_reqs,
        partially_covered_requirements=partial_reqs,
        uncovered_requirements=len(req_ids) - covered_reqs - partial_reqs,
        total_data_quality=len(dq_ids),
        covered_data_quality=covered_dqs,
        total_test_cases=len(cases),
        automated_test_cases=len([c for c in cases if c.id in automated_case_ids]),
        orphan_requirement_ids=sorted(r for r in req_ids if not cases_by_req.get(r)),
        orphan_data_quality_ids=sorted(d for d in dq_ids if not cases_by_dq.get(d)),
        orphan_test_case_ids=sorted(orphan_cases),
        unknown_reference_ids=sorted(unknown_refs),
    )


def _status_for(
    case_ids: list[str],
    automated_ids: list[str],
    intended_automation: set[str],
    bundle: PytestBundle | None,
) -> tuple[CoverageStatus, str]:
    """Coverage verdict for one row, with the reason spelled out."""
    if not case_ids:
        return CoverageStatus.UNCOVERED, "No test case references this item"

    wanted = [c for c in case_ids if c in intended_automation]
    if not wanted:
        return CoverageStatus.COVERED, "Covered by manual test cases"

    missing = [c for c in wanted if c not in automated_ids]
    if missing:
        return (
            CoverageStatus.PARTIAL,
            "Test cases exist but automation is missing for: " + ", ".join(missing),
        )
    if bundle and bundle.missing_information:
        return (
            CoverageStatus.COVERED,
            "Covered by automated tests (not yet execution-ready: "
            + "; ".join(bundle.missing_information[:2])
            + ")",
        )
    return CoverageStatus.COVERED, "Covered by automated and manual test cases"
