"""Tests for GitHub bot."""

from unittest.mock import MagicMock, patch

import pytest

from codefox.bots.github_bot import GitHubBot


def _bot(monkeypatch: pytest.MonkeyPatch) -> GitHubBot:
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("PR_NUMBER", "12")

    with patch("codefox.bots.github_bot.Github"):
        return GitHubBot()


def test_send_creates_issue_comment(monkeypatch: pytest.MonkeyPatch) -> None:
    with patch("codefox.bots.github_bot.Github") as mock_github_class:
        bot = _bot(monkeypatch)
        bot.github = mock_github_class.return_value
        mock_pull = bot.github.get_repo.return_value.get_pull.return_value

        bot.send("hello")

    bot.github.get_repo.assert_called_once_with("owner/repo")
    bot.github.get_repo.return_value.get_pull.assert_called_once_with(12)
    mock_pull.create_issue_comment.assert_called_once_with("hello")


def test_send_rejects_empty_message(monkeypatch: pytest.MonkeyPatch) -> None:
    bot = _bot(monkeypatch)
    bot.github = MagicMock()

    with pytest.raises(ValueError, match="Message must not be empty"):
        bot.send("  \n ")

    bot.github.get_repo.assert_not_called()
