CONTENT_RELEVANT_CONTEXT = """
## RELEVANT CONTEXT
*(Use only if needed to trace data flow.
Do not analyze this section by itself.)*

{files_context}
"""

CONTENT_FULL = """# DIFF AUDIT & RECONNAISSANCE

Analyze the behavioral change introduced by the diff.

Before analysis check if any referenced symbols are missing.

If definitions are missing, use the search tool to retrieve them.

---

## DIFF
{diff_text}

---

## Required analysis

1. Tool Usage Log
   List which symbols were searched.

2. Changed Lines
   Provide exact modified lines.

3. Behavioral Mapping

OLD behavior →
NEW behavior →

4. Execution Path Audit

Trace how the change propagates through the system.

5. Breakage Points

Identify edge cases introduced by the change.

---

If required definitions cannot be found after using tools, write:

NEED MORE CONTEXT
"""