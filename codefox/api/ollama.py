import os
from typing import Any

import requests
from ollama import ChatResponse, Client

from codefox.api.base_api import BaseAPI, ExecuteResponse, Response
from codefox.prompts.prompt_template import PromptTemplate
from codefox.utils.local_rag import LocalRAG


class Ollama(BaseAPI):
    default_model_name = "gemma3:12b"
    default_embedding = "nomic-embed-text"
    base_url = "https://ollama.com"
    default_max_rag_chars = 4096
    default_max_diff_chars = 16_000

    def __init__(self, config=None):
        super().__init__(config)

        if self.model_config.get("base_url"):
            self.base_url = self.model_config.get("base_url")

        if "embedding" not in self.model_config or not self.model_config.get(
            "embedding"
        ):
            self.model_config["embedding"] = self.default_embedding

        api_key = os.getenv("CODEFOX_API_KEY")

        headers = None
        if api_key and api_key != "null":
            headers = {
                "Authorization": f"Bearer {api_key}",
            }

        self.rag = None

        self.client = Client(
            host=self.base_url,
            headers=headers,
            timeout=self.model_config.get("timeout", 600),
        )

    def check_model(self, name: str) -> bool:
        return name in self.get_tag_models()

    def check_connection(self) -> tuple[bool, Any]:
        try:
            self.client.show(self.default_model_name)
            return True, None
        except Exception as e:
            return False, e

    def upload_files(self, path_files: str) -> tuple[bool, Any]:
        if self.review_config["diff_only"]:
            return True, None

        rag_kw: dict = {
            "chunk_overlap": self.model_config.get("rag_chunk_overlap", 100),
            "max_query_chars": self.model_config.get("rag_max_query_chars", 2000),
        }
        if "rag_min_score" in self.model_config:
            rag_kw["min_score"] = self.model_config["rag_min_score"]

        self.rag = LocalRAG(
            self.model_config["embedding"],
            path_files,
            ollama_client=self.client,
            **rag_kw,
        )
        self.rag.build()

        return True, None

    def remove_files(self):
        pass

    def execute(self, diff_text: str) -> ExecuteResponse:
        system_prompt = PromptTemplate(self.config)

        max_rag_chars = self.model_config.get("max_rag_chars") or self.default_max_rag_chars
        max_diff_chars = self.model_config.get("max_diff_chars") or self.default_max_diff_chars

        if len(diff_text) > max_diff_chars:
            diff_text = (
                diff_text[: max_diff_chars]
                + "\n\n... [diff truncated for context length]"
            )

        rag_context = ""
        if self.rag:
            rag_chunks = self.rag.search(diff_text, k=8)
            parts: list[str] = []
            total = 0
            for c in rag_chunks:
                block = f"<file path='{c['path']}'>\n{c['text']}\n</file>"
                if total + len(block) > max_rag_chars and parts:
                    break
                parts.append(block)
                total += len(block)
            rag_context = "\n\n".join(parts)
            rag_context = f"""
## RELEVANT CONTEXT
*(Use only if needed to trace data flow. Do not analyze this section by itself.)*

{rag_context}
"""

        content = f"""# DIFF AUDIT

**CRITICAL:** Describe only what is in the diff. Use exact names from the diff (do not invent or misspell, e.g. Ollama not Olla). If something is not in the diff, say "not in the diff" — do not speculate.

## Task
Detect **behavior change** caused by the modified lines.

## Do NOT
- Explain the codebase or architecture
- Summarize classes
- Invent class/API/file names

If you do not compare **OLD vs NEW** behavior → the answer is **INVALID**.

---

## DIFF
*Git diff with +/- markers. Only these lines changed.*

```
{diff_text}
```

---

## Required reasoning

1. **List the changed lines**
2. For each change:
   - OLD behavior →
   - NEW behavior →
3. **What execution path** now behaves differently?
4. **What can break?**

If there is no behavioral change → say exactly: **NO BEHAVIORAL CHANGE.**

{rag_context}
"""
        print(content)
        
        options = {}
        if self.model_config.get("temperature") is not None:
            options["temperature"] = self.model_config["temperature"]
        if self.model_config.get("max_tokens") is not None:
            options["num_predict"] = self.model_config["max_tokens"]

        chat_response: ChatResponse = self.client.chat(
            model=self.model_config["name"],
            messages=[
                {"role": "system", "content": system_prompt.get()},
                {"role": "user", "content": content},
            ],
            options=options if options else None,
        )

        response = Response(chat_response.message.content or "")
        return response

    def get_tag_models(self) -> list[str]:
        response = requests.get(f"{self.base_url}/api/tags")

        if response.status_code == 200:
            data = response.json()
            return [
                model["name"] for model in data["models"] if model.get("name")
            ]
        else:
            return []
