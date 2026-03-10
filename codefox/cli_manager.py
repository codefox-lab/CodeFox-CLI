import importlib.metadata
from typing import Any
from pathlib import Path

from dotenv import load_dotenv
from rich import print

from codefox.api.model_enum import ModelEnum
from codefox.cli.init import Init
from codefox.cli.list import List
from codefox.cli.scan import Scan
from codefox.cli.clean import Clean
from codefox.api.base_api import BaseAPI
from codefox.utils.helper import Helper


class CLIManager:
    def __init__(self, command: str, args: dict[str, Any] | None = None):
        self.command = command
        self.args = args

        path_env = Path(".codefoxenv")
        if not load_dotenv(path_env) and command not in [
            "init",
            "version",
        ]:
            raise FileNotFoundError(
                "Failed to load .codefoxenv file."
                "Please ensure it exists and is properly formatted."
            )

    def run(self) -> None:
        if self.command == "version":
            version = importlib.metadata.version("codefox")
            print(f"[green]CodeFox CLI version {version}[/green]")
            return

        if self.command == "list":
            api_class = self._get_api_class()
            list_model = List(api_class, self.args)
            list_model.execute()
            return

        if self.command == "scan":
            api_class = self._get_api_class()
            scan = Scan(api_class, self.args)
            scan.execute()
            return

        if self.command == "clean":
            api_class = self._get_api_class()
            clean = Clean(api_class, self.args)
            clean.execute()
            return

        if self.command == "init":
            init = Init()
            init.execute()
            return

        print(f"[red]Unknown command: {self.command}[/red]")
        print(
            '[yellow]Please use flag "--help"',
            "to see available commands[/yellow]",
        )

    def _get_api_class(self) -> type[BaseAPI]:
        config = Helper.read_yml(".codefox.yml")
        provider = config.get("provider", "gemini")
        return ModelEnum.by_name(provider).api_class
