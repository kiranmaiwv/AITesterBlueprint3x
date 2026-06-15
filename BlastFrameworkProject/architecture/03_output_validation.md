# SOP 03: Output Validation & Formatting

**Goal:** Ensure generated strategies match expected format and can be saved/exported

---

## Validation Checklist

### Format Validation
```
✓ Output is valid Markdown
✓ Contains all 8 sections (Objective, Scope, Focus Areas, etc.)
✓ Length is 1000-2000 words (per spec)
✓ No HTML/code injection attempts
✓ Headings use proper # hierarchy
```

### Content Validation
```
✓ Objective section describes WHAT and WHY
✓ Scope has both "In Scope" and "Out of Scope" lists
✓ Focus Areas includes: Functional, Security, Performance, Usability, Compatibility
✓ Approach specifies testing techniques and tools
✓ Deliverables lists concrete outputs
✓ Entry/Exit Criteria are measurable
✓ Risks section identifies potential blockers
✓ Team & Schedule include realistic estimates
```

### No-Go Criteria (Fail Validation If)
- ❌ GROQ response is empty or null
- ❌ Response doesn't include at least 6 of 8 sections
- ❌ Contains references to the JIRA issue JSON (should be converted to prose)
- ❌ Length < 800 words or > 3000 words

## Error Handling
If validation fails:
1. Log the failure reason to .tmp/validation_error.json
2. Return user-friendly error message
3. Suggest: "Retry generation" or "Check JIRA issue data"

## Output Metadata
```json
{
  "metadata": {
    "generated_from": "KAN-1",
    "generated_at": "2026-06-10T12:34:56Z",
    "generator_version": "1.0.0",
    "status": "VALID" or "INVALID",
    "validation_errors": []
  },
  "strategy_content": "# Test Strategy...",
  "raw_markdown": "...",
  "word_count": 1450
}
```

## Export Formats
1. **Markdown File (.md)** - Default
2. **JSON** - For programmatic access
3. **HTML** - For display in browser

---

**Last Updated:** 2026-06-10
