import math
import os
from typing import Any

from openai import OpenAI
from rich.progress import track

from codefox.api.base_api import BaseAPI, ExecuteResponse, Response
from codefox.prompts.prompt_template import PromptTemplate
from codefox.utils.helper import Helper


class OpenRouter(BaseAPI):
    default_model_name = "qwen/qwen3-vl-30b-a3b-thinking"
    default_embedding = "text-embedding-3-small"
    base_url = "https://openrouter.ai/api/v1"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)

        if "base_url" in self.model_config or self.model_config.get(
            "base_url"
        ):
            self.base_url = self.model_config["base_url"]

        if "embedding" not in self.model_config or not self.model_config.get(
            "embedding"
        ):
            self.model_config["embedding"] = self.default_embedding

        self.files: list[dict[str, Any]] | None = None
        self.index: list[dict[str, Any]] = []
        self.client = OpenAI(
            api_key=os.getenv("CODEFOX_API_KEY"), base_url=self.base_url
        )

    def check_connection(self) -> tuple[bool, Any]:
        try:
            self.client.models.list()
            return True, None
        except Exception as e:
            return False, e

    def check_model(self, name: str) -> bool:
        return name in self.get_tag_models()

    def execute(self, diff_text: str = "") -> ExecuteResponse:
        system_prompt = PromptTemplate(self.config)
        content = (
            "Analyze the following git diff"
            f"and identify potential risks:\n\n{diff_text}"
        )

        files_context = ""
        if not self.review_config["diff_only"]:
            rag_chunks = self._search(diff_text, k=8)

            files_context = "\n\n".join(
                f"<file path='{c['path']}'>\n{c['text']}\n</file>"
                for c in rag_chunks
            )

        completion = self.client.chat.completions.create(
            model=self.model_config["name"],
            temperature=self.model_config["temperature"],
            timeout=self.model_config.get("timeout", 600),
            max_tokens=self.model_config["max_tokens"],
            max_completion_tokens=self.model_config["max_completion_tokens"],
            messages=[
                {"role": "system", "content": system_prompt.get()},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": content},
                        {"type": "text", "text": files_context},
                    ],
                },
            ],
        )

        raw = completion.choices[0].message.content
        return Response(text=raw if raw is not None else "")

    def remove_files(self) -> None:
        pass

    def upload_files(self, path_files: str) -> tuple[bool, Any]:
        if self.review_config["diff_only"]:
            return True, None

        ignored_paths = Helper.read_codefoxignore()

        valid_files = [
            f
            for f in Helper.get_all_files(path_files)
            if not any(ignored in f for ignored in ignored_paths)
        ]

        files: list[dict[str, Any]] = []
        for file in track(valid_files, description="Progress read files..."):
            try:
                with open(file, encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                files.append({"path": file, "content": content})
            except Exception:
                continue

        try:
            self.index = []
            for file_entry in track(
                files, description="Progress files processing..."
            ):
                chunks = self._chunk_text(file_entry["content"])

                if not chunks:
                    continue

                embeddings = self._embed(chunks)

                for chunk, emb in zip(chunks, embeddings):
                    self.index.append(
                        {
                            "path": file_entry["path"],
                            "text": chunk,
                            "embedding": emb,
                        }
                    )

            self.files = files
            return True, None
        except Exception as e:
            return False, e

    def get_tag_models(self) -> list:
        models = self.client.models.list()
        return [model.id for model in models]

    def _chunk_text(self, text: str, size: int = 800) -> list[str]:
        raw_chunks = [text[i : i + size] for i in range(0, len(text), size)]
        return [c for c in raw_chunks if c.strip()]

    def _embed(self, texts: list[str]) -> list[list[float]]:
        clean_texts = [t for t in texts if t and t.strip()]

        if not clean_texts:
            return []

        try:
            resp = self.client.embeddings.create(
                model=self.model_config["embedding"],
                input=clean_texts,
            )
        except ValueError:
            return []

        if not resp.data:
            return []

        return [d.embedding for d in resp.data]

    def _cosine(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb + 1e-8)

    def _search(self, query: str, k: int = 5) -> list[dict]:
        query_emb = self._embed([query])[0]

        scored = [
            (self._cosine(query_emb, item["embedding"]), item)
            for item in self.index
        ]

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:k]]
