# Healthcare ETL QA Crew

AI-powered ETL QA for healthcare star-schema pipelines. Enter a pipeline name;
get back a schema & transform analysis, a reconciliation & data-quality
strategy, detailed data-quality test cases, runnable pytest + SQL automation,
a traceability matrix, and downloadable artifacts.

The engine is a real four-agent CrewAI pipeline over a deterministic demo
star schema: **one fact table (100 rows) + five dimension tables (100 rows
each)** in a healthcare claims warehouse. Nothing is simulated, and no agent
response is hard-coded.

---

## Verification status

Last verified 2026-09-04 (Python 3.11, this repo):

| Check | Result |
| --- | --- |
| `ruff check .` | clean |
| `pytest` | 140 passed, no network, no LLM cost |
| Full four-agent run | **verified end to end** against `deepseek/deepseek-v4-pro` over the demo fixtures: 6 requirements + 6 DQ rules → 6 reconciliation strategies → 10 test cases → 2 pytest files, 100% requirement coverage, zero warnings (run `RUN-20260904-181941`) |
| Streamlit app | starts and renders (fixture mode needs no credentials) |

Not verified here, and not claimed: the Docker image build and a live
warehouse connection (`DATA_SOURCE_MODE=live`).

### What it took to make the LLM stage work (DeepSeek specifics)

Two DeepSeek behaviors had to be handled before a live run could succeed:

1. **`deepseek-v4-pro` (and `deepseek-v4-flash` on this gateway) are reasoning
   models.** Without an explicit disable they spend the *entire* token budget
   on chain-of-thought and return empty `content`, which CrewAI surfaces as
   "Invalid response from LLM call - None or empty" on every attempt. The fix
   is a provider body flag forwarded through CrewAI's supported
   `additional_params` → OpenAI SDK `extra_body` seam (see
   `LLM_EXTRA_BODY_JSON` below). No CrewAI internals are patched.
2. **Agents answer structured contracts loosely.** They put objects in string
   fields, emit `entity_type="schema_requirement"`, return a bare string where
   a list is required, and invent DQ ids. The Pydantic contracts therefore
   coerce before they validate: scalar string fields stringify any input, list
   fields normalize a bare string into a one-item list, and the enums accept
   synonyms (`happy path` → `happy_path`, `yes` → `Yes`). The reconciliation
   task is also told the *exact* available ids after the analysis stage and
   forbidden from extending them. These behaviours are covered by offline
   tests.

---

## What it does

Manual workflow today:

1. Look at the ETL mapping and the target star schema
2. Understand what the load is supposed to guarantee
3. Decide a reconciliation and data-quality strategy
4. Write data-quality test cases as SQL assertions
5. Decide what to automate
6. Write pytest + SQL tests
7. Build traceability from rule to test to automated test
8. Export and share

This tool does all eight, and keeps the human review points visible instead
of hiding them: everything it is unsure about is labelled rather than smoothed
over.

It does **not** run ETL, write to a warehouse, transition anything, or guess
missing business rules.

---

## The demo star schema: `claims_etl_v1`

The unit of work is a **star-schema pipeline**: one fact table plus its five
dimension tables. The bundled demo is a healthcare claims warehouse:

| Table | Kind | Rows | Grain |
| --- | --- | --- | --- |
| `dim_member` | dimension | 100 | one row per insured member (`member_sk`) |
| `dim_provider` | dimension | 100 | one row per rendering provider (`provider_sk`, natural key `npi`) |
| `dim_diagnosis` | dimension | 100 | one row per ICD-10 diagnosis code (`diagnosis_sk`) |
| `dim_service` | dimension | 100 | one row per CPT/HCPCS service (`service_sk`) |
| `dim_time` | dimension | 1096 | one row per calendar date 2023-01-01 … 2025-12-31 |
| `fact_claim_line` | fact | 100 | one row per billed claim line (`claim_line_sk`) |

The four *entity* dimensions and the fact table are exactly **100 rows each**.
`dim_time` is generated at its natural calendar grain (see
`fixtures/README.md` for why), so it is the one documented exception.

