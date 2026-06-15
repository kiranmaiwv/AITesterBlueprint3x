# SOP 02: GROQ Strategy Generation

**Goal:** Use GROQ API to generate a comprehensive test strategy from JIRA issue data

---

## Input
- GROQ API key (from .env: GROQ_KEY)
- JIRA issue data (from SOP 01)

## Process

### Step 1: Build GROQ Prompt
```
System Prompt:
"You are a QA test strategy expert. Generate comprehensive test strategies for software features."

User Prompt Template:
"""
Generate a complete Test Strategy document for this feature:

Issue Key: {issue.key}
Issue Title: {issue.summary}
Description: {issue.description}
Issue Type: {issue.issue_type}

Follow this EXACT structure:
1. Objective - What are we testing and why?
2. Scope (In Scope / Out of Scope) - What's included and excluded?
3. Focus Areas - Which aspects need testing? (Functional, Security, Performance, Usability, Compatibility)
4. Approach - What techniques and tools will we use?
5. Deliverables - What outputs will we produce?
6. Team & Schedule - Who and how long?
7. Entry/Exit Criteria - When do we start and finish?
8. Risks - What could go wrong?

Make the strategy ~1500 words, formal tone, matching the TestStrategy.md template format exactly.
"""

Model: openai/gpt-oss-120b (FREE)
Temperature: 0.7 (for balanced creativity + consistency)
Max Tokens: 2000
```

### Step 2: Call GROQ API
```
POST https://api.groq.com/openai/v1/chat/completions
Headers:
  Authorization: Bearer {GROQ_KEY}
  Content-Type: application/json

Body:
{
  "model": "openai/gpt-oss-120b",
  "messages": [
    {"role": "system", "content": "{system_prompt}"},
    {"role": "user", "content": "{user_prompt}"}
  ],
  "temperature": 0.7,
  "max_tokens": 4000
}
```

### Step 3: Parse Response
```json
Extract: response.choices[0].message.content
```

### Step 4: Handle Errors
| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Extract content |
| 401 | Invalid key | Check GROQ_KEY in .env |
| 429 | Rate limited | Retry after 60s |
| 500 | Server error | Retry with exponential backoff |

## Output Schema
```json
{
  "strategy_content": "# Test Strategy for User Authentication...",
  "model_used": "openai/gpt-oss-120b",
  "tokens_used": 1450,
  "generation_time_ms": 3200,
  "source_issue": "KAN-1"
}
```

## Rules
- ✅ **Timeout: 30 seconds max** (SLA requirement)
- ✅ **Retry once on 429** (rate limit)
- ✅ **Never modify GROQ response** - pass raw content
- ✅ **Include generation metadata** for audit trail
- ✅ **Log all API calls** to .tmp/ for debugging

---

**Last Updated:** 2026-06-10
