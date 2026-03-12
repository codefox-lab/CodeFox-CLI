from collections.abc import Callable
from typing import cast

from codefox.tools.base_tool import BaseTool
from codefox.utils.local_rag import LocalRAG
from codefox.utils.parser import Parser


class RagTool(BaseTool):
    def __init__(self, rag: LocalRAG | None, max_rag_chars: int):
        self.rag = rag
        self.max_rag_chars = max_rag_chars

    def get_tool(self) -> Callable:
        def search_knowledge_base(query: str) -> str:
            """Search the project's internal knowledge base using semantic RAG.

            Use this tool when you need additional context about the codebase,
            architecture, APIs, configuration, or implementation details that
            are not present in the current conversation.
            The tool performs semantic search over indexed project files and
            returns the most relevant code snippets or documentation fragments.

            Args:
                query: A natural language search query describing what you
                    want to find. The query may include:
                    - class names
                    - function or method names
                    - module names
                    - API endpoints
                    - configuration keys
                    - error messages
                    - short code fragments

                    Example queries:
                    - "def validate_token"
                    - "class UserService methods"
                    - "how authentication middleware works"
                    - "database connection configuration"
                    - "function create_user implementation"

            Returns:
                A string containing the most relevant code snippets or
                documentation extracted from the project knowledge base.
                The result may include multiple fragments from different files.
            """
            if not self.rag:
                return "None RAG"

            return cast(
                str,
                Parser.get_files_context(
                    self.rag, query, k=18, max_rag_chars=self.max_rag_chars
                ),
            )

        return search_knowledge_base
