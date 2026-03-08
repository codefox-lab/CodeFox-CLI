import os
import time
from typing import Any

import requests
from ollama import ChatResponse, Client, pull, web_fetch
from rich import print
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.prompt import Confirm

from codefox.api.base_api import BaseAPI, ExecuteResponse, Response
from codefox.prompts.prompt_template import PromptTemplate
from codefox.utils.helper import Helper
from codefox.utils.local_rag import LocalRAG


class Ollama(BaseAPI):
    default_model_name = "gemma3:12b"
    default_embedding = "BAAI/bge-small-en-v1.5"
    base_url = "http://localhost:11434"
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
        if name not in self.get_tag_models():
            return self._pull_model(name)

        return True

    def check_connection(self) -> tuple[bool, Any]:
        try:
            self.client.show(self.default_model_name)
            return True, None
        except Exception as e:
            return False, e

    def upload_files(self, path_files: str) -> tuple[bool, Any]:
        if self.review_config["diff_only"]:
            return True, None

        rag_kw = {
            "max_query_chars": self.model_config.get(
                "rag_max_query_chars", 2000
            ),
        }
        key_map = {
            "rag_min_score": "min_score",
            "rag_chunk_size": "chunk_size",
            "rag_chunk_overlap": "chunk_overlap",
            "rag_embed_batch_size": "embed_batch_size",
            "rag_max_chunks": "max_chunks",
            "rag_max_files": "max_files",
            "rag_threads_embedding": "threads_embedding",
            "rag_lazy_load": "lazy_load",
            "rag_index_dir": "index_dir",
        }
        for config_key, kw_key in key_map.items():
            if config_key in self.model_config:
                rag_kw[kw_key] = self.model_config[config_key]

        self.rag = LocalRAG(
            self.model_config["embedding"], files_path=path_files, **rag_kw
        )
        if not self.rag.load_index():
            self.rag.build()
            self.rag.save_index()

        return True, None

    def remove_files(self):
        pass

    def execute(self, diff_text: str) -> ExecuteResponse:
        max_rag_chars = (
            self.model_config.get("max_rag_chars")
            or self.default_max_rag_chars
        )
        max_diff_chars = (
            self.model_config.get("max_diff_chars")
            or self.default_max_diff_chars
        )

        if len(diff_text) > max_diff_chars:
            diff_text = (
                diff_text[:max_diff_chars]
                + "\n\n... [diff truncated for context length]"
            )

        rag_context = ""
        if self.rag:
            rag_context = Helper.get_files_context(
                self.rag, diff_text, k=12, max_rag_chars=max_rag_chars
            )

        system_prompt = PromptTemplate(self.config)
        context_prompt = PromptTemplate(
            {
                "files_context": rag_context,
                "diff_text": diff_text,
            },
            "content",
        )

        def search_knowledge_base(query: str) -> str:
            if not self.rag:
                return "None RAG"

            return Helper.get_files_context(
                self.rag, 
                query, 
                k=18, 
                max_rag_chars=max_rag_chars
            )

        options = {}
        if self.model_config.get("temperature") is not None:
            options["temperature"] = self.model_config["temperature"]
        if self.model_config.get("max_tokens") is not None:
            options["num_predict"] = self.model_config["max_tokens"]
        
        tools = None                                                                
        if self.review_config.get("tools") and self.rag:                                                                                                      
            tools = [search_knowledge_base,]
        
        messages = [
            {"role": "system", "content": system_prompt.get()},
            {"role": "user", "content": context_prompt.get()},
        ]

        print(messages)

        chat_response: ChatResponse = self.client.chat(
            model=self.model_config["name"],
            messages=messages,
            options=options if options else None,
            tools=tools if tools else None,
            think=self.model_config["think_mode"]
        )

        messages.append(chat_response.message)                                                                                                                
        max_tool_iterations = 25                                                                                                                               
        tool_iteration = 0                                                                                                                                    
                                                                                                                                                            
        while chat_response.message.tool_calls and tool_iteration < max_tool_iterations:                                                                      
            tool_iteration += 1                                                                                                                               
            print(chat_response.message.thinking)                                                                                                             
            print(chat_response.message.tool_calls)                                                                                                           
                                                                                                                                                            
            for call in chat_response.message.tool_calls:                                                                                                     
                if call.function.name == 'search_knowledge_base':
                    args = call.function.arguments                                                                                     
                    if 'query' not in args or len(args) != 1:                                                                                                     
                        result = 'Error: Invalid arguments for search_knowledge_base'                                                                            
                    else:                                                                                                                                         
                        result = search_knowledge_base(args['query'])                                                                              
                else:                                                                                                                                         
                    result = 'Unknown tool'                                                                                                                   
                                                                                                                                                            
                print(call.function.name)                                                                                                                     
                print(call.function.arguments)                                                                                                                
                print(result)                                                                                                                                 
                                                                                                                                                            
                messages.append({                                                                                                                                     
                    'role': 'tool',                                                                                                                                   
                    'name': call.function.name,                                                                                                                       
                    'content': str(result)                                                                                         
                })
                                                                                                                                        
            chat_response: ChatResponse = self.client.chat(                                                                                                   
                model=self.model_config["name"],                                                                                                              
                messages=messages,                                                                                                                            
                options=options if options else None,                                                                                                      
                tools=[search_knowledge_base,],                                                                                                         
                think=self.model_config["think_mode"]                                                                                                                                    
            )                                                                                                                                                 
                                                                                                        
            time.sleep(2)                                                                                                                                     
                                                                                                                              
        if tool_iteration >= max_tool_iterations:                                                                                                             
            print("[yellow]Warning: Max tool iterations reached[/yellow]") 

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

    def _pull_model(self, model: str) -> bool:
        if Confirm.ask(
            "[yellow]Do you wanna download model?[/yellow]", default=True
        ):
            try:
                print(f"Starting download for model: {model}")

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task(
                        f"Downloading {model}", total=None
                    )

                    for event in pull(model, stream=True):
                        completed = event.get("completed")
                        total = event.get("total")
                        status = event.get("status")

                        if total:
                            progress.update(task, total=total)

                        if completed:
                            progress.update(task, completed=completed)

                        if status:
                            progress.update(
                                task, description=f"[cyan]{status}"
                            )

                print(f"[green]Model {model} downloaded successfully.[/green]")
                return True
            except Exception as e:
                print(f"[red]Sorry but we cannot download model: {e}[/red]")
                return False

        return False
