CONTENT_FULL = """
Review this diff for proven, actionable bugs. Consider intended change,
OLD -> NEW behavior, affected data/control flow, and concrete failure paths.
Report only issues introduced by changed lines. Do not guess about unseen code.

DIFF:
{diff_text}
"""

CONTENT_RELEVANT_CONTEXT = """
OPTIONAL PROJECT CONTEXT (use only to understand the diff; do not report
pre-existing issues from this section):
{files_context}
"""
