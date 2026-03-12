import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import git
import yaml

from codefox.utils.parser import Parser, TreeSitterParser

if TYPE_CHECKING:
    import codefox.utils.local_rag as local_rag


class Helper:
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
                ext = Path(filename).suffix.lower()
                if Parser.get_ts_parser_by_extension(ext):
                    all_files_to_upload.append(os.path.join(root, filename))

        return all_files_to_upload

    @staticmethod
    def get_diff(
        source_branch: str | None = None, target_branch: str | None = None
    ) -> str | None:
        try:
            repo = git.Repo(".")

            if source_branch and target_branch:
                diff_text = repo.git.diff(
                    f"origin/{target_branch}...origin/{source_branch}"
                )
            else:
                diff_text = repo.git.diff()

            return cast(str | None, diff_text)
        except git.exc.InvalidGitRepositoryError:
            return None

    # ------------------------------------------------------------------
    # Backward‑compatible wrappers - delegate to Parser
    # ------------------------------------------------------------------
    @staticmethod
    def parse_diff_for_rag(diff_text: str, max_tokens: int = 300) -> str:
        return cast(str, Parser.parse_diff_for_rag(diff_text, max_tokens))

    @staticmethod
    def get_ts_parser_by_extension(ext: str) -> TreeSitterParser | None:
        return Parser.get_ts_parser_by_extension(ext)

    @staticmethod
    def get_files_context(
        rag: "local_rag.LocalRAG",
        query: str,
        k: int = 5,
        max_rag_chars: int = 16_000,
        parse_diff: bool = True,
    ) -> str:
        return cast(
            str,
            Parser.get_files_context(rag, query, k, max_rag_chars, parse_diff),
        )

    @staticmethod
    def chunk_code_with_ts(parser: Any, content: str) -> list[str]:
        return cast(list[str], Parser.chunk_code_with_ts(parser, content))

    @staticmethod
    def chunk_text_sentences(
        text: str, chunk_size: int, overlap: int
    ) -> list[str]:
        return cast(
            list[str],
            Parser.chunk_text_sentences(text, chunk_size, overlap),
        )

    @staticmethod
    def smart_chunk(
        path: Path, content: str, chunk_size: Any, overlap: Any
    ) -> list[Any]:
        return cast(
            list[Any],
            Parser.smart_chunk(path, content, chunk_size, overlap),
        )
