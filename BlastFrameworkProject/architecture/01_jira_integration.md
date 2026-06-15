# SOP 01: JIRA Integration

**Goal:** Reliably fetch JIRA issues and parse them into our schema

---

## Input
- JIRA base URL (from .env: JIRA_URL base domain)
- JIRA email (from .env: JIRA_EMAIL)
- JIRA API token (from .env: JIRA_API_TOKEN)
- Issue key (from user input: e.g., "KAN-1")

## Process

### Step 1: Build Authentication
```
1. Encode email:token as Base64
2. Add header: Authorization: Basic {base64}
3. Content-Type: application/json
```

### Step 2: Fetch Issue via REST API v3
```
GET {base_url}/rest/api/3/issue/{issueKey}
```

### Step 3A: Extract ADF Description (if applicable)
JIRA descriptions use Atlassian Document Format (ADF) — nested JSON. Must extract to plain text.

**`extract_adf_text()` algorithm:**
- Walk all `"text"` nodes → append text content
- `"paragraph"` type → add newlines around content
- `"heading"`, `"listItem"`, `"blockquote"` → add newlines
- `"hardBreak"` → add newline
- `"orderedList"`, `"bulletList"`, `"doc"` → recurse children

### Step 3B: Parse Response
Extract ONLY these fields (per AntiHallucinations.md):
- `key` - Issue identifier
- `fields.summary` - Issue title
- `fields.description` - Detailed description (**ADF extracted to plain text**)
- `fields.issuetype.name` - Type (Story, Task, Bug, Epic, etc.)
- `fields.status.name` - Current status
- `fields.priority.name` - Priority level
- `fields.assignee` - Assigned person (may be null)
- `fields.project.key` - Project identifier

### Step 4: Handle Errors
| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Return parsed issue |
| 401 | Auth failed | Check credentials in .env |
| 403 | Forbidden | Token lacks permissions |
| 404 | Not found | Issue doesn't exist |
| 429 | Rate limited | Wait and retry |

## Output Schema
```json
{
  "jira_issue": {
    "key": "KAN-1",
    "summary": "User Authentication & SSO Integration",
    "description": "As a user... (extracted from ADF format to plain text)",
    "issue_type": "Story",
    "status": "To Do",
    "priority": "High",
    "assignee": null,
    "project_key": "KAN"
  }
}
```

## Rules
- ✅ **Never assume missing fields** - If description is null, pass it as null
- ✅ **All responses must be timestamped**
- ✅ **Always include HTTP status in response**
- ✅ **Timeout: 10 seconds max per request**

---

**Last Updated:** 2026-06-10
