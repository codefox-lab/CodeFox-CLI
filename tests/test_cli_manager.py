"""Tests for CLIManager."""

from unittest.mock import patch

import pytest

from codefox.api.model_enum import ModelEnum
from codefox.cli_manager import CLIManager


@patch("codefox.cli_manager.load_dotenv", return_value=True)
def test_get_api_class_returns_gemini_by_default(
    mock_load_dotenv: object,
) -> None:
    with patch("codefox.cli_manager.Helper") as mock_helper:
        mock_helper.read_yml.return_value = {"provider": "gemini"}
        manager = CLIManager(command="scan")
        api_class = manager._get_api_class()
        assert api_class is ModelEnum.GEMINI.api_class


@patch("codefox.cli_manager.load_dotenv", return_value=True)
def test_get_api_class_uses_provider_from_config(
    mock_load_dotenv: object,
) -> None:
    with patch("codefox.cli_manager.Helper") as mock_helper:
        mock_helper.read_yml.return_value = {"provider": "openrouter"}
        manager = CLIManager(command="scan")
        api_class = manager._get_api_class()
        assert api_class is ModelEnum.OPENROUTER.api_class


@patch("codefox.cli_manager.load_dotenv", return_value=True)
def test_get_api_class_default_provider_when_missing(
    mock_load_dotenv: object,
) -> None:
    with patch("codefox.cli_manager.Helper") as mock_helper:
        mock_helper.read_yml.return_value = {}
        manager = CLIManager(command="scan")
        api_class = manager._get_api_class()
        assert api_class is ModelEnum.GEMINI.api_class


def test_run_version_prints_and_exits() -> None:
    manager = CLIManager(command="version", args={})
    manager.run()


def test_run_unknown_command_prints_help() -> None:
    with patch("codefox.cli_manager.load_dotenv", return_value=True):
        with patch("codefox.cli_manager.Helper") as mock_helper:
            mock_helper.read_yml.return_value = {"provider": "gemini"}
            manager = CLIManager(command="unknown_cmd", args={})
            with patch("codefox.cli_manager.print"):
                manager.run()


def test_init_does_not_require_codefoxenv() -> None:
    manager = CLIManager(command="init", args={})
    with patch("codefox.cli_manager.Init") as mock_init:
        mock_init.return_value.execute.return_value = None
        manager.run()
        mock_init.return_value.execute.assert_called_once()


def test_scan_requires_codefoxenv() -> None:
    with patch("codefox.cli_manager.load_dotenv", return_value=False):
        with pytest.raises(FileNotFoundError, match=".codefoxenv"):
            CLIManager(command="scan", args={})
