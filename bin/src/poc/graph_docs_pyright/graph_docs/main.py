#!/usr/bin/env python3
"""graph_docs CLI - Dual KuzuDB Query Interface

I/O制御層：コマンドライン引数の処理とクエリ結果の表示
"""

from graph_docs.infrastructure.cli.cli_handler import main as cli_main


def main():
    """Main entry point that delegates to the CLI handler."""
    cli_main()


if __name__ == "__main__":
    main()