The fact table carries five foreign keys to the dimensions
(`member_sk`, `provider_sk`, `diagnosis_sk`, `service_sk`, `date_sk`) and the
measures a reconciliation suite expects (`billed_amount`, `allowed_amount`,
`paid_amount`) plus `claim_status` / `denial_reason`.

**The demo dataset deliberately contains defects** so the generated pytest
suite has something real to catch:

- a claim line whose `member_sk` has no member row (FK break)
- a claim line whose `provider_sk` has no provider row (FK break)
- a claim line whose `date_sk` has no calendar row (FK break)
- a `PAID` claim line with a NULL `allowed_amount` (business rule)
- a member with NULL `gender` (completeness)
- a provider with NULL `network_status` (completeness)

Everything is deterministic: the fixtures are *generated* from the canonical
schema registry (see `fixtures/README.md`), so the CSV dataset, the SQLite
demo database, the agents' view of the data and the test suite can never
drift apart.

---

## Pipeline

```text
Pipeline name (claims_etl_v1)
   ↓  parse, normalize, deduplicate, validate
Data Gateway  ──  fixture dataset (primary)  →  live warehouse (optional)
   ↓
Agent 1: Schema & Transform Analyst   →  SchemaAnalysis   (REQ-*, DQ-*, TR-*)
   ↓  validate: unique ids, provenance, missing-information honesty
Agent 2: Reconciliation Strategist    →  ReconcilePlan    (REC-*, DQ-*, tolerances)
   ↓  validate: strategies reference real ids
Agent 3: Data-Quality Test Case Writer →  TestCaseSuite   (SQL assertion per case)
   ↓  validate: no duplicate ids, no dangling refs, every DQ rule covered
Agent 4: pytest Coder                  →  PytestBundle     (importable .py tests)
   ↓  validate: no sleep/subprocess, no hard-coded secrets, readiness is honest
Deterministic renderers →  Markdown, CSV, JSON, pytest
   ↓
Streamlit results and downloads
```

The process is **sequential** because each stage depends on the *validated*
output of the one before it. Each pipeline run gets a fresh crew, fresh agents
and fresh tasks, with crew memory off, so nothing leaks between runs.

### Agent responsibilities

| Agent | Owns | Cannot |
| --- | --- | --- |
| **Schema & Transform Analyst** | Requirements (`REQ-*`), measurable data-quality rules (`DQ-*`), transform rules, field profiles, provenance | Invent a rule, column, code, threshold or row count |
| **Reconciliation Strategist** | Row-count / SUM / referential-integrity strategies, quality-rule thresholds | Reference an id the analysis did not produce |
| **Test Case Writer** | SQL-shaped positive/negative/boundary cases traced to real ids | Reference an unknown id, or pad with irrelevant categories |
| **pytest Coder** | Importable pytest modules, per-test traceability, readiness status | Invent connection strings or claim READY while placeholders remain |

Only the Schema Analyst gets the data tool. The other three work from
validated upstream output, so a prompt injected into column metadata cannot
reach the warehouse through them.

---

## Architecture decisions

**Provider choice is application logic, not an LLM decision.** `DataGateway`
decides fixture-vs-live in Python. An agent is never asked which provider to
use, and never learns the credentials.

**The data snapshot is captured before the agents start.** Each table's
columns, row count, sample rows and quality probes are read deterministically
and handed to the agents as a bounded prompt block. Agents never query the
warehouse ad hoc.

**Pydantic objects are the source of truth, never LLM Markdown.** Agents return
structured objects. Every `.md`, `.csv`, `.json` and `.py` artifact is rendered
from those objects by deterministic Python in `services/artifacts.py`.

**Coverage is computed, not claimed.** `services/traceability.py` derives
coverage from the validated objects. No agent is asked how well it covered the
data-quality rules, because an agent has an obvious incentive to answer
"fully".

**Stages hand off validated summaries, not raw text.** CrewAI's `Task.context`
forwards the full raw output of every earlier task. Across four stages that
compounds, and by the pytest stage the prompt carries the entire analysis and
strategy JSON. So each stage receives a compact block rendered from the
*validated* upstream object (`services/handoff.py`), and the raw context is
dropped. This is strictly better than the raw text: it is 40-70% smaller, it
cannot contain anything validation rejected, and it lists exactly the ids the
next stage is allowed to reference. The pytest stage is only sent the cases
marked for automation.

