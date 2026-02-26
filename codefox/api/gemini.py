import os
from typing import Any

from google import genai
from google.genai import types

from codefox.api.base_api import BaseAPI, ExecuteResponse, Response
from codefox.prompts.prompt_template import PromptTemplate
from codefox.utils.helper import Helper
from codefox.utils.local_rag import LocalRAG


class Gemini(BaseAPI):
    default_model_name = "gemini-2.0-flash"
    default_embedding = "BAAI/bge-small-en-v1.5"
    default_max_rag_chars = 4096
    default_max_diff_chars = 500_000

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        if "embedding" not in self.model_config or not self.model_config.get(
            "embedding"
        ):
            self.model_config["embedding"] = self.default_embedding
        self.rag: LocalRAG | None = None
        self.client = genai.Client(api_key=os.getenv("CODEFOX_API_KEY"))

    def check_model(self, name: str) -> bool:
        return name in self.get_tag_models()

    def check_connection(self) -> tuple[bool, Any]:
        try:
            self.client.models.list()
            return True, None
        except Exception as e:
            return False, e

    def get_tag_models(self) -> list[str]:
        response = self.client.models.list()
        page = response.page or []
        return [
            (model.name or "").replace("models/", "")
            for model in page
            if (
                model.supported_actions
                and "generateContent" in model.supported_actions
            )
        ]

    def upload_files(self, path_files: str) -> tuple[bool, Any]:
        if self.review_config["diff_only"]:
            self.rag = None
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

        try:
            self.rag = LocalRAG(
                self.model_config["embedding"],
                files_path=path_files,
                **rag_kw,
            )
            if not self.rag.load_index():
                self.rag.build()
                self.rag.save_index()
            return True, None
        except Exception as e:
            return False, f"LocalRAG error: {str(e)}"

    def remove_files(self) -> None:
        self.rag = None

    def execute(self, diff_text: str) -> ExecuteResponse:
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

        response = self.client.models.generate_content(
            model=self.model_config["name"],
            contents=content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt.get(),
                temperature=self.model_config["temperature"],
                max_output_tokens=self.model_config["max_tokens"],
            ),
        )
        return Response(text=response.text or "")
