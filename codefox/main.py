#!/usr/bin/env python3
import typer

from codefox.cli_manager import CLIManager


app = typer.Typer()

@app.command("scan")
def scan(
    ci: bool = typer.Option(False, "--ci", help="CI mode"),
    source_branch: str = typer.Option(None, help="Source branch"),
    target_branch: str = typer.Option(None, help="Target branch"),
):
    """Run AI code review."""
    manager = CLIManager(
        command="scan",
        args={
            "ci": ci,
            "sourceBranch": source_branch,
            "targetBranch": target_branch,
        }
    )
    manager.run()

@app.command("init")
def init():
    """Initialize CodeFox."""
    CLIManager(command="init", args={}).run()

@app.command("list")
def list_models(
    type_model: str = typer.Argument("models", help="Model type")
):
    """List available models."""
    manager = CLIManager(
        command="list",
        args={
            "typeModel": type_model,
        }
    )
    manager.run()

@app.command("clean")
def clean(
    type_cache: str = typer.Argument("all", help="Cache type")
):
    """Clean cache"""
    manager = CLIManager(
        command="clean",
        args={
            "typeCache": type_cache,
        }
    )
    manager.run()

@app.command("version")
def version():
    """Show version."""
    CLIManager(command="version", args={}).run()

def cli():
    app()

if __name__ == "__main__":
    cli()