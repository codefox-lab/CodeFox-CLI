import json
from pathlib import Path

import bm25s
import faiss
import numpy as np
from fastembed import TextEmbedding
from rich.console import Console
from rich.progress import track

from codefox.utils.helper import Helper


class LocalRAG:
    default_cache_dir = ".codefox/embedding_cache/"
    default_index_dir = ".codefox/rag_index/"
    default_language = "english"
    default_rff_k = 60
    default_threads_embedding = None
    default_lazy_load = False
    default_embed_batch_size = 64

    def __init__(self, embedding: str, files_path: str, **kwargs):
        self.console = Console()
        self.console.print("[bold cyan]Initializing LocalRAG...[/bold cyan]")

        self.all_files = Helper.get_all_files(files_path)
        self.kwargs = self._get_kwargs(**kwargs)

        with self.console.status(
            "[blue]Loading TextEmbedding model...[/blue]"
        ):
            self.model = TextEmbedding(
                embedding,
                cache_dir=self.default_cache_dir,
                threads=self.kwargs["threads_embedding"],
                lazy_load=self.kwargs["lazy_load"],
            )
        self.console.print("[green]✓[/green] Model loaded successfully.")

        self.retriever = bm25s.BM25()
        self.files: list[dict] = []
        self.index: faiss.IndexFlatL2 | None = None
        self.chunks: list[str] = []
        self.embedding_name = embedding
        self.files_path = files_path

    def _index_dir(self) -> Path:
        return Path(self.kwargs.get("index_dir", self.default_index_dir))

    def load_index(self) -> bool:
        idx_dir = self._index_dir()
        meta_path = idx_dir / "meta.json"
        faiss_path = idx_dir / "faiss.index"
        chunks_path = idx_dir / "chunks.json"
        files_path = idx_dir / "files.json"
        if (
            not meta_path.exists()
            or not faiss_path.exists()
            or not chunks_path.exists()
            or not files_path.exists()
        ):
            return False
        try:
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            if (
                meta.get("embedding") != self.embedding_name
                or meta.get("files_path") != self.files_path
            ):
                return False
            self.index = faiss.read_index(str(faiss_path))
            with open(chunks_path, encoding="utf-8") as f:
                self.chunks = json.load(f)
            with open(files_path, encoding="utf-8") as f:
                self.files = json.load(f)
            corpus_tokens = bm25s.tokenize(
                self.chunks, stopwords=self.kwargs["language"]
            )
            self.retriever.index(corpus_tokens)
            self.console.print("[green]✓[/green] RAG index loaded from disk.")
            return True
        except Exception:
            return False

    def save_index(self) -> None:
        if self.index is None or not self.chunks or not self.files:
            return
        idx_dir = self._index_dir()
        idx_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(idx_dir / "faiss.index"))
        with open(idx_dir / "chunks.json", "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False)
        with open(idx_dir / "files.json", "w", encoding="utf-8") as f:
            json.dump(self.files, f, ensure_ascii=False)
        with open(idx_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "embedding": self.embedding_name,
                    "files_path": self.files_path,
                },
                f,
                indent=0,
            )
        self.console.print("[green]✓[/green] RAG index saved to disk.")

    def build(self) -> None:
        self.console.print(
            "[bold magenta]Starting RAG database build...[/bold magenta]"
        )
        texts: list[str] = []

        chunk_size = self.kwargs.get("chunk_size", 1000)
        chunk_overlap = self.kwargs.get("chunk_overlap", 200)
        max_chunks = self.kwargs.get("max_chunks")
        max_files = self.kwargs.get("max_files")

        step = chunk_size - chunk_overlap
        if step <= 0:
            step = chunk_size

        files_read = 0
        for file in track(
            self.all_files,
            description="[cyan]Reading & chunking files...[/cyan]",
        ):
            if max_files is not None and files_read >= max_files:
                break
            try:
                path = Path(file)
                content = path.read_text(encoding="utf-8")

                if not content.strip():
                    continue

                files_read += 1
                for i in range(0, len(content), step):
                    if max_chunks is not None and len(texts) >= max_chunks:
                        break
                    chunk_text = content[i : i + chunk_size]
                    texts.append(chunk_text)
                    self.files.append({"path": file, "text": chunk_text})
                if max_chunks is not None and len(texts) >= max_chunks:
                    break
            except Exception:
                continue

        self.console.print(
            f"[green]✓[/green] Created {len(texts)} chunks from "
            f"{files_read} files."
        )

        with self.console.status(
            "[yellow]Tokenizing and building BM25 index...[/yellow]"
        ):
            corpus_tokens = bm25s.tokenize(
                texts, stopwords=self.kwargs["language"]
            )
            self.retriever.index(corpus_tokens)
        self.console.print("[green]✓[/green] BM25 lexical index built.")

        self.chunks = texts
        batch_size = self.kwargs.get(
            "embed_batch_size", self.default_embed_batch_size
        )
        vectors = []

        for i in track(
            range(0, len(texts), batch_size),
            total=(len(texts) + batch_size - 1) // max(batch_size, 1),
            description=(
                "[blue]Generating vector embeddings (batches)...[/blue]"
            ),
        ):
            batch = texts[i : i + batch_size]
            for vec in self.model.embed(batch):
                vectors.append(vec)

        with self.console.status(
            "[magenta]Building FAISS vector index...[/magenta]"
        ):
            vectors_np = np.array(vectors).astype("float32")
            dim = vectors_np.shape[1]
            index = faiss.IndexFlatL2(dim)
            index.add(vectors_np)
            self.index = index

        self.console.print("[green]✓[/green] FAISS semantic index built.")
        self.console.print(
            "[bold green]RAG build complete and ready for "
            "queries![/bold green]\n"
        )

    def search(self, query: str, k: int = 5) -> list[dict]:
        if self.index is None or not self.chunks:
            self.console.print(
                "[bold red]Index is empty. "
                "Please run build() first.[/bold red]"
            )
            return []

        search_k = min(len(self.chunks), max(k * 2, 10))

        if "max_query_chars" in self.kwargs:
            query = query[: self.kwargs["max_query_chars"]]

        with self.console.status(
            "[bold cyan]Analyzing query...[/bold cyan]"
        ) as status:
            status.update("[cyan]Embedding search query...[/cyan]")
            q_vec = list(self.model.embed([query]))[0]
            q_vec = np.array([q_vec]).astype("float32")

            status.update("[cyan]Performing FAISS semantic search...[/cyan]")
            _, dense_ids = self.index.search(q_vec, search_k)

            status.update("[cyan]Performing BM25 lexical search...[/cyan]")
            query_tokens = bm25s.tokenize(
                [query], stopwords=self.kwargs["language"]
            )
            bm25_results, _ = self.retriever.retrieve(query_tokens, k=search_k)
            sparse_ids = bm25_results[0]

            status.update("[cyan]Fusing results with RRF algorithm...[/cyan]")
            rrf_scores: dict[int, float] = {}

            for rank, doc_id in enumerate(dense_ids[0]):
                if doc_id == -1:
                    continue
                doc_id = int(doc_id)
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (
                    self.kwargs["rff_k"] + rank + 1
                )

            for rank, doc_id in enumerate(sparse_ids):
                if isinstance(doc_id, dict):
                    doc_id = doc_id.get("id", rank)
                doc_id = int(doc_id)
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (
                    self.kwargs["rff_k"] + rank + 1
                )

            sorted_docs = sorted(
                rrf_scores.items(), key=lambda x: x[1], reverse=True
            )
            min_score = self.kwargs.get("min_score")
            if min_score is not None:
                sorted_docs = [
                    (doc_id, score)
                    for doc_id, score in sorted_docs
                    if score >= min_score
                ]
            top_ids = [doc_id for doc_id, _ in sorted_docs[:k]]

        self.console.print(
            f"[green]✓ Found top {len(top_ids)} matching chunks.[/green]"
        )
        return [self.files[i] for i in top_ids]

    def _get_kwargs(self, **kwargs):
        kwargs.setdefault("language", self.default_language)
        kwargs.setdefault("rff_k", self.default_rff_k)
        kwargs.setdefault("threads_embedding", self.default_threads_embedding)
        kwargs.setdefault("lazy_load", self.default_lazy_load)

        kwargs.setdefault("chunk_size", 1000)
        kwargs.setdefault("chunk_overlap", 200)
        kwargs.setdefault("embed_batch_size", self.default_embed_batch_size)
        kwargs.setdefault("min_score", None)
        kwargs.setdefault("max_chunks", None)
        kwargs.setdefault("max_files", None)
        kwargs.setdefault("index_dir", self.default_index_dir)

        if not isinstance(kwargs["language"], str):
            raise TypeError(
                "Parameter 'language' must be a string "
                "(e.g., 'english', 'russian')."
            )

        if not isinstance(kwargs["rff_k"], int) or kwargs["rff_k"] <= 0:
            raise ValueError("Parameter 'rff_k' must be a positive integer.")

        if kwargs["threads_embedding"] is not None and not isinstance(
            kwargs["threads_embedding"], int
        ):
            raise TypeError(
                "Parameter 'threads_embedding' must be an integer or None."
            )

        if not isinstance(kwargs["lazy_load"], bool):
            raise TypeError("Parameter 'lazy_load' must be a boolean.")

        if (
            not isinstance(kwargs["chunk_size"], int)
            or kwargs["chunk_size"] <= 0
        ):
            raise ValueError(
                "Parameter 'chunk_size' must be a positive integer."
            )

        if (
            not isinstance(kwargs["chunk_overlap"], int)
            or kwargs["chunk_overlap"] < 0
        ):
            raise ValueError(
                "Parameter 'chunk_overlap' must be a non-negative integer."
            )

        if kwargs["chunk_overlap"] >= kwargs["chunk_size"]:
            raise ValueError(
                "Parameter 'chunk_overlap' must be strictly less than "
                "'chunk_size' to prevent infinite looping."
            )

        if kwargs.get("embed_batch_size") is not None and (
            not isinstance(kwargs["embed_batch_size"], int)
            or kwargs["embed_batch_size"] < 1
        ):
            raise ValueError(
                "Parameter 'embed_batch_size' must be a positive integer."
            )

        if kwargs.get("max_chunks") is not None and (
            not isinstance(kwargs["max_chunks"], int)
            or kwargs["max_chunks"] < 1
        ):
            raise ValueError(
                "Parameter 'max_chunks' must be a positive integer or None."
            )

        if kwargs.get("max_files") is not None and (
            not isinstance(kwargs["max_files"], int) or kwargs["max_files"] < 1
        ):
            raise ValueError(
                "Parameter 'max_files' must be a positive integer or None."
            )

        if kwargs.get("min_score") is not None and not isinstance(
            kwargs["min_score"], (int, float)
        ):
            raise TypeError("Parameter 'min_score' must be a number or None.")

        return kwargs