**Structured output degrades gracefully.** Providers disagree about how much
structure they can guarantee, so the pipeline walks a ladder and remembers
where it landed: provider-enforced schema → `json_object` + schema in the
prompt → schema in the prompt, free text. **Enforcement is downgraded;
validation never is** — every rung ends with the same `model_validate` call.
Set `LLM_STRUCTURED_OUTPUT=prompt` to skip rung 1 on a provider you already
know cannot do it.

**One repair attempt, never a loop.** A stage whose output fails schema or
deterministic validation is re-run exactly once with the specific problems
listed. Transient empty completions are retried on a bounded backoff. Both are
capped.

---

## Repository structure

```text
app.py                          Streamlit entry point (presentation only)
src/hc_etl_qa_crew/
├── config.py                   Settings, readiness, secret redaction
├── models.py                   Pydantic contracts between stages
├── exceptions.py               Typed errors
├── schema_registry/            The canonical star schema (1 fact + 5 dims)
├── demo_loader/                Deterministic 100-row dataset + fixture writer
├── data_gateway/               Fixture + live (SQLAlchemy) snapshot providers
├── tools/data_tool.py          Read-only, scope-limited agent tool
├── crew/                       Four agents, tasks, factory, prompts, callbacks
├── prompts/
│   ├── agents.yaml             Agent role/goal/backstory
│   └── tasks.yaml              Task descriptions and expected output
├── services/
│   ├── pipelines.py            Input parsing, path sanitization
│   ├── pipeline.py             Orchestration, stage gates, repair
│   ├── handoff.py              Compact validated stage-to-stage summaries
│   ├── structured.py           Schema-rejection fallback, JSON extraction
│   ├── validation.py           Deterministic post-stage checks
│   ├── traceability.py         Coverage and orphan detection
│   └── artifacts.py            Renderers, manifests, ZIP
└── ui/                         Streamlit state, components, results
fixtures/datasets/              Generated deterministic CSVs (100 rows per table)
tests/                          140 tests, no live warehouse or LLM
scripts/                        Fixture builder + demo smoke test
outputs/                        Generated artifacts (gitignored)
```

---

## Install

Requires Python 3.11–3.13 (CrewAI does not support 3.14).

```bash
cd chapter_14_HC_ETL_QA_Pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # then fill it in
```

## Configure

All configuration is environment based. Nothing secret is ever typed into the
UI, and the sidebar shows only a redacted readiness report.

```dotenv
LLM_MODEL=deepseek/deepseek-v4-pro
LLM_API_KEY=sk-...
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=12000

# Disable DeepSeek's chain-of-thought. Without this the reasoning models
# spend the whole token budget thinking and return empty content.
LLM_EXTRA_BODY_JSON={"thinking":{"type":"disabled"}}

DATA_SOURCE_MODE=fixture     # fixture | live
DATA_URL=                    # SQLAlchemy URL when DATA_SOURCE_MODE=live
```

See `.env.example` for the full list. The verified run used
`deepseek/deepseek-v4-pro` with `LLM_MAX_TOKENS=12000` and
`LLM_EXTRA_BODY_JSON` as above.

`HC_ETL_QA_CREW_SKIP_DOTENV=1` makes the app ignore any `.env` and read the
environment only. Tests and containers use it so local files cannot change
behaviour.

### Demo mode

```dotenv
DEMO_MODE=true
```

Reads the deterministic star schema from `fixtures/datasets` (and the built
`outputs/hc_etl_demo.db`) instead of a warehouse. It is labelled in the sidebar
and on every result, and artifacts record the source as `DEMO_FIXTURE`.
**It is never an automatic fallback for a failed live call** — a failed live
fetch raises, and there is a test that proves it.

### Live warehouse (optional)

```dotenv
DATA_SOURCE_MODE=live
DATA_ENGINE=postgresql        # sqlalchemy dialect
DATA_URL=postgresql+psycopg://user:pass@host:5432/warehouse
```

