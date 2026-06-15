# CLAUDE.md: Project Constitution & Architecture Map

## 🏛️ Project Identity
**Name:** JIRA Test Strategy Auto-Generator  
**Purpose:** Lightweight React app that auto-generates complete test strategy documents from JIRA issues using GROQ API  
**Owner:** Kiran  
**Start Date:** 2026-06-10  
**Last Updated:** 2026-06-14  
**Current State:** Phase 4 COMPLETE — All 8 bugs fixed, 8 features added, end-to-end verified

---

## 📊 DATA SCHEMA

### INPUT SCHEMA: Configuration
```json
{
  "config": {
    "groq_key": "string (from .env: GROQ_KEY)",
    "jira_email": "string (from .env: JIRA_EMAIL)",
    "jira_api_token": "string (from .env: JIRA_API_TOKEN, may contain = chars)",
    "jira_base_url": "string (from .env: JIRA_URL, full URL or base domain)",
    "jira_issue_key": "string (e.g., 'KAN-1')"
  }
}
```

### INTERMEDIATE: JIRA Issue Data
```json
{
  "jira_issue": {
    "key": "string",
    "summary": "string",
    "description": "string (extracted from ADF format to plain text)",
    "issue_type": "string",
    "status": "string",
    "priority": "string",
    "assignee": "object or null",
    "project_key": "string"
  }
}
```

### OUTPUT SCHEMA: Generated Test Strategy
```json
{
  "test_strategy": {
    "strategy_content": "string (full markdown)",
    "metadata": {
      "model_used": "openai/gpt-oss-120b",
      "generation_time_ms": "number",
      "tokens_used": "number"
    },
    "steps": {
      "groq_generation": {},
      "validation": {},
      "save_markdown": {}
    }
  }
}
```

### Required Strategy Sections
1. Objective (what and why)
2. Scope (in-scope / out-of-scope)
3. Focus Areas (functional, security, performance, usability, compatibility)
4. Approach (techniques, tools, testing types)
5. Deliverables
6. Team & Schedule
7. Entry/Exit Criteria
8. Risks

---

## 🎯 Behavioral Rules (MANDATORY)

### Anti-Hallucination Rules
- **ONLY use data explicitly provided by JIRA API** — no invented fields
- **JIRA descriptions are in ADF format** — must extract plain text via `extract_adf_text()`
- **Fail gracefully** if JIRA data is incomplete
- **Never assume default values** for fields not returned

### Performance & Reliability
- **30-second SLA:** Strategy generation must complete within 30 seconds
- **Network Timeouts:** 15s for JIRA, 35s for GROQ (via AbortController)
- **Error Messages:** User-friendly with specific guidance per error type

### API Constraints
- **GROQ:** Model `openai/gpt-oss-120b`, max_tokens=4000, 30s timeout
- **JIRA:** REST API v3, Basic auth (email + API token), ADF description format
- **Server:** Flask on port 5050 (avoid macOS AirPlay conflict on 5000)

---

## 🏗️ 3-LAYER ARCHITECTURE

### Layer 1: Architecture (SOPs) — `architecture/`
- `01_jira_integration.md` — JIRA API v3, ADF extraction, error codes
- `02_groq_strategy_generation.md` — GROQ prompt template, model config
- `03_output_validation.md` — Format validation rules
- `04_error_recovery.md` — Self-annealing procedures

### Layer 2: Navigation (Decision making)
- **React App** (`src/`): App.jsx + 4 components (Settings, IssuePreview, StrategyDisplay, Toast)
- **Flask API** (`app.py`): 6 endpoints (health, env-config, fetch-issue, generate-strategy, generate-full, strategies)
- **State Flow:** settings → preview → generating → result

### Layer 3: Tools (Python) — `tools/`
- `jira_connector.py` — ADF-aware JIRA client
- `groq_strategy_generator.py` — GROQ client (model: openai/gpt-oss-120b)
- `validator.py` — Word count, sections, markdown, security validation
- `file_manager.py` — Save/export to markdown and JSON
- `orchestrator.py` — Full flow coordinator

---

## ✅ Architectural Invariants

1. **Data flows through known shapes** — All code validates against schema
2. **Connectivity verified before generation** — Phase 2: Link must pass
3. **.env token parsing uses split('=', 1)** — Tokens may contain `=` characters
4. **ADF descriptions extracted to plain text** — JIRA API returns ADF format
5. **All intermediate files go to .tmp/** — Production payload to UI + generated_strategies/
6. **Port 5050** — Port 5000 is reserved by macOS AirPlay Receiver

---

## 🔄 Project States

| Phase | Status | Details |
|-------|--------|---------|
| Phase 1: Blueprint | ✅ COMPLETE | Schema defined, discovery done |
| Phase 2: Link | ✅ COMPLETE | GROQ + JIRA verified |
| Phase 3: Architect | ✅ COMPLETE | All layers built & integrated |
| Phase 4: Stylize | ✅ COMPLETE | 8 bugs fixed, 8 features added |
| Phase 5: Trigger | ✅ DEV READY | Running on localhost:3000 + 5050 |

## 📦 Deliverables

- **Frontend:** React (Vite) — 4 components, Toast system
- **Backend:** Flask — 6 API endpoints
- **Tools:** 5 Python modules
- **Architecture:** 4 SOP markdown files
- **Output:** Generated strategies saved to `generated_strategies/`
