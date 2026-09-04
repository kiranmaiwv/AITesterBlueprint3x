"""Pipeline run input parsing, normalization, validation and deduplication.

Accepts commas, spaces, newlines and semicolons in any combination, which is
what people actually paste out of a runbook. Recognized names are resolved
through the schema registry's alias table.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from hc_etl_qa_crew.exceptions import RunInputError
from hc_etl_qa_crew.schema_registry.star_schema import PIPELINE_NAME

_SPLIT_RE = re.compile(r"[,\s;]+")


@dataclass
class ParsedRuns:
    """Result of parsing the pipeline box. Nothing is silently discarded."""

    valid: list[str] = field(default_factory=list)
    invalid: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    dropped_over_limit: list[str] = field(default_factory=list)

    @property
    def has_valid(self) -> bool:
        return bool(self.valid)


def parse_run_input(
    raw: str,
    max_runs: int = 20,
    max_chars: int = 4000,
) -> ParsedRuns:
    """Turn free-form input into an ordered, unique list of pipeline names.

    Order is preserved (first occurrence wins) so results appear in the order
    the user typed them. Unknown names are reported as invalid rather than
    silently dropped.
    """
    if raw is None:
        raise RunInputError("No pipeline input was provided")
    if len(raw) > max_chars:
        raise RunInputError(
            f"Pipeline input is too long ({len(raw)} characters, limit {max_chars})"
        )

    result = ParsedRuns()
    seen: set[str] = set()
    for token in _SPLIT_RE.split(raw.strip()):
        if not token:
            continue
        name = token.strip().lower()
        # Only the canonical registered pipeline name is valid pipeline input.
        # Table aliases are for the data tool, not for the pipeline box.
        if name != PIPELINE_NAME:
            result.invalid.append(token.strip())
            continue
        if name in seen:
            result.duplicates.append(token.strip())
            continue
        seen.add(name)
        if len(result.valid) >= max_runs:
            result.dropped_over_limit.append(token.strip())
            continue
        result.valid.append(name)
    return result


def safe_path_segment(value: str) -> str:
    """Make a filesystem-safe segment out of a pipeline name.

    Pipeline input must never be able to escape the run directory, so anything
    outside ``[A-Za-z0-9._-]`` is replaced and traversal is stripped.
    """
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", (value or "").strip())
    cleaned = cleaned.replace("..", "_").strip("._-")
    return cleaned or "unknown"