The gateway introspects the registered tables, verifies every expected column
exists, reads row counts and an 8-row sample, and hands that to the agents.
Read-only by construction: only `SELECT` / introspection statements are ever
issued. A table that is missing a registered column fails loudly rather than
proceeding on partial data.

## Run

There are two ways to run the project. Both use the environment from your
`.env` (see Configure).

### Option 1 - CLI smoke (fastest way to see results)

Runs the full four-agent pipeline over the demo fixtures and prints a live
per-stage report plus a summary. Costs LLM tokens.

```bash
# from the project root
./.venv/bin/python scripts/demo_smoke.py claims_etl_v1
```

A successful run prints something like:

```text
[claims_etl_v1] Data Fetch: COMPLETED Read 6 tables via DEMO_FIXTURE
[claims_etl_v1] Schema & Transform Analyst: COMPLETED
[claims_etl_v1] Reconciliation Strategist: COMPLETED
[claims_etl_v1] Test Case Writer: COMPLETED
[claims_etl_v1] pytest Coder: COMPLETED
[claims_etl_v1] Artifacts: COMPLETED 10 test cases, 100.0% requirement coverage

claims_etl_v1: COMPLETED source=DEMO_FIXTURE
  requirements=6 data_quality_rules=6
  strategies=6 quality_rules=6
  test_cases=10
  pytest_files=2 readiness=NEEDS_CONFIGURATION
  requirement_coverage=100.0% automation=100.0%
artifacts: outputs/RUN-<id>
```

### Option 2 - Streamlit UI (browse and download artifacts)

```bash
# from the project root
./.venv/bin/streamlit run app.py
```

Then open <http://localhost:8501>, type `claims_etl_v1` into the box, and
press **Analyze & Generate QA Pack**. The six stages stream live, and the
finished results render in tabs - Schema Analysis, Reconciliation, Test
Cases, pytest, Traceability, Run Details - with a **Download all artifacts
(ZIP)** button at the top.

### Where the results live

Every run writes into `outputs/RUN-YYYYMMDD-HHMMSS/claims_etl_v1/`:

| File | Contents |
| --- | --- |
| `schema_analysis.md` / `.json` | Requirements (REQ-*) and data-quality rules (DQ-*) |
| `reconciliation_strategy.md` | Reconciliation strategies and quality-rule thresholds |
| `test_cases.md` / `.csv` | The data-quality test cases with SQL templates |
| `pytest/tests/test_claims_etl_v1.py` + `conftest.py` | The generated pytest automation |
| `traceability_matrix.csv` | Rule → test case → automated-test mapping and coverage status |
| `manifest.json` | Counts, coverage percentages, stage timing |

Note: the generated pytest needs an `ETL_TEST_DATABASE_URL` before it can be
executed against a real warehouse; demo mode generates the QA pack against the
fixture dataset.

## Run the generated tests against the demo database

The QA crew *generates* pytest automation; it does not execute it, because
execution needs a warehouse. To see real pass/fail results for the demo, run
the latest generated suite against the deterministic demo SQLite database:

```bash
./.venv/bin/python scripts/run_generated_tests.py
```

The script finds the most recent `outputs/RUN-*`, points
`ETL_TEST_DATABASE_URL` at `outputs/hc_etl_demo.db`, and runs pytest. Generated
suites may target a warehouse dialect (the demo emits PostgreSQL
`information_schema.columns`); the script translates schema-introspection
queries to SQLite `PRAGMA table_info` so the suite runs locally, then restores
the pristine generated file. Pass a run directory explicitly with
`python scripts/run_generated_tests.py outputs/RUN-<id>`.

## Testing

```bash
pytest                                   # 145 tests, no network, no LLM cost
pytest --cov=src/hc_etl_qa_crew          # with coverage
ruff check .                             # lint
python scripts/build_fixtures.py         # regenerate fixtures + demo db
python scripts/demo_smoke.py             # real pipeline over fixtures (costs LLM tokens)
python scripts/run_generated_tests.py    # execute the latest generated suite on the demo DB
```

