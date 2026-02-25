import math
import re
from pathlib import Path

from rich.progress import track

from codefox.utils.helper import Helper

from ollama import Client

# TODO: completely remake LocalRAG
class LocalRAG:
    def __init__(
        self,
        embedding_model: str,
        files_path: str,
        ollama_client: Client,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        min_score: float | None = 0.25,
        max_query_chars: int = 2000,
    ):
        self.embedding_model = embedding_model
        self.files_path = files_path
        self.ollama_client = ollama_client
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_score = min_score
        self.max_query_chars = max_query_chars
        self.index: list[dict] = []

    def _chunk_text(self, text: str, size: int | None = None) -> list[str]:
        sz = size or self.chunk_size
        overlap = min(self.chunk_overlap, sz // 2)
        lines = text.splitlines()
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        for line in lines:
            line_len = len(line) + 1
            if current_len + line_len > sz and current:
                chunks.append("\n".join(current))
                overlap_lines: list[str] = []
                overlap_len = 0
                for L in reversed(current):
                    overlap_len += len(L) + 1
                    overlap_lines.insert(0, L)
                    if overlap_len >= overlap:
                        break
                current = overlap_lines
                current_len = overlap_len
            current.append(line)
            current_len += line_len

        if current:
            chunks.append("\n".join(current))
        return [c for c in chunks if c.strip()]

    def _embed(self, texts: list[str]) -> list[list[float]]:
        clean = [t for t in texts if t and t.strip()]
        if not clean:
            return []
        resp = self.ollama_client.embed(
            model=self.embedding_model,
            input=clean,
        )
        return resp.embeddings

    def _cosine(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb + 1e-8)

    def _query_for_embedding(self, query: str) -> str:
        """Shorten and clean query for better embedding (e.g. diff has lots of +/- noise)."""
        if len(query) <= self.max_query_chars:
            return query.strip()
        lines = query.strip().splitlines()
        seen: set[str] = set()
        kept: list[str] = []
        total = 0
        for line in lines:
            if total >= self.max_query_chars:
                break
            stripped = line.strip()
            if not stripped or stripped in seen:
                continue
            if stripped.startswith("+++") or stripped.startswith("---"):
                kept.append(stripped)
                total += len(stripped) + 1
                continue
            clean = re.sub(r"^[+\-]", "", stripped).strip()
            if clean:
                kept.append(stripped)
                total += len(stripped) + 1
        return "\n".join(kept) if kept else query[: self.max_query_chars]

    def build(self) -> None:
        ignored_paths = Helper.read_codefoxignore()
        all_files = Helper.get_all_files(self.files_path)
        valid_files = [
            f
            for f in all_files
            if not any(ignored in f for ignored in ignored_paths)
        ]

        self.index = []
        for file_path in track(valid_files, description="Progress read files..."):
            try:
                content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            chunks = self._chunk_text(content)
            if not chunks:
                continue

            try:
                embeddings = self._embed(chunks)
            except Exception:
                continue

            for chunk, emb in zip(chunks, embeddings):
                self.index.append(
                    {
                        "path": file_path,
                        "text": chunk,
                        "embedding": emb,
                    }
                )

    def search(self, query: str, k: int = 8) -> list[dict]:
        if not self.index:
            return []

        embed_input = self._query_for_embedding(query)
        query_emb = self._embed([embed_input])
        if not query_emb:
            return []
        query_vec = query_emb[0]

        scored = [
            (self._cosine(query_vec, item["embedding"]), item)
            for item in self.index
        ]
        scored.sort(key=lambda x: x[0], reverse=True)

        if self.min_score is not None:
            scored = [(s, item) for s, item in scored if s >= self.min_score]

        return [item for _, item in scored[:k]]
