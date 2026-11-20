import os
from typing import Any

from openai import OpenAI

from codefox.api.base_api import BaseAPI
from codefox.api.openrouter import OpenRouter


class LlamaCpp(OpenRouter):
    """Provider for llama.cpp's OpenAI-compatible llama-server API."""

    default_model_name = "local-model"
    base_url = "http://localhost:8080/v1"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        BaseAPI.__init__(self, config)
        if self.model_config.get("base_url"):
            self.base_url = self.model_config["base_url"]

        self.client = OpenAI(
            api_key=os.getenv("CODEFOX_API_KEY") or "llama.cpp",
            base_url=self.base_url,
            timeout=self.model_config.get("timeout", 600),
        )
