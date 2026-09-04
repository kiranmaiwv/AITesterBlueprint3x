"""Tests for pipeline input parsing and path safety.

Only the canonical pipeline name (claims_etl_v1) is a valid pipeline input.
Table aliases are for the *data tool*, not the pipeline box.
"""

from __future__ import annotations

import pytest

from hc_etl_qa_crew.exceptions import RunInputError
from hc_etl_qa_crew.services.pipelines import parse_run_input, safe_path_segment


def test_parse_accepts_pipeline_name() -> None:
    parsed = parse_run_input("claims_etl_v1")
    assert parsed.valid == ["claims_etl_v1"]
    assert parsed.invalid == []
    assert parsed.duplicates == []


def test_parse_rejects_table_aliases_in_pipeline_box() -> None:
    parsed = parse_run_input("member, claims, dx\nfact")
    assert parsed.valid == []
    assert set(parsed.invalid) == {"member", "claims", "dx", "fact"}


def test_parse_deduplicates_canonical_name() -> None:
    parsed = parse_run_input("claims_etl_v1 claims_etl_v1")
    assert parsed.valid == ["claims_etl_v1"]
    assert parsed.duplicates == ["claims_etl_v1"]


def test_parse_reports_unknown_tokens() -> None:
    parsed = parse_run_input("claims_etl_v1 bogus_etl_v9")
    assert parsed.valid == ["claims_etl_v1"]
    assert parsed.invalid == ["bogus_etl_v9"]


def test_parse_handles_mixed_separators() -> None:
    parsed = parse_run_input("claims_etl_v1; claims_etl_v1\nclaims_etl_v1")
    assert parsed.valid == ["claims_etl_v1"]
    assert len(parsed.duplicates) == 2


def test_parse_uppercases_and_normalizes() -> None:
    parsed = parse_run_input("CLAIMS_ETL_V1")
    assert parsed.valid == ["claims_etl_v1"]


def test_parse_none_raises() -> None:
    with pytest.raises(RunInputError, match="No pipeline input"):
        parse_run_input(None)


def test_parse_over_max_chars_raises() -> None:
    with pytest.raises(RunInputError, match="too long"):
        parse_run_input("x" * 500, max_chars=100)


def test_parse_overflow_is_reported_as_duplicate_first() -> None:
    # With one registered pipeline, a second token is a duplicate before it
    # can ever be an overflow.
    parsed = parse_run_input("claims_etl_v1 claims_etl_v1", max_runs=1)
    assert parsed.valid == ["claims_etl_v1"]
    assert parsed.duplicates == ["claims_etl_v1"]
    assert parsed.dropped_over_limit == []


def test_parse_empty_input_has_no_valid() -> None:
    parsed = parse_run_input("   ")
    assert not parsed.has_valid
    assert parsed.valid == []


def test_safe_path_segment_removes_traversal() -> None:
    assert safe_path_segment("claims_etl_v1") == "claims_etl_v1"
    assert safe_path_segment("../evil") == "evil"
    assert safe_path_segment("a/b") == "a_b"
    assert safe_path_segment("") == "unknown"
    assert safe_path_segment("..") == "unknown"
