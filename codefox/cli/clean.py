import shutil
from pathlib import Path
from typing import Any

from codefox.api.base_api import BaseAPI
from codefox.cli.base_cli import BaseCLI
from codefox.utils.local_rag import LocalRAG


class Clean(BaseCLI):
    def __init__(
        self, model: type[BaseAPI], args: dict[str, Any] | None = None
    ):
        self.model = model()
        self.args = args

    def execute(self) -> None:
        args = self.args or {}
        type_cache = args.get("typeCache")
        if type_cache != "all":
            path = self._get_dir_cache(
                type_cache if type_cache is not None else "rag"
            )
            self._clean_dir(path)
            return

        if type_cache == "all":
            for cache_type in ("rag", "embedding"):
                path = self._get_dir_cache(cache_type)
                self._clean_dir(path)
            return

        print("Argument invalid. Use next params: all, rag, embedding'")

    def _clean_dir(self, path: Path | None) -> None:
        if not path or not path.exists():
            print("Not found cache dir")
            return

        if not path.is_dir():
            print("Current path is not dir")
            return

        if path in [Path("/"), Path.home()]:
            raise ValueError("Refusing to delete dangerous directory")

        try:
            shutil.rmtree(path)
            print(f"Cache directory removed: {path}")
        except Exception as e:
            print(f"Failed to remove cache dir: {e}")

    def _get_dir_cache(self, type_cache: str) -> Path | None:
        if type_cache == "embedding":
            return Path(self._get_embedding_cache())
        elif type_cache == "rag":
            return Path(self._get_rag_index_dir())
        return None

    def _get_embedding_cache(self) -> str:
        return LocalRAG.default_cache_dir

    def _get_rag_index_dir(self) -> str:
        configured_path = self.model.model_config.get(
            "rag_index_dir", LocalRAG.default_index_dir
        )

        allowed_root = Path(LocalRAG.default_index_dir).resolve()
        target_path = Path(configured_path).resolve()
        if not target_path.is_relative_to(allowed_root):
            raise ValueError(
                "Configured rag_index_dir is outside the allowed "
                "cache directory"
            )

        return str(target_path)
