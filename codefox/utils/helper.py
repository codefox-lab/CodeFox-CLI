import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import git
import yaml
from nltk.tokenize import sent_tokenize
from tree_sitter import Parser
from tree_sitter_language_pack import get_parser

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

    CODE_CHUNK_TYPES = {
        "function_definition",
        "class_definition",
        "method_definition",
        "function_declaration",
        "class_declaration",
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
    def get_diff(
        source_branch: str | None = None,
        target_branch: str | None = None
    ) -> str | None:
        try:
            repo = git.Repo(".")

            if not source_branch:
                source_branch = repo.head.commit

            diff_text: str = repo.git.diff(source_branch, target_branch)
            return diff_text
        except git.exc.InvalidGitRepositoryError:
            return None

    @staticmethod
    def parse_diff_for_rag(diff_text: str, max_tokens: int = 300) -> str:
        if not diff_text or not diff_text.strip():
            return diff_text.strip()

        paths: set[str] = set()
        tokens: set[str] = set()

        for m in re.finditer(r"diff --git a/(.+?) b/\1", diff_text):
            paths.add(m.group(1).strip())
        for m in re.finditer(
            r"^(?:---|\+\+\+) [ab]/(.+?)(?:\s|$)", diff_text, re.MULTILINE
        ):
            paths.add(m.group(1).strip())

        changed_lines = re.findall(
            r"^[+-](?![-+]{2})(.+)$", diff_text, re.MULTILINE
        )

        stop = {
            "the",
            "and",
            "for",
            "return",
            "if",
            "else",
            "null",
            "true",
            "false",
            "def",
            "class",
            "function",
        }

        for line in changed_lines:
            line = line.strip()
            for w in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", line):
                if len(w) > 1 and w.lower() not in stop:
                    tokens.add(w)

            for w in re.findall(r"\$[a-zA-Z_][a-zA-Z0-9_]*", line):
                tokens.add(w)

            for w in re.findall(r"['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]", line):
                if len(w) > 1:
                    tokens.add(w)

        parts = list(paths) + sorted(tokens)
        query = " ".join(parts[:max_tokens]) if max_tokens else " ".join(parts)
        return query.strip() or diff_text[:2000].strip()

    @staticmethod
    def get_files_context(
        rag: "local_rag.LocalRAG",
        query: str,
        k: int = 5,
        max_rag_chars: int = 16_000,
        parse_diff: bool = True,
    ) -> str:
        if parse_diff and (
            "diff --git" in query or "--- a/" in query or "+++ b/" in query
        ):
            query = Helper.parse_diff_for_rag(query)
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

    @staticmethod
    def get_ts_parser_by_extension(ext: str) -> Parser | None:
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "c_sharp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
        }

        lang = mapping.get(ext)
        if not lang:
            return None

        return get_parser(cast(Any, lang))

    @staticmethod
    def chunk_code_with_ts(parser, content: str) -> list[str]:
        tree = parser.parse(bytes(content, "utf8"))
        root = tree.root_node

        chunks = []

        def walk(node):
            if node.type in Helper.CODE_CHUNK_TYPES:
                chunk = content[node.start_byte : node.end_byte]
                chunks.append(chunk)
                return

            for child in node.children:
                walk(child)

        walk(root)
        return chunks

    @staticmethod
    def chunk_text_sentences(text, chunk_size, overlap) -> list[str]:
        sentences = sent_tokenize(text)
        chunks = []
        current = []

        current_len = 0

        for sent in sentences:
            current.append(sent)
            current_len += len(sent)

            if current_len >= chunk_size:
                chunks.append(" ".join(current))

                overlap_text = " ".join(current)[-overlap:]
                current = [overlap_text]
                current_len = len(overlap_text)

        if current:
            chunks.append(" ".join(current))

        return chunks

    @staticmethod
    def smart_chunk(path: Path, content: str, chunk_size, overlap) -> list:
        ext = path.suffix.lower()

        parser = Helper.get_ts_parser_by_extension(ext)

        if parser:
            chunks = Helper.chunk_code_with_ts(parser, content)
            if chunks:
                return chunks

        return Helper.chunk_text_sentences(content, chunk_size, overlap)
