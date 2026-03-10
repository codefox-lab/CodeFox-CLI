from pathlib import Path

import yaml
from dotenv import load_dotenv, set_key
from rich import print
from rich.prompt import Confirm, Prompt

from codefox.api.base_api import BaseAPI
from codefox.api.model_enum import ModelEnum
from codefox.cli.base_cli import BaseCLI


class Init(BaseCLI):
    def __init__(self, model_enum: ModelEnum | None = None):
        self.model_enum = model_enum or self._ask_model()
        self.api_class: type[BaseAPI] = self.model_enum.api_class
        self.config_path = Path(".codefoxenv")
        self.ignore_path = Path(".codefoxignore")
        self.yaml_config_path = Path(".codefox.yml")

    def _ask_model(self) -> ModelEnum:
        names = ModelEnum.names()
        choice = Prompt.ask(
            f"[yellow]Select provider[/yellow] ({', '.join(names)})",
            default=names[0],
            choices=names,
        )
        return ModelEnum.by_name(choice)

    def execute(self) -> None:
        api_key = self._ask_api_key() or ""

        if not self._write_config(api_key):
            return

        self._ensure_ignore_file()
        self._ensure_yaml_config()
        self._ensure_gitignore()

        if not self._check_connection():
            return

        print("[green]CodeFox CLI initialized successfully![/green]")

    def _ask_api_key(self) -> str | None:
        if not Confirm.ask(
            f"[yellow]Enter API key for {self.model_enum.name}?[/yellow]",
            default=True,
        ):
            return None

        api_key = Prompt.ask(
            f"[yellow]API Key for {self.model_enum.name}[/yellow]",
            default="",
        ).strip()

        if not self._is_valid_key(api_key):
            print("[red]Invalid API key format.[/red]")
            return None

        return api_key

    def _is_valid_key(self, key: str) -> bool:
        if len(key) < 30:
            return False

        valid_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
        )
        if not any(c in valid_chars for c in key):
            return False

        return True

    def _ensure_yaml_config(self) -> None:
        if self.yaml_config_path.exists():
            overwrite = Confirm.ask(
                "[yellow].codefox.yml already exists. Overwrite?[/yellow]",
                default=False,
            )
            if not overwrite:
                print("[blue]Skipping .codefox.yml creation.[/blue]")
                return

        try:
            print("[yellow]Creating .codefox.yml...[/yellow]")

            default_model_name = getattr(
                self.api_class, "default_model_name", "gemini-2.0-flash"
            )
            default_config = {
                "provider": self.model_enum.name.lower(),
                "model": {
                    "name": default_model_name,
                    "temperature": 0.2,
                    "max_tokens": 4000,
                },
                "review": {
                    "severity": "high",
                    "max_issues": None,
                    "suggest_fixes": True,
                    "diff_only": False,
                },
                "baseline": {
                    "enable": True,
                },
                "ruler": {
                    "security": True,
                    "performance": True,
                    "style": True,
                },
                "prompt": {
                    "system": None,
                    "extra": None,
                    "strict_facts": False,
                },
            }

            with self.yaml_config_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(default_config, f, sort_keys=False)

            print("[green].codefox.yml created successfully![/green]")

        except Exception as e:
            print(f"[red]Error creating .codefox.yml: {e}[/red]")

    def _write_config(self, api_key: str) -> bool:
        if self.config_path.exists():
            overwrite = Confirm.ask(
                "[yellow].codefoxenv already exists. Overwrite"
                ".codefoxenv?[/yellow]"
            )
            if not overwrite:
                print("[blue]Skipping .codefoxenv update.[/blue]")
                return True

        try:
            print("[yellow]Saving API key to .codefoxenv...[/yellow]")

            self.config_path.touch(exist_ok=True)
            set_key(str(self.config_path), "CODEFOX_API_KEY", api_key)

            if not load_dotenv(self.config_path):
                print("[red].codefoxenv was not loaded[/red]")
                return False

            print("[green]API key saved successfully![/green]")
            return True
        except Exception as e:
            print(f"[red]Error writing .env: {e}[/red]")
            return False

    def _ensure_ignore_file(self) -> None:
        if self.ignore_path.exists():
            print("[blue].codefoxignore already exists, skipping...[/blue]")
            return

        try:
            print("[yellow]Creating .codefoxignore...[/yellow]")

            default = "\n".join(
                [
                    "node_modules/",
                    "vendor/",
                    ".git/",
                    "__pycache__/",
                    ".env",
                ]
            )

            self.ignore_path.write_text(default + "\n", encoding="utf-8")
        except Exception as e:
            print(f"[red]Error creating .codefoxignore: {e}[/red]")

    def _ensure_gitignore(self) -> None:
        gitignore = Path(".gitignore")
        entry = ".codefoxenv"
        if gitignore.exists():
            content = gitignore.read_text()
            if entry not in content:
                with gitignore.open("a") as f:
                    f.write(f"\n{entry}\n")
        else:
            gitignore.write_text(f"{entry}\n")

    def _check_connection(self) -> bool:
        print("[yellow]Checking model connection...[/yellow]")

        try:
            model = self.api_class()
            if not model.check_connection():
                print(
                    "[red]Failed to connect to model API. "
                    "Check API key and network.[/red]"
                )
                return False
        except Exception as e:
            print(
                "[red]Failed to connect to model API. "
                f"Check API key and network: {e}[/red]"
            )
            return False

        return True
