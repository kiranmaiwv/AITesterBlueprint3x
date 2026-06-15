# Task Plan: JIRA Test Strategy Auto-Generator React App

## 🎯 Project Overview
**Objective:** Build a lightweight React app that fetches JIRA issues (e.g., KAN-1) and auto-generates complete test strategy documents using GROQ API.

**Last Updated:** 2026-06-14

## 📋 Phase 1: Blueprint (B) - ✅ COMPLETE
- [x] Define JSON Data Schema (Input/Output shapes) in claude.md
- [x] Document GROQ prompt template for strategy generation
- [x] Document JIRA API integration approach
- [x] Define error handling strategy

## ⚡ Phase 2: Link (L) - ✅ COMPLETE
- [x] Test GROQ API connectivity with sample prompt
- [x] Test JIRA API connectivity and fetch KAN-1 sample data
- [x] Verify .env credentials are loaded correctly
- [x] Create minimal test scripts in tools/

## ⚙️ Phase 3: Architect (A) - ✅ COMPLETE
### Layer 1: Architecture (SOPs)
- [x] 01_jira_integration.md - JIRA fetch procedures
- [x] 02_groq_strategy_generation.md - AI generation flow
- [x] 03_output_validation.md - Format validation rules
- [x] 04_error_recovery.md - Self-annealing procedures

### Layer 2: Navigation (React UI + Flask API)
- [x] App.jsx with state management (settings → preview → generating → result)
- [x] Settings component with env-load button
- [x] IssuePreview with separate fetch/generate flow
- [x] StrategyDisplay with toast notifications + full preview toggle
- [x] Toast notification component
- [x] Flask backend with 6 endpoints (health, env-config, fetch-issue, generate-strategy, generate-full, strategies)

### Layer 3: Tools (Python Backend)
- [x] jira_connector.py - JIRA API client (with ADF extraction)
- [x] groq_strategy_generator.py - GROQ API client (model: openai/gpt-oss-120b)
- [x] validator.py - Strategy validation
- [x] file_manager.py - Save/export strategies
- [x] orchestrator.py - Main coordinator

## ✨ Phase 4: Stylize (S) - ✅ COMPLETE
### Bug Fixes (8 issues resolved)
- [x] Vite proxy rewrite bug (removed `/api` stripping)
- [x] JIRA token parsing bug (split('=', 1) for tokens with `=` chars)
- [x] JIRA ADF description extraction (plain text from Atlassian Document Format)
- [x] Flask on Python 3.14 (upgraded to Flask 3.1.3)
- [x] PORT 5000 conflict with macOS AirPlay (moved to 5050)
- [x] GROQ model name mismatch (changed to openai/gpt-oss-120b)
- [x] Strategy truncation (max_tokens 2000 → 4000)
- [x] JIRA API token expired (user generated new token)

### Missing Features Added (8 features)
- [x] Toast notifications (replaced alert() calls)
- [x] .env auto-load button in Settings
- [x] Direct generate flow (separate fetch vs generate)
- [x] Generation loading state (spinner + disabled button)
- [x] Full strategy preview toggle
- [x] Copy to clipboard with toast
- [x] Download confirmation toast
- [x] AbortController timeout handling

## 🛰️ Phase 5: Trigger (T) - COMPLETE (Dev Environment)
- [x] Flask backend running on port 5050
- [x] React dev server running on port 3000
- [x] Vite proxy configured and working
- [x] JIRA fetch (KAN-1) working end-to-end
- [x] GROQ strategy generation working end-to-end
- [x] Production build verified (97ms, 50 kB gzipped)

### Future Deployment (Optional)
- [ ] Docker containerization
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Production deployment guide
- [ ] Monitoring & alerting

## 📂 Deliverables
- [x] React app (Vite, 3 components + Toast)
- [x] Flask backend (6 API endpoints)
- [x] Python tools (5 modules)
- [x] Architecture docs (4 SOPs)
- [x] Project documentation (README, findings, progress, task_plan)
