CONTENT_RELEVANT_CONTEXT = """
## RELEVANT CONTEXT
*(Use only if needed to trace data flow.
Do not analyze this section by itself.)*

{files_context}
"""

CONTENT_FULL = """# DIFF AUDIT & RECONNAISSANCE

**CRITICAL:** You must analyze the behavioral change of the modified lines. 
If the DIFF refers to functions, classes, or variables whose definitions are NOT in the diff, you MUST use the provided tools to fetch them before giving a final verdict.

## Step 0: Context Acquisition (Mandatory)
Before starting the analysis, identify any "blind spots":
- Are there new function calls without definitions?
- Are there modified methods where you don't see the class properties?
- If yes: **STOP and call the search tool.** Do not say "not shown in the diff" until you have attempted a search.

## Task
Detect **behavior change** caused by the modified lines by comparing OLD vs NEW logic.

---

## DIFF
{diff_text}


---

## Required reasoning protocol

1. **Tool Usage Log:** List which symbols you searched for (or explain why no search was needed).
2. **List the changed lines:** Exact line numbers and content.
3. **Behavioral Mapping:**
   - OLD behavior (infer from diff or tool results) →
   - NEW behavior (visible in diff) →
4. **Execution Path Audit:** Trace how data flows through these changes into the rest of the system.
5. **Breakage Points:** Identify specific edge cases where this new logic fails.

If you cannot find the definition even after using tools, only then write: **NEED MORE CONTEXT** and specify what is missing.
"""
