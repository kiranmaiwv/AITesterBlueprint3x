# Deterministic demo fixtures (claims_etl_v1)

These CSVs are **generated**, not hand-maintained. Regenerate them from the
canonical schema registry with:

```bash
python scripts/build_fixtures.py
```

They exist so the demo and the test suite run with **zero network and zero
credentials**.

## Row-count contract

The user-facing contract is *"1 fact table + 5 dimension tables, 100 rows
each"*. The generated CSVs honour that with one documented exception:

| Table | Kind | Rows |
| --- | --- | --- |
| `dim_member` | dimension | 100 |
| `dim_provider` | dimension | 100 |
| `dim_diagnosis` | dimension | 100 |
| `dim_service` | dimension | 100 |
| `dim_time` | dimension | 1096 (a calendar table: 2023-01-01 … 2025-12-31) |
| `fact_claim_line` | fact | 100 |

`dim_time` is a calendar/grain dimension. Truncating it to 100 rows would
break date-key coverage for the 2023–2025 fact rows, so it is generated at its
natural grain. Every *entity* dimension (member, provider, diagnosis, service)
is exactly 100 rows, and the fact table is exactly 100 rows.

## Seeded defects

The demo fact table deliberately contains violations so the generated pytest
suite has something real to catch. A correct ETL QA run surfaces each one:

| Defect | Location |
| --- | --- |
| `fact_claim_line.member_sk` = 1002 with no matching `dim_member` row | FK break |
| `fact_claim_line.provider_sk` = 1005 with no matching `dim_provider` row | FK break |
| `fact_claim_line.date_sk` = 990001 with no matching `dim_time` row | FK break |
| A `claim_status='PAID'` row with `allowed_amount IS NULL` | business-rule break |
| `dim_member.gender` NULL on member_sk 3 | completeness break |
| `dim_provider.network_status` NULL on provider_sk 5 | completeness break |
