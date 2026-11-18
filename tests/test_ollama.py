"""Tests for Ollama provider connectivity and model listing."""

from unittest.mock import MagicMock, patch

from codefox.api.ollama import Ollama


def test_check_connection_does_not_require_default_model() -> None:
    with patch("codefox.api.base_api.Helper.read_yml") as read_yml:
        read_yml.return_value = {
            "model": {"name": "llama3.1:8b"},
            "review": {},
        }
        with patch("codefox.api.ollama.Client"):
            provider = Ollama()

    response = MagicMock(status_code=200)
    with patch(
        "codefox.api.ollama.requests.get", return_value=response
    ) as get:
        connected, error = provider.check_connection()

    assert connected is True
    assert error is None
    get.assert_called_once()
    response.raise_for_status.assert_called_once()


def test_get_tag_models_returns_empty_list_when_no_models() -> None:
    with patch("codefox.api.base_api.Helper.read_yml") as read_yml:
        read_yml.return_value = {
            "model": {"name": "llama3.1:8b"},
            "review": {},
        }
        with patch("codefox.api.ollama.Client"):
            provider = Ollama()

    response = MagicMock(status_code=200)
    response.json.return_value = {"models": []}
    with patch("codefox.api.ollama.requests.get", return_value=response):
        assert provider.get_tag_models() == []
