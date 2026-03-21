import abc
import dataclasses
from pathlib import Path
from typing import Any, Protocol

from codefox.utils.helper import Helper
from codefox.utils.local_rag import LocalRAG
from codefox.utils.parser import Parser


class ExecuteResponse(Protocol):
    text: str


@dataclasses.dataclass
class Response:
    text: str


class BaseAPI(abc.ABC):
    default_embedding = "BAAI/bge-small-en-v1.5"
    default_max_rag_chars = 4096
    default_max_rag_matching_chunks = 12
    default_max_diff_chars = 16_000

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__()
        try:
            self.config: dict[str, Any] = config or Helper.read_yml(
                ".codefox.yml"
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Configuration file '.codefox.yml' not found. "
                "Please run 'codefox init' first."
            )

        if "model" not in self.config or not self.config.get("model"):
            raise ValueError("Missing required key 'model'")

        self.model_config = self._processing_model_config(self.config["model"])
        self.review_config = self._processing_review_config(
            self.config["review"]
        )

        if "embedding" not in self.model_config or not self.model_config.get(
            "embedding"
        ):
            self.model_config["embedding"] = self.default_embedding

        self.rag: LocalRAG | None = None

        self.max_rag_chars = (
            self.model_config.get("max_rag_chars")
            or self.default_max_rag_chars
        )
        self.max_rag_matching_chunks = (
            self.model_config.get("max_rag_matching_chunks")
            or self.default_max_rag_matching_chunks
        )
        self.max_diff_chars = (
            self.model_config.get("max_diff_chars")
            or self.default_max_diff_chars
        )

    @abc.abstractmethod
    def check_model(self, name: str) -> bool:
        pass

    @abc.abstractmethod
    def execute(self, diff_text: str) -> ExecuteResponse:
        pass

    @abc.abstractmethod
    def check_connection(self) -> tuple[bool, Any]:
        pass

    @abc.abstractmethod
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

        safe_rag_kw = {}
        for k, v in rag_kw.items():
            if k in {"index_dir", "rag_index_dir"}:
                base_dir = (Path.cwd() / ".codefox").resolve()
                target = Path(v).resolve()

                if not target.is_relative_to(base_dir):
                    raise ValueError(f"Invalid RAG index directory: {v}")

                safe_rag_kw[k] = str(target)
            else:
                safe_rag_kw[k] = v

        try:
            self.rag = LocalRAG(
                self.model_config["embedding"],
                files_path=path_files,
                **safe_rag_kw,
            )
            if not self.rag.load_index():
                self.rag.build()
                self.rag.save_index()
            return True, None
        except Exception as e:
            return False, f"LocalRAG error: {str(e)}"

    @abc.abstractmethod
    def remove_files(self) -> None:
        pass

    @abc.abstractmethod
    def get_tag_models(self) -> list[str]:
        return []

    def get_context(self, diff_text: str) -> str:
        if len(diff_text) > self.max_diff_chars:
            diff_text = (
                diff_text[: self.max_diff_chars]
                + "\n\n... [diff truncated for context length]"
            )

        rag_context = ""
        if self.rag:
            rag_context = Parser.get_files_context(
                self.rag,
                diff_text,
                k=self.max_rag_matching_chunks,
                max_rag_chars=self.max_rag_chars,
            )

        return rag_context

    def _processing_review_config(
        self, review_config: dict[str, Any]
    ) -> dict[str, Any]:
        if "max_issues" not in review_config:
            review_config["max_issues"] = None

        if "suggest_fixes" not in review_config:
            review_config["suggest_fixes"] = True

        if "diff_only" not in review_config:
            review_config["diff_only"] = False

        if "sourceBranch" not in review_config:
            review_config["sourceBranch"] = None

        if "targetBranch" not in review_config:
            review_config["targetBranch"] = None

        if "tools" not in review_config:
            review_config["tools"] = False

        review_config["max_tool_iterations"] = review_config.get(
            "max_tool_iterations", 25
        )
        if review_config["max_tool_iterations"] > 100:
            review_config["max_tool_iterations"] = 100

        if review_config["max_tool_iterations"] < 0:
            review_config["max_tool_iterations"] = 0

        return review_config

    def _processing_model_config(
        self, model_config: dict[str, Any]
    ) -> dict[str, Any]:
        if "name" not in model_config or not model_config.get("name"):
            raise ValueError("Key 'model' missing required value key 'name'")

        if not model_config["name"].strip():
            raise ValueError("Model name cannot be empty")

        if "max_tokens" not in model_config or not model_config.get(
            "max_tokens"
        ):
            model_config["max_tokens"] = None

        if "think_mode" not in model_config or not model_config.get(
            "think_mode"
        ):
            model_config["think_mode"] = False

        if "max_completion_tokens" not in model_config or not model_config.get(
            "max_completion_tokens"
        ):
            model_config["max_completion_tokens"] = None

        if "temperature" not in model_config or not model_config.get(
            "temperature"
        ):
            model_config["temperature"] = 0.2

        if model_config["temperature"] > 1 or model_config["temperature"] < 0:
            raise ValueError(
                "Temperature must be between 0 and 1, "
                f"got {model_config['temperature']}"
            )

        timeout = model_config.get("timeout")
        if timeout is None:
            model_config["timeout"] = 600
            timeout = 600
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError(f"Timeout must be positive number, got {timeout}")

        return model_config
