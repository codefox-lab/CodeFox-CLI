"""Tests for PromptTemplate."""

import pytest

from codefox.prompts.prompt_template import PromptTemplate


@pytest.fixture
def full_config() -> dict:
    return {
        "model": {"name": "test"},
        "review": {
            "severity": "high",
            "max_issues": None,
            "suggest_fixes": True,
            "diff_only": True,
        },
        "baseline": {"enable": True},
        "ruler": {"security": True, "performance": True, "style": True},
        "prompt": {"system": None, "extra": None},
    }


def test_prompt_template_get_contains_role(full_config: dict) -> None:
    t = PromptTemplate(full_config)
    out = t.get()
    assert "CodeFox" in out or "ROLE" in out
    assert "ANALYSIS" in out or "Workflow" in out or "protocol" in out.lower()


def test_prompt_template_get_contains_review_policy(full_config: dict) -> None:
    t = PromptTemplate(full_config)
    out = t.get()
    assert "REVIEW POLICY" in out
    assert "high" in out
    assert "Auto-fix" in out or "suggest_fixes" in str(full_config)


def test_prompt_template_custom_system(full_config: dict) -> None:
    full_config["prompt"]["system"] = "Custom system instruction"
    t = PromptTemplate(full_config)
    out = t.get()
    assert "Custom system instruction" in out


def test_prompt_template_missing_ruler_raises() -> None:
    config = {
        "model": {"name": "x"},
        "review": {},
        "baseline": {},
        "prompt": {},
    }
    t = PromptTemplate(config)
    with pytest.raises(ValueError) as exc_info:
        t.get()
    assert (
        "ruler" in str(exc_info.value).lower()
        or "config" in str(exc_info.value).lower()
    )
