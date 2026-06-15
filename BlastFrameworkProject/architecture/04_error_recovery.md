# SOP 04: Error Recovery & Self-Annealing

**Goal:** When errors occur, learn from them and improve the system

---

## Error Categories & Recovery

### 1. JIRA Connection Errors
| Error | Cause | Recovery |
|-------|-------|----------|
| 404: Issue not found | Issue key is wrong | User: Check issue key, try again |
| 401: Auth failed | Bad credentials | System: Regenerate .env, test credentials |
| 429: Rate limited | Too many requests | System: Retry after 60s with exponential backoff |
| Timeout | Network issue | System: Retry once, then fail gracefully |

**Action:** Log to `.tmp/jira_errors.log`, alert user

### 2. GROQ Generation Errors
| Error | Cause | Recovery |
|-------|-------|----------|
| 401: Invalid key | Bad GROQ_KEY | System: Test with test_groq_connectivity.py |
| 429: Rate limited | Quota exceeded | System: Retry after 30s |
| 500: Server error | GROQ down | System: Retry 3x with backoff, then fail |
| Timeout (>30s) | Generation too slow | System: Fail and suggest simpler issue |

**Action:** Log to `.tmp/groq_errors.log`, suggest retry

### 3. Validation Errors
| Error | Cause | Recovery |
|-------|-------|----------|
| Output too short | GROQ didn't generate full strategy | System: Log as SOP 02 failure, retry prompt |
| Missing sections | Prompt needs refinement | System: Update SOP 02 prompt template |
| Invalid Markdown | GROQ formatting issue | System: Clean output with regex, validate |

**Action:** Log to `.tmp/validation_errors.log`, allow manual override

---

## Self-Annealing Loop

When an error occurs:
1. **Log**: Write stack trace + context to `.tmp/{error_type}.log`
2. **Analyze**: Identify root cause
3. **Patch**: Update relevant SOP (SOP 01/02/03)
4. **Test**: Re-run with same inputs
5. **Update**: Commit fix to claude.md "Maintenance Log"

---

## Error Message User Experience

### For Users (React UI)
```
✅ Success: "Strategy generated! Ready to download/view."

⚠️ Warning: "Strategy generated but some sections were brief. Click 'Regenerate' for more detail."

❌ Error: "Failed to fetch issue. Check: 1) Issue key is correct, 2) Your .env has valid credentials"

🔄 Retry: Show retry button with exponential backoff (1s, 2s, 4s, 8s)
```

### For Debugging (Developers)
- All errors logged to `.tmp/` with ISO timestamp
- Include: error type, stack trace, inputs, attempted recovery
- Format: JSON for machine parsing + markdown summary for humans

---

## Prevention Measures

1. **Timeouts:** Set max 30s for entire flow
2. **Validation:** Check response format before processing
3. **Credentials:** Verify on app startup via test_connectivity scripts
4. **Rate Limits:** Implement exponential backoff
5. **Monitoring:** Alert if error rate > 5%

---

**Last Updated:** 2026-06-10
