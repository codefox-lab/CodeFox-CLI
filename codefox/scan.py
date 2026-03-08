import os

from rich import print
from rich.console import Console
from rich.errors import MarkupError
from rich.markdown import Markdown
from rich.markup import escape
from rich.table import Table

from codefox.api.base_api import BaseAPI
from codefox.utils.helper import Helper


class Scan:
    def __init__(self, model: type[BaseAPI]):
        self.model = model()

    def execute(self) -> None:
        source_branch = self.model.review_config['sourceBranch']
        target_branch = self.model.review_config['targetBranch']

        diff_text = Helper.get_diff(source_branch, target_branch)
        if not diff_text:
            print(
                "[yellow]Repository is not found or not have change[/yellow]"
            )
            return

        is_connect, error = self.model.check_connection()
        if not is_connect:
            print(f"[red]Failed to connect to mode: {error}[/red]")
            return

        name = self.model.model_config["name"]
        if not self.model.check_model(name):
            models = self.model.get_tag_models()

            print(f"[red]Model '{name}' not found.")

            if not models:
                print("[yellow]No models available[/yellow]")
                return

            table = Table()

            table.add_column("#", style="dim", width=4, justify="right")
            table.add_column("Model name", style="cyan")

            for i, model_name in enumerate(models, start=1):
                table.add_row(str(i), model_name)

            print(table)
            return

        if not diff_text.strip():
            print(
                "[yellow]No changes to analyze."
                "Make changes and run scan again.[/yellow]"
            )
            return

        is_upload, error = self.model.upload_files(os.getcwd())
        if not is_upload:
            print(
                "[red]Failed to upload files to model: "
                + escape(str(error))
                + "[/red]"
            )
            return

        print("[yellow]Waiting for model response...[/yellow]")
        try:
            try:
                response = self.model.execute(diff_text)

                console = Console()
                text = Markdown(response.text, code_theme="manni")
                print("[green]Scan result from model:[/green]\n")
                console.print(text)
            except MarkupError:
                print(
                    "[green]Scan result from model:[/green]\n"
                    + escape(response.text)
                )
        except Exception as e:
            err_str = str(e)
            print("[red]Failed scan: " + escape(err_str) + "[/red]")

        self.model.remove_files()
