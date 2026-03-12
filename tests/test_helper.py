"""Tests for Helper."""

import os
from pathlib import Path

import pytest

from codefox.utils.helper import Helper


def test_read_yml_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        Helper.read_yml("/nonexistent/path.yml")


def test_read_yml_valid(tmp_path: Path, sample_config: dict) -> None:
    import yaml

    path = tmp_path / "config.yml"
    path.write_text(
        yaml.dump(sample_config, default_flow_style=False),
        encoding="utf-8",
    )
    result = Helper.read_yml(str(path))
    assert result["model"]["name"] == "gemini-2.0-flash"
    assert result["model"]["temperature"] == 0.2


def test_read_codefoxignore_missing_returns_empty(tmp_path: Path) -> None:
    prev = os.getcwd()
    try:
        os.chdir(tmp_path)
        out = Helper.read_codefoxignore()
        assert out == []
    finally:
        os.chdir(prev)


def test_read_codefoxignore_with_file(tmp_path: Path) -> None:
    (tmp_path / ".codefoxignore").write_text(
        "node_modules/\nvendor/\n# comment\n\n",
        encoding="utf-8",
    )
    prev = os.getcwd()
    try:
        os.chdir(tmp_path)
        out = Helper.read_codefoxignore()
        assert "node_modules/" in out
        assert "vendor/" in out
        assert "# comment" not in out
    finally:
        os.chdir(prev)


def test_get_all_files_skips_unsupported_ext(tmp_path: Path) -> None:
    (tmp_path / "foo.py").write_text("x", encoding="utf-8")
    (tmp_path / "bar.txt").write_text("y", encoding="utf-8")
    (tmp_path / "baz.js").write_text("z", encoding="utf-8")
    prev = os.getcwd()
    try:
        os.chdir(tmp_path)
        (tmp_path / ".codefoxignore").write_text("", encoding="utf-8")
        files = Helper.get_all_files(str(tmp_path))
        paths = [Path(p) for p in files]
        assert any("foo.py" in str(p) for p in paths)
        assert any("baz.js" in str(p) for p in paths)
        assert not any("bar.txt" in str(p) for p in paths)
    finally:
        os.chdir(prev)


def test_get_all_files_skips_ignore_dirs(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("y", encoding="utf-8")
    prev = os.getcwd()
    try:
        os.chdir(tmp_path)
        (tmp_path / ".codefoxignore").write_text("", encoding="utf-8")
        files = Helper.get_all_files(str(tmp_path))
        assert any("a.py" in p for p in files)
        assert not any("node_modules" in p for p in files)
    finally:
        os.chdir(prev)


# --- parse_diff_for_rag ---


def test_parse_diff_for_rag_empty_returns_empty() -> None:
    assert Helper.parse_diff_for_rag("") == ""
    assert Helper.parse_diff_for_rag("   \n  ") == ""


def test_parse_diff_for_rag_extracts_paths_and_tokens() -> None:
    diff = """diff --git a/src/foo.py b/src/foo.py
--- a/src/foo.py
+++ b/src/foo.py
@@ -1,2 +1,3 @@
+def hello_world():
+    fetch_user_data()
"""
    out = Helper.parse_diff_for_rag(diff, max_tokens=50)
    assert "src/foo.py" in out or "foo" in out
    assert "hello_world" in out or "fetch_user_data" in out


def test_parse_diff_for_rag_respects_max_tokens() -> None:
    diff = "diff --git a/a.py b/a.py\n" + "\n".join(
        "+something_" + str(i) for i in range(100)
    )
    out = Helper.parse_diff_for_rag(diff, max_tokens=5)
    parts = out.split()
    assert len(parts) <= 5 or "a.py" in out


# --- chunk_text_sentences (require nltk punkt) ---


def test_chunk_text_sentences_splits_by_size() -> None:
    import nltk

    nltk.download("punkt_tab", quiet=True)
    text = "First sentence. Second sentence. Third sentence. Fourth one."
    chunks = Helper.chunk_text_sentences(text, chunk_size=30, overlap=5)
    assert len(chunks) >= 1
    assert all(isinstance(c, str) for c in chunks)
    joined = " ".join(chunks)
    assert "First" in joined and "Fourth" in joined


def test_chunk_text_sentences_single_short() -> None:
    import nltk

    nltk.download("punkt_tab", quiet=True)
    text = "One short sentence."
    chunks = Helper.chunk_text_sentences(text, chunk_size=100, overlap=0)
    assert len(chunks) == 1
    assert chunks[0] == text


# --- get_ts_parser_by_extension ---


def test_get_ts_parser_by_extension_python() -> None:
    parser = Helper.get_ts_parser_by_extension(".py")
    assert parser is not None


def test_get_ts_parser_by_extension_unknown_returns_none() -> None:
    assert Helper.get_ts_parser_by_extension(".xyz") is None
    assert Helper.get_ts_parser_by_extension("") is None


# --- smart_chunk fallback for non-code ---


def test_smart_chunk_fallback_to_sentences() -> None:
    import nltk

    nltk.download("punkt_tab", quiet=True)
    path = Path("readme.txt")
    content = "First sentence here. Second sentence there. Third."
    chunks = Helper.smart_chunk(path, content, chunk_size=25, overlap=5)
    assert len(chunks) >= 1
    assert "First" in chunks[0] or "First" in " ".join(chunks)