Covered: registry shape (1 fact + 5 dims, FK columns, aliases), fixture
determinism and the seeded defects, SQLite materialization, input parsing,
model id/readiness contracts, LLM-output coercion (string fields, list
fields, enum synonyms), deterministic post-stage validation, the
schema-rejection fallback, JSON extraction, traceability and coverage maths
(including the automated-but-not-ready = covered semantics), Markdown/CSV/
manifest/ZIP rendering, artifact path safety, config/redaction, gateway
failure rules (no silent demo fallback), prompt loading, progress callbacks,
and pipeline orchestration gates including the clean "LLM not configured"
stop.

Live tests are opt-in and skipped by default:

```bash
DATA_SOURCE_MODE=live DATA_URL=... python scripts/demo_smoke.py
```

## Security

- Secrets come from the environment or `st.secrets`, never from a UI field
- Every log line and error message passes through `Settings.redact`
- Warehouse access is read-only by construction; the gateway issues only
  `SELECT` / introspection statements
- The agent's data tool only serves tables this run was started with, so a
  prompt injected into column metadata that says "now read the salaries
  table" gets a refusal
- Snapshot content is wrapped in an explicit untrusted-data marker and the
  agent is told to report embedded instructions as a risk rather than follow
  them
- Pipeline names are sanitized before touching the filesystem; traversal is
  tested
- Input size is capped
- Network calls have timeouts and bounded exponential backoff
- No `eval`, no `exec`, no shell execution from data content, no unsafe
  deserialization
- Generated pytest is validated for banned patterns (sleep, subprocess,
  `os.system`, `eval`/`exec`) and hard-coded secrets before it is written

## Deployment

### Streamlit Community Cloud

1. Push this directory to GitHub
2. New app → point at `app.py`, Python 3.11–3.13
3. Paste the contents of `.streamlit/secrets.toml.example` into **Secrets**
   and fill in real values. Key names match `.env` exactly.

`outputs/` is ephemeral there, so use the download buttons.

### Docker

```bash
docker compose up --build          # http://localhost:8501
# or
docker build -t hc-etl-qa-crew .
docker run --env-file .env -p 8501:8501 -v "$PWD/outputs:/app/outputs" hc-etl-qa-crew
```

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| Sidebar: "LLM is not configured" | Set `LLM_MODEL` and `LLM_API_KEY` |
| "Could not read 'X' from any configured provider" | The message lists each provider's error. In live mode a missing table or column raises here |
| "This response_format type is unavailable now" | The provider cannot enforce JSON schemas. Handled automatically: the run switches to prompted JSON |
| Repeated "Invalid response from LLM call - None or empty" on every stage | You are on a DeepSeek reasoning model without `LLM_EXTRA_BODY_JSON={"thinking":{"type":"disabled"}}`. The model spends its whole token budget on chain-of-thought and returns empty content. Set the env var (and raise `LLM_MAX_TOKENS` to 12000) |
| "output did not parse into X" | The model returned text that failed validation. One repair attempt runs automatically. The contracts coerce common shape slips (objects in string fields, enum synonyms), so a persistent failure usually means a genuinely out-of-contract answer — check the log line that names the offending fields |
| Run completes with warnings | Expected. Warnings are coverage gaps and missing information, listed per pipeline |
| Run is slow | Four sequential LLM calls per run. Latency is the provider's, not the app's |

## Limitations

- **Requires real credentials to be useful.** Demo mode proves the pipeline;
  it does not read your warehouse.
- **Generated pytest is usually `NEEDS_CONFIGURATION`.** The demo dataset does
  not contain connection strings, so the coder emits clean scaffolds with
  clearly marked placeholders and says what it needs. That is the honest
  outcome, not a defect.
- **Artifact quality tracks schema quality.** A pipeline with no documented
  business rules produces an analysis that says so, not invented rules.
- **One registered pipeline.** The registry ships a single canonical pipeline
  (`claims_etl_v1`). Point `DATA_SOURCE_MODE=live` at your own warehouse to
  apply the same contracts to a real schema.
- **Runs are sequential**, so a large batch takes a while. Expect roughly
  3-6 minutes per pipeline on DeepSeek.
- **`outputs/` is local disk.** On Streamlit Community Cloud it does not
  persist; download the ZIP.
