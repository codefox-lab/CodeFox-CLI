"""Tests for BaseAPI config validation (via a concrete subclass)."""

from unittest.mock import patch

import pytest

from codefox.api.gemini import Gemini


def test_base_api_requires_model_key() -> None:
    with pytest.raises(ValueError, match="Missing required key 'model'"):
        Gemini(config={"other": 1})


def test_base_api_requires_model_name() -> None:
    with pytest.raises(ValueError, match="name"):
        Gemini(config={"model": {"temperature": 0.2}})


def test_base_api_rejects_empty_model_name() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        Gemini(config={"model": {"name": "   "}})


def test_base_api_accepts_valid_structure(sample_config: dict) -> None:
    """Valid config completes BaseAPI init; Gemini client is mocked."""
    with patch("codefox.api.gemini.genai.Client"):
        try:
            Gemini(config=sample_config)
        except (ValueError, RuntimeError) as e:
            if "Missing required key" in str(e) or "name" in str(e):
                pytest.fail(
                    "Valid config must not raise config validation errors"
                )
            raise


def test_base_api_file_not_found_raises_runtime_error() -> None:
    """When config is None and .codefox.yml missing, RuntimeError is raised."""
    with patch(
        "codefox.api.base_api.Helper.read_yml",
        side_effect=FileNotFoundError(),
    ):
        with pytest.raises(RuntimeError, match="not found"):
            Gemini(config=None)


def test_review_config_defaults() -> None:
    with patch("codefox.api.gemini.genai.Client"):
        g = Gemini(
            config={
                "model": {"name": "gemini-2.0-flash"},
                "review": {},
            }
        )
    assert g.review_config.get("max_issues") is None
    assert g.review_config.get("suggest_fixes") is True
    assert g.review_config.get("diff_only") is False
    assert g.review_config.get("sourceBranch") is None
    assert g.review_config.get("targetBranch") is None
    assert g.review_config.get("tools") is False


def test_temperature_out_of_range_raises() -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with pytest.raises(ValueError, match="Temperature"):
            Gemini(
                config={
                    "model": {"name": "x", "temperature": 1.5},
                    "review": {},
                }
            )
        with pytest.raises(ValueError, match="Temperature"):
            Gemini(
                config={
                    "model": {"name": "x", "temperature": -0.1},
                    "review": {},
                }
            )


def test_timeout_default_and_validation() -> None:
    with patch("codefox.api.gemini.genai.Client"):
        g = Gemini(
            config={
                "model": {"name": "x"},
                "review": {},
            }
        )
    assert g.model_config.get("timeout") == 600

    with patch("codefox.api.gemini.genai.Client"):
        with pytest.raises(ValueError, match="Timeout"):
            Gemini(
                config={
                    "model": {"name": "x", "timeout": -1},
                    "review": {},
                }
            )
        with pytest.raises(ValueError, match="Timeout"):
            Gemini(
                config={
                    "model": {"name": "x", "timeout": 0},
                    "review": {},
                }
            )
