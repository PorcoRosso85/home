"""RGL CLI entry point"""
from .infrastructure.cli_adapter import create_cli

if __name__ == "__main__":
    cli = create_cli()
    cli()