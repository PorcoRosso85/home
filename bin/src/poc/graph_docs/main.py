#!/usr/bin/env python3
"""graph_docs CLI - Dual KuzuDB Query Interface

I/O制御層：コマンドライン引数の処理とクエリ結果の表示
"""

import typer
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich import print as rprint
import json

from mod import DualKuzuDB, QueryResult, DualQueryResult

app = typer.Typer(help="2つのKuzuDBに対するクエリインターフェース")
console = Console()

def display_query_result(result: QueryResult) -> None:
    """単一のクエリ結果を表示"""
    if result.error:
        console.print(f"[red]Error in {result.source}: {result.error}[/red]")
        return
    
    if not result.rows:
        console.print(f"[yellow]{result.source}: No results[/yellow]")
        return
    
    table = Table(title=f"Results from {result.source}")
    for col in result.columns:
        table.add_column(col)
    
    for row in result.rows:
        table.add_row(*[str(val) for val in row])
    
    console.print(table)

def display_dual_result(result: DualQueryResult) -> None:
    """2つのDBの結果を表示"""
    if result.db1_result:
        display_query_result(result.db1_result)
    
    console.print()  # 空行
    
    if result.db2_result:
        display_query_result(result.db2_result)
    
    if result.combined:
        console.print("\n[bold]Combined Results:[/bold]")
        rprint(result.combined)

@app.command()
def query(
    db1_path: Path = typer.Argument(..., help="1つ目のKuzuDBディレクトリパス"),
    db2_path: Path = typer.Argument(..., help="2つ目のKuzuDBディレクトリパス"),
    query_text: str = typer.Argument(..., help="実行するCypherクエリ"),
    single: Optional[str] = typer.Option(None, "--single", "-s", help="単一のDBのみクエリ (db1 or db2)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON形式で出力")
):
    """指定されたクエリを実行"""
    
    try:
        with DualKuzuDB(db1_path, db2_path) as db:
            if single:
                result = db.query_single(single, query_text)
                if json_output:
                    output = {
                        "source": result.source,
                        "columns": result.columns,
                        "rows": result.rows,
                        "error": result.error
                    }
                    console.print_json(data=output)
                else:
                    display_query_result(result)
            else:
                result = db.query_both(query_text)
                if json_output:
                    output = {
                        "db1": {
                            "columns": result.db1_result.columns if result.db1_result else [],
                            "rows": result.db1_result.rows if result.db1_result else [],
                            "error": result.db1_result.error if result.db1_result and result.db1_result.error else None
                        } if result.db1_result or (result.db1_result and result.db1_result.error) else None,
                        "db2": {
                            "columns": result.db2_result.columns if result.db2_result else [],
                            "rows": result.db2_result.rows if result.db2_result else [],
                            "error": result.db2_result.error if result.db2_result and result.db2_result.error else None
                        } if result.db2_result or (result.db2_result and result.db2_result.error) else None
                    }
                    console.print_json(data=output)
                else:
                    display_dual_result(result)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def parallel(
    db1_path: Path = typer.Argument(..., help="1つ目のKuzuDBディレクトリパス"),
    db2_path: Path = typer.Argument(..., help="2つ目のKuzuDBディレクトリパス"),
    db1_query: str = typer.Argument(..., help="DB1に対するクエリ"),
    db2_query: str = typer.Argument(..., help="DB2に対するクエリ"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON形式で出力")
):
    """各DBに対して異なるクエリを実行"""
    
    try:
        with DualKuzuDB(db1_path, db2_path) as db:
            result = db.query_parallel(db1_query, db2_query)
            
            if json_output:
                output = {
                    "db1": {
                        "query": db1_query,
                        "columns": result.db1_result.columns if result.db1_result else [],
                        "rows": result.db1_result.rows if result.db1_result else [],
                        "error": result.db1_result.error if result.db1_result and result.db1_result.error else None
                    } if result.db1_result or (result.db1_result and result.db1_result.error) else None,
                    "db2": {
                        "query": db2_query,
                        "columns": result.db2_result.columns if result.db2_result else [],
                        "rows": result.db2_result.rows if result.db2_result else [],
                        "error": result.db2_result.error if result.db2_result and result.db2_result.error else None
                    } if result.db2_result or (result.db2_result and result.db2_result.error) else None
                }
                console.print_json(data=output)
            else:
                console.print(f"[bold]DB1 Query:[/bold] {db1_query}")
                console.print(f"[bold]DB2 Query:[/bold] {db2_query}\n")
                display_dual_result(result)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def info(
    db1_path: Path = typer.Argument(..., help="1つ目のKuzuDBディレクトリパス"),
    db2_path: Path = typer.Argument(..., help="2つ目のKuzuDBディレクトリパス")
):
    """2つのDBの情報を表示"""
    
    console.print("[bold]Database Information:[/bold]\n")
    console.print(f"DB1 Path: {db1_path}")
    console.print(f"DB2 Path: {db2_path}")
    
    # スキーマ情報を取得
    try:
        with DualKuzuDB(db1_path, db2_path) as db:
            # DB1のテーブル一覧
            result1 = db.query_single("db1", "CALL show_tables() RETURN *;")
            console.print("\n[bold]DB1 Tables:[/bold]")
            if result1.error:
                console.print(f"[red]Error: {result1.error}[/red]")
            else:
                display_query_result(result1)
            
            # DB2のテーブル一覧
            result2 = db.query_single("db2", "CALL show_tables() RETURN *;")
            console.print("\n[bold]DB2 Tables:[/bold]")
            if result2.error:
                console.print(f"[red]Error: {result2.error}[/red]")
            else:
                display_query_result(result2)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()