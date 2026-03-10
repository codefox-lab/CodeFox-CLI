#!/usr/bin/env python3
import typer

from codefox.cli_manager import CLIManager


app = typer.Typer()

@app.command()
def scan(
    ci: str = typer.Option(False, help="CI mode"),
    sourceBranch: str = typer.Option(None, help="Source branch"),
    targetBranch: str = typer.Option(None, help="Target branch"),
):
    """Run AI code review."""
    manager = CLIManager(
        command="scan",
        args={
            "ci": ci,
            "sourceBranch": sourceBranch,
            "targetBranch": targetBranch,
        }
    )
    manager.run()

@app.command()
def init():
    """Initialize CodeFox."""
    CLIManager(command="init", args={}).run()

@app.command()
def list(
    typeModel: str = typer.Option("models", help="Model type")
):
    """List available models."""
    manager = CLIManager(
        command="list",
        args={
            "typeModel": typeModel,
        }
    )
    manager.run()

@app.command()
def clean(
    typeCache: str = typer.Option("all", help="Cache type")
):
    """Clean cache"""
    manager = CLIManager(
        command="clean",
        args={
            "typeCache": typeCache,
        }
    )
    manager.run()

@app.command()
def version():
    """Show version."""
    CLIManager(command="version", args={}).run()

def cli():
    app()

if __name__ == "__main__":
    cli()