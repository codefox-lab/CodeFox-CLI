import os
from typing import Any

from rich import print
from rich.console import Console
from rich.errors import MarkupError
from rich.markdown import Markdown
from rich.markup import escape

from codefox.api.base_api import BaseAPI
from codefox.bots.github_bot import GitHubBot
from codefox.bots.gitlab_bot import GitLabBot
from codefox.cli.base_cli import BaseCLI
from codefox.cli.list import List
from codefox.utils.helper import Helper


class Scan(BaseCLI):
    def __init__(self, model: type[BaseAPI], args: dict[str, Any]):
        self.model = model()
        self.args = args

        self.github_bot = None
        self.gitlab_bot = None
        if self.args.get("ci", False) and os.getenv("GITHUB_TOKEN"):
            self.github_bot = GitHubBot()
        elif self.args.get("ci", False) and os.getenv("GITLAB_TOKEN"):
            self.gitlab_bot = GitLabBot()

    def execute(self) -> None:
        source_branch, target_branch = self._get_branchs()

        diff_text = Helper.get_diff(source_branch, target_branch)
        if not diff_text:
            print(
                "[yellow]Repository is not found or not have change[/yellow]"
            )
            return

        is_connect, error = self.model.check_connection()
        if not is_connect:
            print(f"[red]Failed to connect to model: {error}[/red]")
            return

        name = self.model.model_config["name"]
        if not self.model.check_model(name):
            print(f"[red]Model '{name}' not found.")

            command = List(
                model=self.model.__class__,
                args={
                    "typeModel": "models",
                },
            )
            command.execute()
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

        if not self.args.get("ci", False):
            self._classic_response_answer(diff_text)
            return

        self._ci_response_answer(diff_text)

    def _ci_response_answer(self, diff_text: str) -> None:
        response = self.model.execute(diff_text)
        if self.github_bot is not None:
            self.github_bot.send(response.text)

        if self.gitlab_bot is not None:
            self.gitlab_bot.send(response.text)

        self.model.remove_files()

    def _classic_response_answer(self, diff_text: str) -> None:
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

    def _get_branchs(self) -> tuple[str | None, str | None]:
        source_branch = self.args.get("sourceBranch")
        target_branch = self.args.get("targetBranch")

        if source_branch and target_branch:
            return source_branch, target_branch

        source_branch = self.model.review_config["sourceBranch"]
        target_branch = self.model.review_config["targetBranch"]

        return source_branch, target_branch
