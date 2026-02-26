CONTENT_RELEVANT_CONTEXT = """
## RELEVANT CONTEXT
*(Use only if needed to trace data flow.
Do not analyze this section by itself.)*

{files_context}
"""

CONTENT_FULL = """# DIFF AUDIT

**CRITICAL:** Describe only what is in the diff. Use exact names from the diff
(do not invent or misspell, e.g. Ollama not Olla). If something is not in the
diff, say "not in the diff" — do not speculate.

## Task
Detect **behavior change** caused by the modified lines.

## Do NOT
- Explain the codebase or architecture
- Summarize classes
- Invent class/API/file names

If you do not compare **OLD vs NEW** behavior → the answer is **INVALID**.

---

## DIFF
*Git diff with +/- markers. Only these lines changed.*

```
{diff_text}
```

---

## Required reasoning

1. **List the changed lines**
2. For each change:
   - OLD behavior →
   - NEW behavior →
3. **What execution path** now behaves differently?
4. **What can break?**

If there is no behavioral change → say exactly: **NO BEHAVIORAL CHANGE.**

"""
