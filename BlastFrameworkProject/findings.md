# Findings & Research Log

## ✅ Verified Facts (Initial)
- **GROQ Model:** openai/gpt-oss-120b is FREE and suitable for test strategy generation
- **TestStrategy.md Format:** Reference template includes sections: Objective, Scope (in/out), Focus Areas, Approach, Deliverables, Team & Schedule, Entry/Exit Criteria, Risks
- **.env Available:** Contains GROQ_KEY, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_URL
- **JIRA Instance:** https://kiranmaiwv.atlassian.net/jira/software/projects/KAN/boards/1
- **Target Issue:** KAN-1

## 🔍 Constraints Identified
1. **Anti-Hallucination:** Per AntiHallucinations.md, must only use JIRA data provided - no assumptions about standard fields
2. **Performance SLA:** 30 seconds maximum for generation
3. **Connectivity:** Must verify both GROQ and JIRA are accessible before proceeding
4. **Data Safety:** .env file should NOT be committed

## ✅ KAN-1 Issue Data (Confirmed 2026-06-14)
- **Key:** KAN-1
- **Summary:** User Authentication & SSO Integration (Qase-style Login)
- **Type:** Feature (Story)
- **Status:** To Do
- **Priority:** Medium
- **Assignee:** Kiranmai W V (kiranmaiwv@gmail.com)
- **Description:** Full ADF format with business goals, functional requirements, and acceptance criteria for a login/SSO feature

## 🔧 Issues Discovered & Fixed

### Issue 1: Vite Proxy Rewrite Bug
**Status:** ✅ FIXED
- **Problem:** Vite proxy config rewrote `/api` prefix, so `/api/fetch-issue` → `/fetch-issue` (Flask route not found)
- **Fix:** Removed `rewrite: (path) => path.replace(/^\/api/, '')` from vite.config.js
- **Result:** Proxy now passes full path to Flask

### Issue 2: JIRA API Token Expired (401)
**Status:** ✅ RESOLVED (User provided new token)
- **Problem:** Original JIRA API token had expired (AUTHENTICATED_FAILED)
- **Fix:** User generated a new token from Atlassian API tokens page
- **Note:** JIRA tokens contain `=` characters — `.env` parsing must use `split('=', 1)` not `split('=')`

### Issue 3: .env Parsing Bug (Token Truncation)
**Status:** ✅ FIXED
- **Problem:** `line.split('=')[1]` split on ALL `=` signs, truncating JIRA token after first `=`
- **Scope:** 21 instances across 8 Python files
- **Fix:** Changed all to `line.split('=', 1)[1]`
- **Files fixed:** jira_connector.py, groq_strategy_generator.py, orchestrator.py, diagnose_jira.py, verify_kan1.py, test_jira_connectivity.py, test_groq_connectivity.py, test_jql_search.py

### Issue 4: JIRA ADF Description Format
**Status:** ✅ FIXED
- **Problem:** JIRA stores descriptions in Atlassian Document Format (ADF) — nested JSON, not plain text
- **Fix:** Added `extract_adf_text()` function to jira_connector.py that recursively walks ADF nodes and extracts plain text
- **Result:** Full description extracted (1879 chars with business goals, requirements, ACs)

### Issue 5: Port 5000 Conflict (macOS AirPlay)
**Status:** ✅ WORKAROUND
- **Problem:** macOS Monterey+ uses port 5000 for AirPlay Receiver (ControlCenter)
- **Fix:** Changed Flask to port 5050, updated Vite proxy config accordingly

### Issue 6: Flask on Python 3.14
**Status:** ✅ FIXED
- **Problem:** Flask 2.x uses `pkgutil.get_loader()` which was removed in Python 3.14
- **Fix:** Upgraded to Flask 3.1.3

### Issue 7: GROQ Model Name Mismatch
**Status:** ✅ FIXED
- **Problem:** Code used `mixtral-8x7b-32768` but user wants `openai/gpt-oss-120b`
- **Fix:** Updated model name in groq_strategy_generator.py

### Issue 8: Strategy Truncation (max_tokens too low)
**Status:** ✅ FIXED
- **Problem:** max_tokens=2000 caused strategy to cut off before Team/Schedule, Entry/Exit Criteria, Risks sections
- **Fix:** Increased to max_tokens=4000

## 📦 Architecture Decisions
- **React Framework:** Vite (lightweight, fast builds — 97ms)
- **Backend:** Flask on port 5050 (avoid AirPlay conflict)
- **State Management:** React local component state (minimal)
- **API Communication:** Fetch API with AbortController for timeouts
- **Toast Notifications:** Custom lightweight Toast component instead of alert()

## 📊 Performance Metrics
- **React Build:** 97ms production build
- **Bundle:** 155.48 kB JS / 10.60 kB CSS / 50.17 kB gzipped
- **GROQ Generation:** ~4.5s for 1100 words (2000 tokens)
- **JIRA Fetch:** <2s
- **Network Timeouts:** 15s (JIRA) / 35s (GROQ)

---
**Last Updated:** 2026-06-14
