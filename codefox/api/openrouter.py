import json
import os
import time
from typing import Any, cast

from openai import OpenAI

from codefox.api.base_api import BaseAPI, ExecuteResponse, Response
from codefox.prompts.prompt_template import PromptTemplate
from codefox.tools.rag_tool import RagTool


class OpenRouter(BaseAPI):
    default_model_name = "qwen/qwen3-vl-30b-a3b-thinking"
    base_url = "https://openrouter.ai/api/v1"
    default_max_rag_chars = 4096
    default_max_diff_chars = 16_000

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)

        if "base_url" in self.model_config or self.model_config.get(
            "base_url"
        ):
            self.base_url = self.model_config["base_url"]

        self.client = OpenAI(
            api_key=os.getenv("CODEFOX_API_KEY"), base_url=self.base_url
        )

    def check_connection(self) -> tuple[bool, Any]:
        try:
            self.client.models.list()
            return True, None
        except Exception as e:
            return False, e

    def check_model(self, name: str) -> bool:
        return name in self.get_tag_models()

    def execute(self, diff_text: str = "") -> ExecuteResponse:
        rag_context = self.get_context(diff_text)

        rag_tool = RagTool(self.rag, self.max_rag_chars)
        search_knowledge_base = rag_tool.get_tool()

        think_mode = None
        if self.model_config.get("think_mode"):
            think_mode = {"reasoning": {"enabled": True}}

        system_prompt = PromptTemplate(self.config)
        context_prompt = PromptTemplate(
            {"files_context": rag_context, "diff_text": diff_text}, "content"
        )
        content = context_prompt.get()
        messages = [
            {"role": "system", "content": system_prompt.get()},
            {"role": "user", "content": content},
        ]

        tools = self._get_tools() if self.review_config["tools"] else None

        response = self.client.chat.completions.create(
            model=self.model_config["name"],
            temperature=self.model_config["temperature"],
            timeout=self.model_config.get("timeout", 600),
            max_tokens=self.model_config["max_tokens"],
            max_completion_tokens=self.model_config["max_completion_tokens"],
            tools=cast(Any, tools),
            messages=cast(Any, messages),
            extra_body=think_mode,
        )

        message = response.choices[0].message
        max_tool_iterations = self.review_config["max_tool_iterations"]
        tool_iteration = 0

        while (
            tool_iteration < max_tool_iterations
            and self.review_config["tools"]
        ):
            message = response.choices[0].message
            if message.tool_calls:
                tool_iteration += 1
                for tool_call in message.tool_calls:
                    fn = getattr(tool_call, "function", None)
                    if fn is None:
                        continue
                    tool_name = fn.name

                    try:
                        tool_args = json.loads(fn.arguments)
                        if tool_name == "search_knowledge_base" and isinstance(
                            tool_args, dict
                        ):
                            query = tool_args.get("query", "")
                            result_data = search_knowledge_base(query)
                        else:
                            result_data = (
                                f"Error: Tool {tool_name} is not supported."
                            )
                    except json.JSONDecodeError:
                        result_data = "Error: Invalid JSON in tool arguments."

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": getattr(tool_call, "id", ""),
                            "content": result_data,
                        }
                    )

                response = self.client.chat.completions.create(
                    model=self.model_config["name"],
                    temperature=self.model_config["temperature"],
                    timeout=self.model_config.get("timeout", 600),
                    max_tokens=self.model_config["max_tokens"],
                    max_completion_tokens=self.model_config[
                        "max_completion_tokens"
                    ],
                    tools=cast(Any, tools),
                    messages=cast(Any, messages),
                    extra_body=think_mode,
                )
                message = response.choices[0].message
                time.sleep(0.5)
            else:
                break

        raw = message.content
        return Response(text=raw if raw is not None else "")

    def remove_files(self) -> None:
        pass

    def upload_files(self, path_files: str) -> tuple[bool, Any]:
        return super().upload_files(path_files)

    def get_tag_models(self) -> list:
        models = self.client.models.list()
        return [model.id for model in models]

    def _get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": (
                        "Search the project's internal knowledge base using "
                        "semantic retrieval (RAG). "
                        "Use this tool when you need "
                        "additional context about the codebase, architecture, "
                        "APIs, coding conventions, or implementation details."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": (
                                    "A natural language query describing what "
                                    "to search for in the knowledge base. The "
                                    "query may include class names, "
                                    "function or method names, modules, "
                                    "APIs, configuration "
                                    "keys, error messages, or short code "
                                    "snippets. Use it to find related "
                                    "implementations, documentation, or "
                                    "examples. Examples: 'def method_name', "
                                    "'class UserService methods', "
                                    "'function validate_token'"
                                ),
                            }
                        },
                    },
                    "required": ["query"],
                },
            }
        ]
