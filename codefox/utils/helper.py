import os
from pathlib import Path
from typing import Any, TYPE_CHECKING

import git
import yaml

if TYPE_CHECKING:
    import codefox.utils.local_rag as local_rag


class Helper:
    SUPPORTED_EXTENSIONS = {
        ".py",
        ".js",
        ".java",
        ".cpp",
        ".c",
        ".cs",
        ".go",
        ".rb",
        ".php",
        ".ts",
        ".swift",
    }

    @staticmethod
    def read_yml(path: str) -> dict[str, Any]:
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Not found file with {path_obj}")

        with open(path_obj, encoding="utf-8") as file:
            config_data: Any = yaml.safe_load(file)

        if config_data is None:
            return {}
        return dict(config_data) if isinstance(config_data, dict) else {}

    @staticmethod
    def read_codefoxignore() -> list[str]:
        ignore = Path(".codefoxignore")
        if not ignore.exists():
            return []

        ignored_paths = []
        with open(ignore, encoding="utf-8") as ignore_file:
            ignored_paths = [
                line.strip()
                for line in ignore_file
                if line.strip() and not line.startswith("#")
            ]

        return ignored_paths

    @staticmethod
    def get_all_files(path_files: str) -> list[str]:
        ignored_paths = Helper.read_codefoxignore()

        all_files_to_upload = []
        for root, _, files in os.walk(path_files):
            skip_dirs = [".git", "__pycache__", "node_modules"]
            if os.path.basename(root) in skip_dirs or any(
                ignored in root for ignored in ignored_paths
            ):
                continue

            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in Helper.SUPPORTED_EXTENSIONS:
                    all_files_to_upload.append(os.path.join(root, filename))

        return all_files_to_upload

    @staticmethod
    def get_diff() -> str | None:
        try:
            repo = git.Repo(".")
            diff_text: str = repo.git.diff(repo.head.commit)
            return diff_text
        except git.exc.InvalidGitRepositoryError:
            return None
    
    @staticmethod
    def get_files_context(
        rag: "local_rag.LocalRAG", 
        query: str, 
        k: int = 5,
        max_rag_chars: int = 16_000
    ) -> str:
        rag_chunks = rag.search(query, k=k)

        total = 0
        parts: list[str] = []
        for c in rag_chunks:
            block = f"<file path='{c['path']}'>\n{c['text']}\n</file>"
            if total + len(block) > max_rag_chars and parts:
                break

            total += len(block)
            parts.append(block)
        
        return "\n\n".join(parts)
