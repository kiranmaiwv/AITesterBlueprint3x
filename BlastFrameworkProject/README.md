# JIRA Test Strategy Auto-Generator

A lightweight React app that fetches JIRA issues and auto-generates comprehensive test strategy documents using GROQ AI.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- JIRA account with API token
- GROQ API key (free)

### Installation

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Node dependencies**
   ```bash
   npm install
   ```

3. **Configure credentials**
   ```bash
   cp .env.example .env
   # Edit .env with your JIRA and GROQ credentials
   ```

### Run

**Terminal 1: Backend API**
```bash
python app.py
```

**Terminal 2: Frontend (Vite)**
```bash
npm run dev
```

App will be available at: `http://localhost:3000`

---

## 📋 Project Structure

```
BlastFrameworkProject/
├── architecture/              # Layer 1: SOPs (How-to guides)
│   ├── 01_jira_integration.md
│   ├── 02_groq_strategy_generation.md
│   ├── 03_output_validation.md
│   └── 04_error_recovery.md
├── tools/                     # Layer 3: Python backend scripts
│   ├── jira_connector.py      # JIRA API client
│   ├── groq_strategy_generator.py
│   ├── validator.py
│   ├── file_manager.py
│   └── orchestrator.py        # Main flow coordinator
├── src/                       # Layer 2: React UI (Navigation)
│   ├── App.jsx
│   ├── components/
│   │   ├── Settings.jsx
│   │   ├── IssuePreview.jsx
│   │   └── StrategyDisplay.jsx
│   └── index.css
├── generated_strategies/      # Output location
├── app.py                     # Flask backend
├── package.json
├── vite.config.js
├── claude.md                  # Project constitution
├── task_plan.md               # Phases & checklists
├── findings.md                # Research log
├── progress.md                # Execution log
└── .env                       # Credentials (NOT committed)
```

---

## 🏗️ B.L.A.S.T. Framework Phases

### ✅ Phase 1: Blueprint (Complete)
- Discovery questions answered
- Data schema defined
- Specifications confirmed

### ✅ Phase 2: Link (Complete)
- GROQ API: Verified ✓
- JIRA API: Verified ✓
- Credentials: Validated ✓

### ✅ Phase 3: Architect (Complete)
- Layer 1: Architecture SOPs ✓
- Layer 2: React UI + Flask backend ✓
- Layer 3: Python tools ✓

### ⏳ Phase 4: Stylize (Next)
- UI refinement and testing
- Error message polish
- Mobile responsiveness

### ⏳ Phase 5: Trigger (Pending)
- Production deployment
- CI/CD setup
- Maintenance procedures

---

## 📊 Data Flow

```
User Input (Settings)
    ↓
[Settings Component] → Configure credentials & issue key
    ↓
Fetch JIRA Issue
    ↓
[jira_connector.py] → REST API v3 call
    ↓
JIRA Issue Data
    ↓
Generate Strategy
    ↓
[groq_strategy_generator.py] → GROQ API call
    ↓
Raw Strategy Content
    ↓
Validate Output
    ↓
[validator.py] → Format check, word count, sections
    ↓
Save to File
    ↓
[file_manager.py] → Markdown export
    ↓
Display & Download
    ↓
[StrategyDisplay Component] → Show results to user
```

---

## 🔑 API Endpoints

### Health Check
```
GET /health
```

### Fetch JIRA Issue
```
POST /api/fetch-issue
Body: { issueKey, jiraEmail, jiraToken, jiraUrl }
Response: { success, jira_issue or error }
```

### Generate Strategy
```
POST /api/generate-strategy
Body: { issueKey, jiraIssue, groqKey, saveDir }
Response: { success, strategy_content, metadata }
```

### Full Generation (One Call)
```
POST /api/generate-full
Body: { issueKey, jiraEmail, jiraToken, jiraUrl, groqKey, saveDir }
Response: { success, generation results }
```

### List Saved Strategies
```
GET /api/strategies?saveDir=./generated_strategies
Response: { success, count, strategies[] }
```

---

## 🔒 Security & Anti-Hallucination

- ✅ No credentials in frontend code
- ✅ .env file never committed
- ✅ Only uses JIRA data (no assumptions)
- ✅ Validates all outputs before saving
- ✅ 30-second SLA on all operations

---

## 📚 Architecture Decisions

**Why Vite over Create-React-App?**
- Lightweight (6MB vs 100MB)
- Fast dev server
- Faster builds
- Perfect for "lightweight" requirement

**Why Flask for backend?**
- Simple to understand
- Easy to expand
- Deterministic Python tools
- Clear separation of concerns

**Why Python for tools?**
- Better for data processing
- Easy integration with APIs
- Deterministic vs LLM randomness

---

## 🧪 Testing

### Test Python Tools
```bash
python tools/jira_connector.py KAN-1
python tools/groq_strategy_generator.py
python tools/validator.py
python tools/orchestrator.py KAN-1
```

### Verify Connectivity
```bash
python tools/verify_kan1.py
```

---

## 📝 Next Steps (Phase 4 & 5)

1. **Stylize Phase**: Test UI on mobile, polish error messages
2. **Trigger Phase**: Prepare for deployment (Docker, CI/CD)
3. **Maintenance**: Document runbooks for common issues

---

**Last Updated:** 2026-06-10  
**Status:** Phase 3 Complete ✅
