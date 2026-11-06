import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import git
import yaml

from codefox.utils.parser import Parser, TreeSitterParser


class GitRepositoryError(RuntimeError):
    """Raised when the current directory is not inside a Git repository."""


class GitBranchNotFoundError(RuntimeError):
    """Raised when a requested source or target branch cannot be resolved."""

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
            repo = git.Repo(".", search_parent_directories=True)
        except (
            git.exc.InvalidGitRepositoryError,
            git.exc.NoSuchPathError,
        ) as e:
            raise GitRepositoryError(
                "The current directory is not a Git repository. "
                "Run this command inside a checkout containing .git."
            ) from e

        if source_branch and target_branch:
            refs: dict[str, str] = {}
            for branch in (source_branch, target_branch):
                for ref in (f"origin/{branch}", branch):
                    try:
                        refs[branch] = str(repo.commit(ref))
                        break
                    except (git.exc.BadName, ValueError):
                        continue
                if branch not in refs:
                    raise GitBranchNotFoundError(
                        f"Branch '{branch}' does not exist locally or on "
                        "the configured origin remote."
                    )

            try:
                return cast(
                    str | None,
                    repo.git.diff(
                        f"{refs[target_branch]}...{refs[source_branch]}"
                    ),
                )
            except git.exc.GitCommandError as e:
                raise RuntimeError(f"Unable to compare branches: {e}") from e

        try:
            return cast(str | None, repo.git.diff())
        except git.exc.GitCommandError as e:
            raise RuntimeError(f"Unable to read the Git diff: {e}") from e

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
