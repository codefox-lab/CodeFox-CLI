import faiss
import bm25s
import numpy as np

from pathlib import Path
from fastembed import TextEmbedding
from rich.console import Console
from rich.progress import track

from codefox.utils.helper import Helper


class LocalRAG:
    default_cache_dir = ".codefox/embedding_cache/"
    default_language = "english"
    default_rff_k = 60
    default_threads_embedding = None
    default_lazy_load = False

    def __init__(self, embedding: str, files_path: str, **kwargs):
        self.console = Console()
        self.console.print("[bold cyan]Initializing LocalRAG...[/bold cyan]")
        
        self.all_files = Helper.get_all_files(files_path)
        self.kwargs = self._get_kwargs(**kwargs)

        with self.console.status("[blue]Loading TextEmbedding model...[/blue]"):
            self.model = TextEmbedding(
                embedding,
                cache_dir=self.default_cache_dir,
                threads=self.kwargs["threads_embedding"],
                lazy_load=self.kwargs["lazy_load"]
            )
        self.console.print("[green]✓[/green] Model loaded successfully.")

        self.retriever = bm25s.BM25()
        self.files = []
        self.index: faiss.IndexFlatL2 | None = None
        self.chunks: list[str] = []

    def build(self) -> None:
        self.console.print("[bold magenta]Starting RAG database build...[/bold magenta]")
        texts = []

        chunk_size = self.kwargs.get("chunk_size", 1000)
        chunk_overlap = self.kwargs.get("chunk_overlap", 200)

        step = chunk_size - chunk_overlap
        if step <= 0:
            step = chunk_size

        for file in track(self.all_files, description="[cyan]Reading & chunking files...[/cyan]"):
            try:
                path = Path(file)
                content = path.read_text(encoding="utf-8")

                if not content.strip():
                    continue

                for i in range(0, len(content), step):
                    chunk_text = content[i : i + chunk_size]
                    
                    texts.append(chunk_text)
                    self.files.append({
                        "path": file, 
                        "text": chunk_text
                    })
            except Exception:
                continue
                
        self.console.print(f"[green]✓[/green] Created {len(texts)} chunks from {len(self.all_files)} files.")

        with self.console.status("[yellow]Tokenizing and building BM25 index...[/yellow]"):
            corpus_tokens = bm25s.tokenize(texts, stopwords=self.kwargs["language"])
            self.retriever.index(corpus_tokens)
        self.console.print("[green]✓[/green] BM25 lexical index built.")

        self.chunks = texts
        vectors = []
        
        for vec in track(
            self.model.embed(texts), 
            total=len(texts), 
            description="[blue]Generating vector embeddings...[/blue]"
        ):
            vectors.append(vec)

        with self.console.status("[magenta]Building FAISS vector index...[/magenta]"):
            vectors_np = np.array(vectors).astype("float32")
            dim = vectors_np.shape[1]
            index = faiss.IndexFlatL2(dim)
            index.add(vectors_np)
            self.index = index
            
        self.console.print("[green]✓[/green] FAISS semantic index built.")
        self.console.print("[bold green]RAG build complete and ready for queries![/bold green]\n")

    def search(self, query: str, k: int = 5) -> list[dict]:
        if self.index is None or not self.chunks:
            self.console.print("[bold red]Index is empty. Please run build() first.[/bold red]")
            return []

        search_k = min(len(self.chunks), max(k * 2, 10))

        if "max_query_chars" in self.kwargs:
            query = query[:self.kwargs["max_query_chars"]]

        with self.console.status("[bold cyan]Analyzing query...[/bold cyan]") as status:
            
            status.update("[cyan]Embedding search query...[/cyan]")
            q_vec = list(self.model.embed([query]))[0]
            q_vec = np.array([q_vec]).astype("float32")
            
            status.update("[cyan]Performing FAISS semantic search...[/cyan]")
            _, dense_ids = self.index.search(q_vec, search_k)

            status.update("[cyan]Performing BM25 lexical search...[/cyan]")
            query_tokens = bm25s.tokenize([query], stopwords=self.kwargs["language"])
            bm25_results, _ = self.retriever.retrieve(query_tokens, k=search_k)
            sparse_ids = bm25_results[0]

            status.update("[cyan]Fusing results with RRF algorithm...[/cyan]")
            rrf_scores = {}

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
            top_ids = [doc_id for doc_id, _ in sorted_docs[:k]]

        self.console.print(f"[green]✓ Found top {len(top_ids)} matching chunks.[/green]")
        return [self.files[i] for i in top_ids]

    def _get_kwargs(self, **kwargs):
        kwargs.setdefault("language", self.default_language)
        kwargs.setdefault("rff_k", self.default_rff_k)
        kwargs.setdefault("threads_embedding", self.default_threads_embedding)
        kwargs.setdefault("lazy_load", self.default_lazy_load)
        
        kwargs.setdefault("chunk_size", 1000)
        kwargs.setdefault("chunk_overlap", 200)

        if not isinstance(kwargs["language"], str):
            raise TypeError("Parameter 'language' must be a string (e.g., 'english', 'russian').")

        if not isinstance(kwargs["rff_k"], int) or kwargs["rff_k"] <= 0:
            raise ValueError("Parameter 'rff_k' must be a positive integer.")

        if kwargs["threads_embedding"] is not None and not isinstance(kwargs["threads_embedding"], int):
            raise TypeError("Parameter 'threads_embedding' must be an integer or None.")

        if not isinstance(kwargs["lazy_load"], bool):
            raise TypeError("Parameter 'lazy_load' must be a boolean.")

        if not isinstance(kwargs["chunk_size"], int) or kwargs["chunk_size"] <= 0:
            raise ValueError("Parameter 'chunk_size' must be a positive integer.")
            
        if not isinstance(kwargs["chunk_overlap"], int) or kwargs["chunk_overlap"] < 0:
            raise ValueError("Parameter 'chunk_overlap' must be a non-negative integer.")
            
        if kwargs["chunk_overlap"] >= kwargs["chunk_size"]:
            raise ValueError("Parameter 'chunk_overlap' must be strictly less than 'chunk_size' to prevent infinite looping.")

        return kwargs