import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast, get_args

from nltk.tokenize import sent_tokenize
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound
from tree_sitter import Parser as TreeSitterParser
from tree_sitter_language_pack import SupportedLanguage, get_parser

if TYPE_CHECKING:
    import codefox.utils.local_rag as local_rag


class Parser:
    CODE_CHUNK_TYPES = {
        "function_definition",
        "class_definition",
        "method_definition",
        "function_declaration",
        "class_declaration",
    }

    @classmethod
    def parse_diff_for_rag(cls, diff_text: str, max_tokens: int = 300) -> str:
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

    @classmethod
    def get_files_context(
        cls,
        rag: "local_rag.LocalRAG",
        query: str,
        k: int = 5,
        max_rag_chars: int = 16_000,
        parse_diff: bool = True,
    ) -> str:
        if parse_diff and (
            "diff --git" in query or "--- a/" in query or "+++ b/" in query
        ):
            query = cls.parse_diff_for_rag(query)
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

    @classmethod
    def get_ts_parser_by_extension(cls, ext: str) -> TreeSitterParser | None:
        try:
            lang = get_lexer_for_filename(ext)
            lang = lang.name.lower()
            if lang not in get_args(SupportedLanguage):
                return None

            return get_parser(cast(Any, lang))
        except (ClassNotFound, ModuleNotFoundError):
            return None

    @classmethod
    def chunk_code_with_ts(cls, parser, content: str) -> list[str]:
        tree = parser.parse(bytes(content, "utf8"))
        root = tree.root_node

        chunks = []

        def walk(node):
            if node.type in cls.CODE_CHUNK_TYPES:
                chunk = content[node.start_byte : node.end_byte]
                chunks.append(chunk)
                return

            for child in node.children:
                walk(child)

        walk(root)
        return chunks

    @classmethod
    def chunk_text_sentences(
        cls, text: str, chunk_size: int, overlap: int
    ) -> list[str]:
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

    @classmethod
    def smart_chunk(
        cls, path: Path, content: str, chunk_size, overlap
    ) -> list:
        ext = path.suffix.lower()

        parser = cls.get_ts_parser_by_extension(ext)

        if parser:
            chunks = cls.chunk_code_with_ts(parser, content)
            if chunks:
                return chunks

        return cls.chunk_text_sentences(content, chunk_size, overlap)
