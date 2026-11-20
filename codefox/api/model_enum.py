import enum
from typing import cast

from codefox.api.base_api import BaseAPI
from codefox.api.gemini import Gemini
from codefox.api.llamacpp import LlamaCpp
from codefox.api.ollama import Ollama
from codefox.api.openrouter import OpenRouter


class ModelEnum(enum.Enum):
    GEMINI = Gemini
    LLAMACPP = LlamaCpp
    OPENROUTER = OpenRouter
    OLLAMA = Ollama

    @property
    def api_class(self) -> type[BaseAPI]:
        return cast(type[BaseAPI], self.value)

    @classmethod
    def by_name(cls, name: str) -> "ModelEnum":
        try:
            return cls[name.upper()]
        except KeyError:
            available = [e.name.lower() for e in cls]
            raise ValueError(
                f"Unknown provider '{name}'. Available: {available}"
            ) from None

    @classmethod
    def names(cls) -> list[str]:
        return [e.name.lower() for e in cls]
