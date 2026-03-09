import hashlib

from typing import Any, cast

import codefox.prompts.audit_content as audit_content
import codefox.prompts.audit_system as audit_system
from codefox.prompts.template import Template


class PromptTemplate(Template):
    def __init__(
        self, config: dict[str, Any], type_prompt: str = "system"
    ) -> None:
        self.config = config
        self.type_prompt = type_prompt

    def get(self) -> str:
        if self.type_prompt == "system":
            return self._get_system()
        elif self.type_prompt == "content":
            return self._get_content()

        return ""

    def _get_content(self) -> str:
        parts: list[str] = []
        parts.append(
            audit_content.CONTENT_FULL.format(
                diff_text=self.config.get("diff_text", "")
            )
        )

        if "files_context" in self.config:
            parts.append(
                audit_content.CONTENT_RELEVANT_CONTEXT.format(
                    files_context=self.config["files_context"]
                )
            )

        prompt = self._join(parts)
        checksum = hashlib.sha256(prompt.encode()).hexdigest()[:10]

        return f"{prompt}\n\n<!-- prompt:{checksum} -->"

    def _get_system(self) -> str:
        ruler = self._get_config("ruler")
        review = self._get_config("review")
        prompt_cfg = self._get_config("prompt")
        baseline = self._get_config("baseline")

        hard_mode = prompt_cfg.get("hard_mode", False)
        short_mode = prompt_cfg.get("short_mode", False)
        strict_facts = prompt_cfg.get("strict_facts", False)

        parts: list[str] = []

        if prompt_cfg.get("system"):
            parts.append(prompt_cfg["system"])

        else:
            if strict_facts:
                parts.append(audit_system.SYSTEM_STRICT_FACTS)
            if hard_mode:
                parts.append(audit_system.SYSTEM_HARD_MODE)
                parts.append(audit_system.SYSTEM_ANTI_HALLUCINATION)

            parts.append(audit_system.SYSTEM_ROLE)
            parts.append(audit_system.SYSTEM_ANALYSIS_PROTOCOL)

            if ruler.get("security", True):
                parts.append(audit_system.SYSTEM_CORE_PRIORITIES)

            if hard_mode:
                parts.append(audit_system.SYSTEM_BUSINESS_LOGIC_EXECUTION)
                parts.append(audit_system.SYSTEM_REGRESSION_PROOF)

            if ruler.get("performance", True):
                parts.append(
                    audit_system.SYSTEM_REGRESSION_AND_IMPACT_ANALYSIS
                )

            if ruler.get("style", True):
                parts.append(audit_system.SYSTEM_SIGNAL_VS_NOISE_RULE)

            parts.append(audit_system.SYSTEM_EVIDENCE_REQUIREMENT)

            if review.get("diff_only", True):
                parts.append(audit_system.SYSTEM_DIFF_AWARE_RULES)

                if hard_mode:
                    parts.append(audit_system.SYSTEM_DIFF_SIMPLIFIED)

            parts.append(audit_system.SYSTEM_SEVERITY_MODEL)
            parts.append(audit_system.SYSTEM_NO_FAKE_STATISTICS)
            parts.append(audit_system.SYSTEM_CONTEXT_SUFFICIENCY_POLICY)

            if hard_mode:
                parts.append(audit_system.SYSTEM_CONCRETE_LANGUAGE)
                parts.append(audit_system.SYSTEM_OUTPUT_GUARD)
                parts.append(audit_system.SYSTEM_SELF_CHECK)

            parts.append(audit_system.SYSTEM_STRICT_FORMATTING_RULES)
            parts.append(audit_system.SYSTEM_RESPONSE_STRUCTURE)
            parts.append(audit_system.SYSTEM_IF_NO_ISSUES_FOUND)

            if short_mode:
                parts.append(audit_system.SYSTEM_SHORT_MODE)

        if baseline.get("enable"):
            parts.append(audit_system.SYSTEM_BASELINE_MODE)

        review_policy = ""
        if review.get("suggest_fixes"):
            review_policy += f"- Auto-fix: {review.get("suggest_fixes")}\n"
        else:
            review_policy += f"- Auto-fix: DO NOT offer auto-fixes\n"
        
        if review.get("severity"):
            review_policy += f"- Minimum severity: {review.get("severity")}\n"
        
        if review.get("max_issues"):
            review_policy += f"- Max findings: {review.get("max_issues")}\n"
        
        if review.get("diff_only"):
            review_policy += f"- Diff-only mode: {review.get("diff_only")}"

        parts.append(f"""
## REVIEW POLICY
{review_policy}
""")

        parts.append("""
Do not show internal reasoning.
Report only final findings.
""")

        severity = review.get("severity")
        if severity:
            parts.append(f"""
Report only issues with **severity >= {(severity or "").upper()}**
""")

        if review.get("max_issues"):
            parts.append(f"""
Limit the output to the **{review.get("max_issues")}** most critical findings.
""")

        if prompt_cfg.get("extra"):
            parts.append(prompt_cfg["extra"])

        prompt = self._join(parts)
        checksum = hashlib.sha256(prompt.encode()).hexdigest()[:10]

        return f"{prompt}\n\n<!-- prompt:{checksum} -->"

    def _get_config(self, key: str) -> dict[str, Any]:
        if key not in self.config:
            raise ValueError(f"Missing required config field: '{key}'")
        return cast(dict[str, Any], self.config[key])

    def _join(self, parts: list[str]) -> str:
        return "\n\n".join(
            p.strip() for p in parts if p and p.strip()
        )
