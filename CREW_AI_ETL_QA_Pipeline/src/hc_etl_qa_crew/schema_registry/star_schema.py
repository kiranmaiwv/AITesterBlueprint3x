"""Canonical healthcare star schema used by the whole pipeline.

The star schema is the *unit of work* this tool QA's. Everything downstream —
the demo dataset, the live-data gateway, the agent prompts, the pytest output —
talks in terms of these six tables and their columns.

``claims_etl_v1`` is a runnable, documented example of a healthcare claims
warehouse (a typical payer star schema). It is deliberately ordinary: one
fact table of claim lines and five dimensions (member, provider, diagnosis,
service, time). A real deployment swaps in its own tables by pointing the
gateway at its own warehouse; the contracts in this file stay the same.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class TableKind(StrEnum):
    FACT = "fact"
    DIMENSION = "dimension"


@dataclass(frozen=True)
class ColumnSpec:
    """A column as the agents and the pytest generator see it."""

    name: str
    type: str = ""
    nullable: bool = True
    primary_key: bool = False
    foreign_key: str | None = None
    description: str = ""
    #: Values the business says are impossible; the pytest generator emits
    #: range checks from these (age in 0..120, amount > 0, ...).
    min_value: float | None = None
    max_value: float | None = None
    #: Valid-code hints for the generator's SET / value-list checks.
    allowed_values: tuple[str, ...] = ()
    #: When set, a row is only valid if the column is non-null.
    not_null_when: str = ""


@dataclass(frozen=True)
class TableSpec:
    """One table in the schema registry."""

    name: str
    kind: TableKind
    business_name: str = ""
    description: str = ""
    columns: list[ColumnSpec] = field(default_factory=list)
    expected_row_count: int = 100

    @property
    def pk_columns(self) -> list[str]:
        return [c.name for c in self.columns if c.primary_key]

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def column(self, name: str) -> ColumnSpec | None:
        for col in self.columns:
            if col.name.lower() == name.lower():
                return col
        return None


# --------------------------------------------------------------------------
# The canonical example: claims_etl_v1 (1 fact + 5 dims)
# --------------------------------------------------------------------------

_MEMBER = TableSpec(
    name="dim_member",
    kind=TableKind.DIMENSION,
    business_name="Member",
    description=(
        "One row per insured member. Grain: a member is uniquely identified "
        "by member_sk. member_id is the natural business key from the source "
        "eligibility system."
    ),
    columns=[
        ColumnSpec("member_sk", "INTEGER", primary_key=True, description="Surrogate key"),
        ColumnSpec(
            "member_id", "VARCHAR(20)", nullable=False, description="Natural business key"
        ),
        ColumnSpec("first_name", "VARCHAR(60)", nullable=False),
        ColumnSpec("last_name", "VARCHAR(60)", nullable=False),
        ColumnSpec("date_of_birth", "DATE", nullable=False),
        ColumnSpec("gender", "VARCHAR(10)", nullable=False),
        ColumnSpec("state_code", "VARCHAR(2)", nullable=False),
        ColumnSpec("zip_code", "VARCHAR(5)", nullable=False),
        ColumnSpec("enrollment_start_date", "DATE", nullable=False),
        ColumnSpec("enrollment_end_date", "DATE", nullable=True),
    ],
)


#: How the demo loader and the gateways recognize shorthand names.
#:   "member" / "MEM" / "dim_member" -> dim_member
NAME_ALIASES: dict[str, str] = {
    "member": "dim_member",
    "members": "dim_member",
    "mem": "dim_member",
    "provider": "dim_provider",
    "providers": "dim_provider",
    "prov": "dim_provider",
    "diagnosis": "dim_diagnosis",
    "diagnoses": "dim_diagnosis",
    "dx": "dim_diagnosis",
    "service": "dim_service",
    "services": "dim_service",
    "cpt": "dim_service",
    "time": "dim_time",
    "dates": "dim_time",
    "date": "dim_time",
    "claim_line": "fact_claim_line",
    "claim_lines": "fact_claim_line",
    "claims": "fact_claim_line",
    "fact": "fact_claim_line",
}


_PROVIDER = TableSpec(
    name="dim_provider",
    kind=TableKind.DIMENSION,
    business_name="Provider",
    description=(
        "One row per rendering provider (physician, facility or pharmacy). "
        "npi is the natural business key."
    ),
    columns=[
        ColumnSpec("provider_sk", "INTEGER", primary_key=True, description="Surrogate key"),
        ColumnSpec("npi", "VARCHAR(10)", nullable=False, description="National Provider Id"),
        ColumnSpec("provider_name", "VARCHAR(120)", nullable=False),
        ColumnSpec("provider_type", "VARCHAR(40)", nullable=False),
        ColumnSpec("specialty", "VARCHAR(60)", nullable=False),
        ColumnSpec("state_code", "VARCHAR(2)", nullable=False),
        ColumnSpec("network_status", "VARCHAR(20)", nullable=False),
        ColumnSpec("contract_start_date", "DATE", nullable=True),
        ColumnSpec("contract_end_date", "DATE", nullable=True),
    ],
)


_DIAGNOSIS = TableSpec(
    name="dim_diagnosis",
    kind=TableKind.DIMENSION,
    business_name="Diagnosis",
    description="One row per ICD-10 diagnosis code referenced by claim lines.",
    columns=[
        ColumnSpec("diagnosis_sk", "INTEGER", primary_key=True, description="Surrogate key"),
        ColumnSpec("icd10_code", "VARCHAR(10)", nullable=False),
        ColumnSpec("icd10_description", "VARCHAR(255)", nullable=False),
        ColumnSpec("diagnosis_category", "VARCHAR(60)", nullable=False),
        ColumnSpec("chronic_flag", "VARCHAR(1)", nullable=False),
    ],
)


_SERVICE = TableSpec(
    name="dim_service",
    kind=TableKind.DIMENSION,
    business_name="Service",
    description=(
        "One row per billable service/procedure code (CPT/HCPCS). "
        "revenue_code is nullable because some professional claims do not "
        "carry a revenue code."
    ),
    columns=[
        ColumnSpec("service_sk", "INTEGER", primary_key=True, description="Surrogate key"),
        ColumnSpec("cpt_code", "VARCHAR(10)", nullable=False),
        ColumnSpec("cpt_description", "VARCHAR(255)", nullable=False),
        ColumnSpec("service_category", "VARCHAR(60)", nullable=False),
        ColumnSpec("revenue_code", "VARCHAR(4)", nullable=True),
        ColumnSpec("place_of_service", "VARCHAR(30)", nullable=False),
    ],
)


_TIME = TableSpec(
    name="dim_time",
    kind=TableKind.DIMENSION,
    business_name="Date",
    description="One row per calendar date referenced by claim lines.",
    columns=[
        ColumnSpec("date_sk", "INTEGER", primary_key=True, description="Surrogate key"),
        ColumnSpec("full_date", "DATE", nullable=False),
        ColumnSpec("year", "INTEGER", nullable=False),
        ColumnSpec("month", "INTEGER", nullable=False),
        ColumnSpec("day", "INTEGER", nullable=False),
        ColumnSpec("quarter", "INTEGER", nullable=False),
        ColumnSpec("day_of_week_name", "VARCHAR(10)", nullable=False),
        ColumnSpec("is_weekend", "VARCHAR(1)", nullable=False),
        ColumnSpec("is_holiday", "VARCHAR(1)", nullable=False),
    ],
)


_FACT_CLAIM_LINE = TableSpec(
    name="fact_claim_line",
    kind=TableKind.FACT,
    business_name="Claim Line",
    description=(
        "One row per billed claim line. Grain: one claim may have several "
        "lines (one per service), so (claim_id, line_number) is the natural "
        "business key. paid_amount is the dollar amount the payer actually "
        "paid. A line that is denied is still a fact row with paid_amount=0."
    ),
    columns=[
        ColumnSpec("claim_line_sk", "INTEGER", primary_key=True, description="Surrogate key"),
        ColumnSpec("claim_id", "VARCHAR(20)", nullable=False),
        ColumnSpec("line_number", "INTEGER", nullable=False, min_value=1, max_value=99),
        ColumnSpec(
            "member_sk",
            "INTEGER",
            nullable=False,
            foreign_key="dim_member.member_sk",
        ),
        ColumnSpec(
            "provider_sk",
            "INTEGER",
            nullable=False,
            foreign_key="dim_provider.provider_sk",
        ),
        ColumnSpec(
            "diagnosis_sk",
            "INTEGER",
            nullable=False,
            foreign_key="dim_diagnosis.diagnosis_sk",
        ),
        ColumnSpec(
            "service_sk",
            "INTEGER",
            nullable=False,
            foreign_key="dim_service.service_sk",
        ),
        ColumnSpec(
            "date_sk",
            "INTEGER",
            nullable=False,
            foreign_key="dim_time.date_sk",
        ),
        ColumnSpec("service_date", "DATE", nullable=False),
        ColumnSpec("billed_amount", "NUMERIC(12,2)", nullable=False, min_value=0),
        ColumnSpec(
            "allowed_amount",
            "NUMERIC(12,2)",
            nullable=True,
            min_value=0,
            not_null_when="claim_status in ('PAID', 'PARTIAL')",
        ),
        ColumnSpec("paid_amount", "NUMERIC(12,2)", nullable=False, min_value=0),
        ColumnSpec("claim_status", "VARCHAR(20)", nullable=False),
        ColumnSpec("denial_reason", "VARCHAR(120)", nullable=True),
        ColumnSpec(
            "inserted_at",
            "TIMESTAMP",
            nullable=False,
            description="ETL load timestamp (the pipeline's own bookkeeping)",
        ),
    ],
)


def _expand(*specs: TableSpec) -> list[TableSpec]:
    """Attach shared 'load metadata' columns to every table in the registry."""
    expanded: list[TableSpec] = []
    for spec in specs:
        load_cols = [
            ColumnSpec(
                "etl_batch_id",
                "VARCHAR(40)",
                nullable=False,
                description="ETL batch identifier for this load",
            ),
            ColumnSpec("etl_loaded_at", "TIMESTAMP", nullable=False),
        ]
        expanded.append(
            TableSpec(
                name=spec.name,
                kind=spec.kind,
                business_name=spec.business_name,
                description=spec.description,
                columns=[*spec.columns, *load_cols],
                expected_row_count=100,
            )
        )
    return expanded


REGISTRY: list[TableSpec] = _expand(
    _MEMBER, _PROVIDER, _DIAGNOSIS, _SERVICE, _TIME, _FACT_CLAIM_LINE
)

_FACT_INDEX = next(i for i, t in enumerate(REGISTRY) if t.kind is TableKind.FACT)
FACT_TABLE: TableSpec = REGISTRY[_FACT_INDEX]
DIMENSION_TABLES: list[TableSpec] = [t for t in REGISTRY if t.kind is TableKind.DIMENSION]
FACT_NAME = FACT_TABLE.name
DIMENSION_NAMES = [t.name for t in DIMENSION_TABLES]

#: The registered ETL pipeline this tool QA's. One pipeline backs the whole
#: schema: the fact table plus its five dimensions.
PIPELINE_NAME = "claims_etl_v1"


#: How the demo loader and the gateways recognize shorthand names.
#:   "member" / "MEM" / "dim_member" -> dim_member
NAME_ALIASES: dict[str, str] = {
    "member": "dim_member",
    "members": "dim_member",
    "mem": "dim_member",
    "provider": "dim_provider",
    "providers": "dim_provider",
    "prov": "dim_provider",
    "diagnosis": "dim_diagnosis",
    "diagnoses": "dim_diagnosis",
    "dx": "dim_diagnosis",
    "service": "dim_service",
    "services": "dim_service",
    "cpt": "dim_service",
    "time": "dim_time",
    "dates": "dim_time",
    "date": "dim_time",
    "claim_line": "fact_claim_line",
    "claim_lines": "fact_claim_line",
    "claims": "fact_claim_line",
    "fact": "fact_claim_line",
}


def lookup_table(name: str) -> TableSpec:
    """Resolve a user-typed name (or alias) to a registered TableSpec.

    Raises ``KeyError`` with a helpful message when nothing matches.
    """
    key = (name or "").strip().lower()
    if key in NAME_ALIASES:
        key = NAME_ALIASES[key]
    for spec in REGISTRY:
        if spec.name.lower() == key:
            return spec
    known = ", ".join(sorted(t.name for t in REGISTRY))
    raise KeyError(
        f"Unknown pipeline or table {name!r}. Registered tables: {known}"
    )
