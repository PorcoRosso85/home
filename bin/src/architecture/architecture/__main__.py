"""Main entry point for architecture tool."""

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def main():
    """Architecture analysis tool for cross-project responsibility separation."""
    console.print("[bold green]Architecture Tool v0.1.0[/bold green]")
    console.print("Purpose: Cross-project responsibility separation and design")
    console.print("\nThis tool is under development.")


if __name__ == "__main__":
    app()