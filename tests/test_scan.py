"""Tests for Scan command."""

from unittest.mock import MagicMock, patch

from codefox.api.gemini import Gemini
from codefox.cli.scan import Scan
from codefox.utils.helper import GitBranchNotFoundError, GitRepositoryError


def test_get_branchs_from_args() -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with patch("codefox.api.base_api.Helper.read_yml") as m:
            m.return_value = {
                "model": {"name": "gemini-2.0-flash"},
                "review": {},
            }
            scan = Scan(
                Gemini,
                args={
                    "sourceBranch": "feature",
                    "targetBranch": "main",
                },
            )
            scan.model = MagicMock()
            scan.model.review_config = {
                "sourceBranch": None,
                "targetBranch": None,
            }
    src, tgt = scan._get_branchs()
    assert src == "feature"
    assert tgt == "main"


def test_execute_reports_missing_git_repository() -> None:
    scan = Scan.__new__(Scan)
    scan.args = {}
    scan.model = MagicMock()
    scan.model.review_config = {"sourceBranch": None, "targetBranch": None}
    with patch("codefox.cli.scan.Helper.get_diff") as get_diff:
        get_diff.side_effect = GitRepositoryError("not a Git repository")
        with patch("codefox.cli.scan.print") as output:
            Scan.execute(scan)
    output.assert_called_once()
    assert "not a Git repository" in output.call_args.args[0]


def test_execute_reports_missing_branch() -> None:
    scan = Scan.__new__(Scan)
    scan.args = {}
    scan.model = MagicMock()
    scan.model.review_config = {"sourceBranch": None, "targetBranch": None}
    with patch("codefox.cli.scan.Helper.get_diff") as get_diff:
        get_diff.side_effect = GitBranchNotFoundError(
            "Branch 'missing' does not exist"
        )
        with patch("codefox.cli.scan.print") as output:
            Scan.execute(scan)
    assert "missing" in output.call_args.args[0]


def test_get_branchs_from_config_when_args_empty() -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with patch("codefox.api.base_api.Helper.read_yml") as m:
            m.return_value = {
                "model": {"name": "gemini-2.0-flash"},
                "review": {
                    "sourceBranch": "dev",
                    "targetBranch": "main",
                },
            }
            scan = Scan(Gemini, args={})
            scan.model = MagicMock()
            scan.model.review_config = {
                "sourceBranch": "dev",
                "targetBranch": "main",
            }
    src, tgt = scan._get_branchs()
    assert src == "dev"
    assert tgt == "main"


def test_get_branchs_prefers_args_over_config() -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with patch("codefox.api.base_api.Helper.read_yml") as m:
            m.return_value = {
                "model": {"name": "gemini-2.0-flash"},
                "review": {"sourceBranch": "dev", "targetBranch": "main"},
            }
            scan = Scan(
                Gemini,
                args={
                    "sourceBranch": "feat",
                    "targetBranch": "master",
                },
            )
            scan.model = MagicMock()
            scan.model.review_config = {
                "sourceBranch": "dev",
                "targetBranch": "main",
            }
    src, tgt = scan._get_branchs()
    assert src == "feat"
    assert tgt == "master"
