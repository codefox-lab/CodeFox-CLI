from typing import Any

from rich import print
from rich.table import Table

from codefox.utils.local_rag import LocalRAG
from codefox.api.base_api import BaseAPI
from codefox.cli.base_cli import BaseCLI


class List(BaseCLI):
    def __init__(self, model: type[BaseAPI], args: dict[str, Any] | None = None):
        self.model = model()
        self.args = args
    
    def _get_tag_model(self) -> list[str]:
        if self.args and self.args.get("typeModel") == "embeddings":
            return LocalRAG.get_model_tag()

        return self.model.get_tag_models()

    def execute(self) -> None:
        is_connect, error = self.model.check_connection()
        if not is_connect:
            print(f"[red]Failed to connect to mode: {error}[/red]")
            return

        try:
            models = self._get_tag_model()

            if not models:
                print("[yellow]No models available[/yellow]")
                return

            table = Table()

            table.add_column("#", style="dim", width=4, justify="right")
            table.add_column("Model name", style="cyan")

            for i, model_name in enumerate(models, start=1):
                table.add_row(str(i), model_name)

            print(table)
        except Exception as e:
            print(f"[red]Failed get models from provider: {e}[/red]")
