"""Tests for Clean command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from codefox.api.gemini import Gemini
from codefox.cli.clean import Clean
from codefox.utils.local_rag import LocalRAG


def test_get_dir_cache_embedding_returns_default() -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with patch("codefox.api.base_api.Helper.read_yml") as m:
            m.return_value = {"model": {"name": "x"}, "review": {}}
            clean = Clean(Gemini, args={"typeCache": "embedding"})
            clean.model = MagicMock()
            clean.model.model_config = {}
    path = clean._get_dir_cache("embedding")
    assert path is not None
    assert "embedding_cache" in str(path)


def test_get_dir_cache_rag_returns_default() -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with patch("codefox.api.base_api.Helper.read_yml") as m:
            m.return_value = {
                "model": {"name": "x"},
                "review": {},
            }
            clean = Clean(Gemini, args={"typeCache": "rag"})
            clean.model = MagicMock()
            clean.model.model_config = {
                "rag_index_dir": LocalRAG.default_index_dir
            }
    path = clean._get_dir_cache("rag")
    assert path is not None
    assert "rag_index" in str(path)


def test_get_dir_cache_unknown_returns_none() -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with patch("codefox.api.base_api.Helper.read_yml") as m:
            m.return_value = {"model": {"name": "x"}, "review": {}}
            clean = Clean(Gemini, args={})
            clean.model = MagicMock()
    assert clean._get_dir_cache("unknown") is None
    assert clean._get_dir_cache("") is None


def test_clean_dir_none_prints_message(capsys: pytest.CaptureFixture) -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with patch("codefox.api.base_api.Helper.read_yml") as m:
            m.return_value = {"model": {"name": "x"}, "review": {}}
            clean = Clean(Gemini, args={})
            clean.model = MagicMock()
    clean._clean_dir(None)
    out = capsys.readouterr().out
    assert "Not found" in out


def test_clean_dir_nonexistent_path_prints_message(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with patch("codefox.api.base_api.Helper.read_yml") as m:
            m.return_value = {"model": {"name": "x"}, "review": {}}
            clean = Clean(Gemini, args={})
            clean.model = MagicMock()
    missing = tmp_path / "missing_dir"
    assert not missing.exists()
    clean._clean_dir(missing)
    out = capsys.readouterr().out
    assert "Not found" in out


def test_clean_dir_dangerous_raises() -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with patch("codefox.api.base_api.Helper.read_yml") as m:
            m.return_value = {"model": {"name": "x"}, "review": {}}
            clean = Clean(Gemini, args={})
            clean.model = MagicMock()
    with pytest.raises(ValueError, match="Refusing to delete"):
        clean._clean_dir(Path("/"))
    with pytest.raises(ValueError, match="Refusing to delete"):
        clean._clean_dir(Path.home())


def test_clean_dir_success_removes_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    with patch("codefox.api.gemini.genai.Client"):
        with patch("codefox.api.base_api.Helper.read_yml") as m:
            m.return_value = {"model": {"name": "x"}, "review": {}}
            clean = Clean(Gemini, args={})
            clean.model = MagicMock()
    to_remove = tmp_path / "cache"
    to_remove.mkdir()
    (to_remove / "file.txt").write_text("x", encoding="utf-8")
    clean._clean_dir(to_remove)
    assert not to_remove.exists()
    out = capsys.readouterr().out
    assert "removed" in out
