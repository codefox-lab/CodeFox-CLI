CONTENT_FULL = """
DIFF AUDIT

Diff:
{diff_text}

Tasks:

1. Tool usage (symbols searched)
2. Changed lines
3. Behavior change: OLD → NEW
4. Execution path (propagation)
5. Breakage points (new edge cases)

Missing definitions → use search.

If still missing → NEED MORE CONTEXT
"""

CONTENT_RELEVANT_CONTEXT = """
RELEVANT CONTEXT
(Use only if needed to trace data flow.
Do not analyze this section by itself.)

{files_context}
"""
