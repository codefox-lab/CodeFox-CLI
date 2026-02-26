import os
from typing import Any

from openai import OpenAI

from codefox.api.base_api import BaseAPI, ExecuteResponse, Response
from codefox.prompts.prompt_template import PromptTemplate
from codefox.utils.helper import Helper
from codefox.utils.local_rag import LocalRAG


class OpenRouter(BaseAPI):
    default_model_name = "qwen/qwen3-vl-30b-a3b-thinking"
    default_embedding = "BAAI/bge-small-en-v1.5"
    base_url = "https://openrouter.ai/api/v1"
    default_max_rag_chars = 4096
    default_max_diff_chars = 16_000

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

        self.rag: LocalRAG | None = None
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
        max_rag_chars = (
            self.model_config.get("max_rag_chars")
            or self.default_max_rag_chars
        )
        max_diff_chars = (
            self.model_config.get("max_diff_chars")
            or self.default_max_diff_chars
        )
        if len(diff_text) > max_diff_chars:
            diff_text = (
                diff_text[:max_diff_chars]
                + "\n\n... [diff truncated for context length]"
            )

        rag_context = ""
        if self.rag:
            rag_context = Helper.get_files_context(
                self.rag,
                diff_text,
                k=8,
                max_rag_chars=max_rag_chars,
            )

        system_prompt = PromptTemplate(self.config)
        context_prompt = PromptTemplate(
            {"files_context": rag_context, "diff_text": diff_text}, "content"
        )
        content = context_prompt.get()

        completion = self.client.chat.completions.create(
            model=self.model_config["name"],
            temperature=self.model_config["temperature"],
            timeout=self.model_config.get("timeout", 600),
            max_tokens=self.model_config["max_tokens"],
            max_completion_tokens=self.model_config["max_completion_tokens"],
            messages=[
                {"role": "system", "content": system_prompt.get()},
                {"role": "user", "content": content},
            ],
        )

        raw = completion.choices[0].message.content
        return Response(text=raw if raw is not None else "")

    def remove_files(self) -> None:
        pass

    def upload_files(self, path_files: str) -> tuple[bool, Any]:
        if self.review_config["diff_only"]:
            return True, None

        rag_kw = {
            "max_query_chars": self.model_config.get(
                "rag_max_query_chars", 2000
            ),
        }
        key_map = {
            "rag_min_score": "min_score",
            "rag_chunk_size": "chunk_size",
            "rag_chunk_overlap": "chunk_overlap",
            "rag_embed_batch_size": "embed_batch_size",
            "rag_max_chunks": "max_chunks",
            "rag_max_files": "max_files",
            "rag_threads_embedding": "threads_embedding",
            "rag_lazy_load": "lazy_load",
            "rag_index_dir": "index_dir",
        }
        for config_key, kw_key in key_map.items():
            if config_key in self.model_config:
                rag_kw[kw_key] = self.model_config[config_key]

        self.rag = LocalRAG(
            self.model_config["embedding"],
            files_path=path_files,
            **rag_kw,
        )
        if not self.rag.load_index():
            self.rag.build()
            self.rag.save_index()

        return True, None

    def get_tag_models(self) -> list:
        models = self.client.models.list()
        return [model.id for model in models]
