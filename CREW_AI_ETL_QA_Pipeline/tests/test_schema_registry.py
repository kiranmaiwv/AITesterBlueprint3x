"""Tests for the canonical healthcare star-schema registry."""

from __future__ import annotations

import pytest

from hc_etl_qa_crew.schema_registry.star_schema import (
    DIMENSION_NAMES,
    DIMENSION_TABLES,
    FACT_NAME,
    FACT_TABLE,
    NAME_ALIASES,
    REGISTRY,
    ColumnSpec,
    TableKind,
    TableSpec,
    lookup_table,
)


def test_registry_has_one_fact_and_five_dimensions() -> None:
    kinds = [spec.kind for spec in REGISTRY]
    assert kinds.count(TableKind.FACT) == 1
    assert kinds.count(TableKind.DIMENSION) == 5
    assert len(REGISTRY) == 6


def test_fact_is_claims_and_dims_are_healthcare() -> None:
    assert FACT_NAME == "fact_claim_line"
    assert FACT_TABLE.kind is TableKind.FACT
    assert set(DIMENSION_NAMES) == {
        "dim_member",
        "dim_provider",
        "dim_diagnosis",
        "dim_service",
        "dim_time",
    }


def test_every_entity_dimension_specifies_hundred_rows() -> None:
    for spec in DIMENSION_TABLES:
        if spec.name != "dim_time":
            assert spec.expected_row_count == 100, spec.name
    assert FACT_TABLE.expected_row_count == 100


def test_fact_has_five_foreign_keys_to_dimensions() -> None:
    fks = [c.foreign_key for c in FACT_TABLE.columns if c.foreign_key]
    assert len(fks) == 5
    for dim_name in DIMENSION_NAMES:
        assert any(fk.startswith(dim_name) for fk in fks), dim_name


def test_every_table_has_a_single_surrogate_primary_key() -> None:
    for spec in REGISTRY:
        pks = spec.pk_columns
        assert len(pks) == 1, spec.name
        assert pks[0].endswith("_sk"), spec.name


def test_dimensions_have_natural_business_keys() -> None:
    assert FACT_TABLE.column("claim_id") is not None
    assert FACT_TABLE.column("line_number") is not None
    assert FACT_TABLE.column("member_sk") is not None
    assert FACT_TABLE.column("service_date") is not None


def test_all_registry_columns_are_nonempty() -> None:
    for spec in REGISTRY:
        for column in spec.columns:
            assert column.name.strip(), f"{spec.name} has an empty column name"


def test_every_column_has_a_type() -> None:
    for spec in REGISTRY:
        for column in spec.columns:
            assert column.type, f"{spec.name}.{column.name} missing type"


def test_fact_table_supports_reconciliation_measures() -> None:
    for measure in ("billed_amount", "allowed_amount", "paid_amount"):
        assert FACT_TABLE.column(measure) is not None, measure


def test_lookup_table_resolves_aliases() -> None:
    for alias in ("member", "MEM", "claims", "fact", "diagnoses", "dx"):
        spec = lookup_table(alias)
        assert spec.name in {t.name for t in REGISTRY}


def test_lookup_table_rejects_unknown() -> None:
    with pytest.raises(KeyError, match="Unknown pipeline or table"):
        lookup_table("dim_aliens")


def test_lookup_table_is_case_insensitive() -> None:
    assert lookup_table("DIM_MEMBER").name == "dim_member"
    assert lookup_table("Fact_Claim_Line").name == "fact_claim_line"


def test_time_dimension_is_calendar_grained() -> None:
    time_spec = lookup_table("dim_time")
    assert time_spec.column("full_date") is not None
    assert time_spec.column("year") is not None
    assert time_spec.column("is_weekend") is not None


def test_expected_row_counts_are_positive() -> None:
    for spec in REGISTRY:
        assert spec.expected_row_count > 0, spec.name


def test_column_spec_defaults() -> None:
    col = ColumnSpec(name="some_col")
    assert col.nullable is True
    assert col.primary_key is False
    assert col.foreign_key is None
    assert col.allowed_values == ()
    assert col.min_value is None
    assert col.max_value is None


def test_table_spec_column_names() -> None:
    spec = TableSpec(
        name="dim_example",
        kind=TableKind.DIMENSION,
        columns=[ColumnSpec("a"), ColumnSpec("b")],
    )
    assert spec.column_names == ["a", "b"]
    assert spec.column("A") is not None
    assert spec.column("missing") is None


def test_aliases_are_consistent_with_registry() -> None:
    for alias, canonical in NAME_ALIASES.items():
        assert any(s.name == canonical for s in REGISTRY), f"{alias} -> {canonical}"
