"""Tests for LocalRAG (kwargs validation and paths, no real embedding)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from codefox.utils.local_rag import LocalRAG


def test_index_dir_uses_default() -> None:
    with patch("codefox.utils.local_rag.TextEmbedding") as _:
        with patch(
            "codefox.utils.local_rag.Helper.get_all_files", return_value=[]
        ):
            with patch("codefox.utils.local_rag.nltk.download"):
                rag = LocalRAG("BAAI/bge-small-en-v1.5", "/tmp")
                rag.kwargs = {"index_dir": LocalRAG.default_index_dir}
    assert rag._index_dir() == Path(LocalRAG.default_index_dir)


def test_index_dir_uses_custom_from_kwargs() -> None:
    with patch("codefox.utils.local_rag.TextEmbedding") as _:
        with patch(
            "codefox.utils.local_rag.Helper.get_all_files", return_value=[]
        ):
            with patch("codefox.utils.local_rag.nltk.download"):
                rag = LocalRAG("BAAI/bge-small-en-v1.5", "/tmp")
                rag.kwargs = {"index_dir": "/custom/rag"}
    assert rag._index_dir() == Path("/custom/rag")


def test_qdrant_path_is_under_index_dir() -> None:
    with patch("codefox.utils.local_rag.TextEmbedding") as _:
        with patch(
            "codefox.utils.local_rag.Helper.get_all_files", return_value=[]
        ):
            with patch("codefox.utils.local_rag.nltk.download"):
                rag = LocalRAG("BAAI/bge-small-en-v1.5", "/tmp")
                rag.kwargs = {"index_dir": "/custom/rag"}
    assert rag._qdrant_path() == Path("/custom/rag") / "qdrant"


def test_get_kwargs_language_not_string_raises() -> None:
    with patch("codefox.utils.local_rag.TextEmbedding") as _:
        with patch(
            "codefox.utils.local_rag.Helper.get_all_files", return_value=[]
        ):
            with patch("codefox.utils.local_rag.nltk.download"):
                rag = LocalRAG("BAAI/bge-small-en-v1.5", "/tmp")
    with pytest.raises(TypeError, match="language"):
        rag._get_kwargs(language=123)  # type: ignore[arg-type]


def test_get_kwargs_rff_k_invalid_raises() -> None:
    with patch("codefox.utils.local_rag.TextEmbedding") as _:
        with patch(
            "codefox.utils.local_rag.Helper.get_all_files", return_value=[]
        ):
            with patch("codefox.utils.local_rag.nltk.download"):
                rag = LocalRAG("BAAI/bge-small-en-v1.5", "/tmp")
    with pytest.raises(ValueError, match="rff_k"):
        rag._get_kwargs(rff_k=0)
    with pytest.raises(ValueError, match="rff_k"):
        rag._get_kwargs(rff_k=-1)


def test_get_kwargs_chunk_overlap_ge_chunk_size_raises() -> None:
    with patch("codefox.utils.local_rag.TextEmbedding") as _:
        with patch(
            "codefox.utils.local_rag.Helper.get_all_files", return_value=[]
        ):
            with patch("codefox.utils.local_rag.nltk.download"):
                rag = LocalRAG("BAAI/bge-small-en-v1.5", "/tmp")
    with pytest.raises(ValueError, match="chunk_overlap"):
        rag._get_kwargs(chunk_size=100, chunk_overlap=100)
    with pytest.raises(ValueError, match="chunk_overlap"):
        rag._get_kwargs(chunk_size=50, chunk_overlap=60)


def test_get_kwargs_defaults() -> None:
    with patch("codefox.utils.local_rag.TextEmbedding") as _:
        with patch(
            "codefox.utils.local_rag.Helper.get_all_files", return_value=[]
        ):
            with patch("codefox.utils.local_rag.nltk.download"):
                rag = LocalRAG("BAAI/bge-small-en-v1.5", "/tmp")
    kw = rag._get_kwargs()
    assert kw["language"] == "english"
    assert kw["rff_k"] == 60
    assert kw["chunk_size"] == 300
    assert kw["chunk_overlap"] == 50
    assert kw["lazy_load"] is False


def test_get_model_tag_returns_list() -> None:
    with patch(
        "codefox.utils.local_rag.TextEmbedding.list_supported_models"
    ) as m:
        m.return_value = [
            {"model": "BAAI/bge-small-en-v1.5"},
            {"model": "other"},
        ]
        tags = LocalRAG.get_model_tag()
    assert isinstance(tags, list)
    assert "BAAI/bge-small-en-v1.5" in tags
    assert "other" in tags
