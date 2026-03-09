import abc
import dataclasses
from typing import Any, Protocol

from codefox.utils.helper import Helper


class ExecuteResponse(Protocol):
    text: str


@dataclasses.dataclass
class Response:
    text: str


class BaseAPI(abc.ABC):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__()
        try:
            self.config: dict[str, Any] = config or Helper.read_yml(
                ".codefox.yml"
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Configuration file '.codefox.yml' not found. "
                "Please run 'codefox --command init' first."
            )

        if "model" not in self.config or not self.config.get("model"):
            raise ValueError("Missing required key 'model'")

        self.model_config = self._processing_model_config(self.config["model"])
        self.review_config = self._processing_review_config(
            self.config["review"]
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
        pass

    @abc.abstractmethod
    def remove_files(self) -> None:
        pass

    def get_tag_models(self) -> list[str]:
        return []

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
                "got {model_config['temperature']}"
            )

        timeout = model_config.get("timeout")
        if timeout is None:
            model_config["timeout"] = 600
            timeout = 600
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError(f"Timeout must be positive number, got {timeout}")

        return model_config
