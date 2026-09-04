"""Tests for the generated-tests runner (dialect translation + discovery)."""

from __future__ import annotations

from scripts.run_generated_tests import _find_pytest_tests, _translate_to_sqlite


def test_translate_information_schema_to_pragma() -> None:
    source = (
        'result = conn.execute(text(\n'
        '    "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = :table"\n'
        '), {"table": table})'
    )
    translated = _translate_to_sqlite(source)
    assert "information_schema" not in translated
    assert "pragma_table_info(:table)" in translated


def test_translate_leaves_row_count_queries_alone() -> None:
    source = 'result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))'
    assert _translate_to_sqlite(source) == source


def test_translate_is_idempotent() -> None:
    source = "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = :table"
    once = _translate_to_sqlite(source)
    assert _translate_to_sqlite(once) == once


def test_find_pytest_tests_discovers_generated_suite(tmp_path) -> None:
    run_dir = tmp_path / "RUN-20260904-000000" / "claims_etl_v1" / "pytest" / "tests"
    run_dir.mkdir(parents=True)
    (run_dir / "test_claims_etl_v1.py").write_text("def test_x():\n    pass\n")
    (run_dir / "conftest.py").write_text("")
    found = _find_pytest_tests(tmp_path / "RUN-20260904-000000")
    assert found is not None
    assert found.name == "tests"


def test_find_pytest_tests_returns_none_when_absent(tmp_path) -> None:
    assert _find_pytest_tests(tmp_path) is None
