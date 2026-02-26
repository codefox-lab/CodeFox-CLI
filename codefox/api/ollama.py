import os
from typing import Any

import requests
from ollama import ChatResponse, Client

from codefox.api.base_api import BaseAPI, ExecuteResponse, Response
from codefox.prompts.prompt_template import PromptTemplate
from codefox.utils.helper import Helper
from codefox.utils.local_rag import LocalRAG


class Ollama(BaseAPI):
    default_model_name = "gemma3:12b"
    default_embedding = "BAAI/bge-small-en-v1.5"
    base_url = "https://ollama.com"
    default_max_rag_chars = 4096
    default_max_diff_chars = 16_000

    def __init__(self, config=None):
        super().__init__(config)

        if self.model_config.get("base_url"):
            self.base_url = self.model_config.get("base_url")

        if "embedding" not in self.model_config or not self.model_config.get(
            "embedding"
        ):
            self.model_config["embedding"] = self.default_embedding

        api_key = os.getenv("CODEFOX_API_KEY")

        headers = None
        if api_key and api_key != "null":
            headers = {
                "Authorization": f"Bearer {api_key}",
            }

        self.rag = None

        self.client = Client(
            host=self.base_url,
            headers=headers,
            timeout=self.model_config.get("timeout", 600),
        )

    def check_model(self, name: str) -> bool:
        return name in self.get_tag_models()

    def check_connection(self) -> tuple[bool, Any]:
        try:
            self.client.show(self.default_model_name)
            return True, None
        except Exception as e:
            return False, e

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
            self.model_config["embedding"], files_path=path_files, **rag_kw
        )
        if not self.rag.load_index():
            self.rag.build()
            self.rag.save_index()

        return True, None

    def remove_files(self):
        pass

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
                self.rag, diff_text, k=12, max_rag_chars=max_rag_chars
            )

        system_prompt = PromptTemplate(self.config)
        context_prompt = PromptTemplate(
            {
                "files_context": rag_context,
                "diff_text": diff_text,
            },
            "content",
        )

        options = {}
        if self.model_config.get("temperature") is not None:
            options["temperature"] = self.model_config["temperature"]
        if self.model_config.get("max_tokens") is not None:
            options["num_predict"] = self.model_config["max_tokens"]

        chat_response: ChatResponse = self.client.chat(
            model=self.model_config["name"],
            messages=[
                {"role": "system", "content": system_prompt.get()},
                {"role": "user", "content": context_prompt.get()},
            ],
            options=options if options else None,
        )

        response = Response(chat_response.message.content or "")
        return response

    def get_tag_models(self) -> list[str]:
        response = requests.get(f"{self.base_url}/api/tags")

        if response.status_code == 200:
            data = response.json()
            return [
                model["name"] for model in data["models"] if model.get("name")
            ]
        else:
            return []
