import os
import time
from typing import Any, cast

from google import genai
from google.genai import types

from codefox.api.base_api import BaseAPI, ExecuteResponse, Response
from codefox.prompts.prompt_template import PromptTemplate
from codefox.tools.rag_tool import RagTool


class Gemini(BaseAPI):
    default_model_name = "gemini-2.5-flash"
    default_max_rag_chars = 4096
    default_max_diff_chars = 500_000

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.client = genai.Client(api_key=os.getenv("CODEFOX_API_KEY"))

    def check_model(self, name: str) -> bool:
        return name in self.get_tag_models()

    def check_connection(self) -> tuple[bool, Any]:
        try:
            self.client.models.list()
            return True, None
        except Exception as e:
            return False, e

    def get_tag_models(self) -> list[str]:
        response = self.client.models.list()
        page = response.page or []
        return [
            (model.name or "").replace("models/", "")
            for model in page
            if (
                model.supported_actions
                and "generateContent" in model.supported_actions
            )
        ]

    def upload_files(self, path_files: str) -> tuple[bool, Any]:
        return super().upload_files(path_files)

    def remove_files(self) -> None:
        self.rag = None

    def execute(self, diff_text: str) -> ExecuteResponse:
        rag_context = self.get_context(diff_text)

        system_prompt = PromptTemplate(self.config)
        context_prompt = PromptTemplate(
            {"files_context": rag_context, "diff_text": diff_text}, "content"
        )

        contents = [
            types.Content(
                role="user", parts=[types.Part(text=context_prompt.get())]
            )
        ]

        rag_tool = RagTool(self.rag, self.max_rag_chars)
        search_knowledge_base = rag_tool.get_tool()

        tools = self._get_tools() if self.review_config["tools"] else None
        tool_config = (
            types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode=cast(Any, "ANY"),
                )
            )
            if self.review_config["tools"]
            else None
        )

        response = self.client.models.generate_content(
            model=self.model_config["name"],
            contents=cast(Any, contents),
            config=types.GenerateContentConfig(
                system_instruction=system_prompt.get(),
                temperature=self.model_config["temperature"],
                max_output_tokens=self.model_config["max_tokens"],
                tools=cast(Any, tools),
                tool_config=tool_config,
            ),
        )

        candidates = response.candidates
        if candidates:
            first_content = candidates[0].content
            if first_content is not None:
                contents.append(first_content)

        max_tool_iterations = self.review_config["max_tool_iterations"]
        tool_iteration = 0

        while (
            tool_iteration < max_tool_iterations
            and self.review_config["tools"]
        ):
            candidates = response.candidates
            if not candidates:
                break
            content = candidates[0].content
            if content is None:
                break
            parts = content.parts
            if not parts:
                break

            part = parts[0]
            if part.function_call:
                function_call = part.function_call
                fc_name = function_call.name or "search_knowledge_base"
                if fc_name == "search_knowledge_base":
                    args = function_call.args or {}
                    query = (
                        args.get("query", "") if isinstance(args, dict) else ""
                    )
                    result_data = {"result": search_knowledge_base(query)}
                else:
                    result_data = {
                        "result": (f"Error: Tool {fc_name} is not supported.")
                    }

                function_response_part = types.Part.from_function_response(
                    name=fc_name, response=result_data
                )

                contents.append(
                    types.Content(role="user", parts=[function_response_part])
                )

                tool_iteration += 1

                response = self.client.models.generate_content(
                    model=self.model_config["name"],
                    contents=cast(Any, contents),
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt.get(),
                        tools=cast(Any, tools),
                        temperature=self.model_config["temperature"],
                        max_output_tokens=self.model_config["max_tokens"],
                    ),
                )

                time.sleep(0.5)
            else:
                break

        return Response(text=response.text or "")

    def _get_tools(self) -> list[types.Tool]:
        search_knowledge_base_function = {
            "name": "search_knowledge_base",
            "description": (
                "Search the project's internal knowledge base using semantic "
                "retrieval (RAG). "
                "Use this tool when you need additional context "
                "about the codebase, architecture, APIs, coding conventions, "
                "or implementation details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "A natural language query "
                            "describing what to search "
                            "for in the knowledge base. The query may include "
                            "class names, function or method names, modules, "
                            "APIs, configuration keys, "
                            "error messages, or short "
                            "code snippets. Use it to find related "
                            "implementations, documentation, or examples. "
                            "Examples: 'def method_name', "
                            "'class UserService methods', "
                            "'function validate_token'"
                        ),
                    },
                },
                "required": ["query"],
            },
        }

        return [
            types.Tool(
                function_declarations=[
                    cast(Any, search_knowledge_base_function),
                ]
            )
        ]
