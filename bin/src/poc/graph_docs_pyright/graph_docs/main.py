#!/usr/bin/env python3
"""graph_docs CLI - Dual KuzuDB Query Interface

I/O制御層：コマンドライン引数の処理とクエリ結果の表示
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from graph_docs.mod import DualKuzuDB, QueryResult, DualQueryResult
import graph_docs.cli_display as cli_display


def display_query_result(result: QueryResult) -> None:
    """単一のクエリ結果を表示"""
    cli_display.query_result(
        source=result.source,
        columns=result.columns,
        rows=result.rows,
        error=result.error
    )


def display_dual_result(result: DualQueryResult) -> None:
    """2つのDBの結果を表示"""
    if result.db1_result:
        display_query_result(result.db1_result)
    
    cli_display.newline()  # 空行
    
    if result.db2_result:
        display_query_result(result.db2_result)
    
    if result.combined:
        cli_display.combined_results(result.combined)


def cmd_query(args):
    """指定されたクエリを実行"""
    try:
        with DualKuzuDB(args.db1_path, args.db2_path) as db:
            if args.single:
                result = db.query_single(args.single, args.query_text)
                if args.json:
                    output = {
                        "source": result.source,
                        "columns": result.columns,
                        "rows": result.rows,
                        "error": result.error
                    }
                    cli_display.json_output(output)
                else:
                    display_query_result(result)
            else:
                result = db.query_both(args.query_text)
                if args.json:
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
                    cli_display.json_output(output)
                else:
                    display_dual_result(result)
    
    except Exception as e:
        cli_display.error(f"Error: {e}")
        sys.exit(1)


def cmd_parallel(args):
    """各DBに対して異なるクエリを実行"""
    try:
        with DualKuzuDB(args.db1_path, args.db2_path) as db:
            result = db.query_parallel(args.db1_query, args.db2_query)
            
            if args.json:
                output = {
                    "db1": {
                        "query": args.db1_query,
                        "columns": result.db1_result.columns if result.db1_result else [],
                        "rows": result.db1_result.rows if result.db1_result else [],
                        "error": result.db1_result.error if result.db1_result and result.db1_result.error else None
                    } if result.db1_result or (result.db1_result and result.db1_result.error) else None,
                    "db2": {
                        "query": args.db2_query,
                        "columns": result.db2_result.columns if result.db2_result else [],
                        "rows": result.db2_result.rows if result.db2_result else [],
                        "error": result.db2_result.error if result.db2_result and result.db2_result.error else None
                    } if result.db2_result or (result.db2_result and result.db2_result.error) else None
                }
                cli_display.json_output(output)
            else:
                cli_display.dual_query_info(args.db1_query, args.db2_query)
                display_dual_result(result)
    
    except Exception as e:
        cli_display.error(f"Error: {e}")
        sys.exit(1)


def cmd_info(args):
    """2つのDBの情報を表示"""
    cli_display.database_info(str(args.db1_path), str(args.db2_path))
    
    # スキーマ情報を取得
    try:
        with DualKuzuDB(args.db1_path, args.db2_path) as db:
            # DB1のテーブル一覧
            result1 = db.query_single("db1", "CALL show_tables() RETURN *;")
            cli_display.section_title("DB1 Tables")
            if result1.error:
                cli_display.error(f"Error: {result1.error}")
            else:
                display_query_result(result1)
            
            # DB2のテーブル一覧
            result2 = db.query_single("db2", "CALL show_tables() RETURN *;")
            cli_display.section_title("DB2 Tables")
            if result2.error:
                cli_display.error(f"Error: {result2.error}")
            else:
                display_query_result(result2)
    
    except Exception as e:
        cli_display.error(f"Error: {e}")
        sys.exit(1)


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="2つのKuzuDBに対するクエリインターフェース"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')
    
    # queryコマンド
    query_parser = subparsers.add_parser('query', help='指定されたクエリを実行')
    query_parser.add_argument('db1_path', type=Path, help='1つ目のKuzuDBディレクトリパス')
    query_parser.add_argument('db2_path', type=Path, help='2つ目のKuzuDBディレクトリパス')
    query_parser.add_argument('query_text', help='実行するCypherクエリ')
    query_parser.add_argument('-s', '--single', choices=['db1', 'db2'], 
                            help='単一のDBのみクエリ (db1 or db2)')
    query_parser.add_argument('-j', '--json', action='store_true', 
                            help='JSON形式で出力')
    query_parser.set_defaults(func=cmd_query)
    
    # parallelコマンド
    parallel_parser = subparsers.add_parser('parallel', help='各DBに対して異なるクエリを実行')
    parallel_parser.add_argument('db1_path', type=Path, help='1つ目のKuzuDBディレクトリパス')
    parallel_parser.add_argument('db2_path', type=Path, help='2つ目のKuzuDBディレクトリパス')
    parallel_parser.add_argument('db1_query', help='DB1に対するクエリ')
    parallel_parser.add_argument('db2_query', help='DB2に対するクエリ')
    parallel_parser.add_argument('-j', '--json', action='store_true', 
                               help='JSON形式で出力')
    parallel_parser.set_defaults(func=cmd_parallel)
    
    # infoコマンド
    info_parser = subparsers.add_parser('info', help='2つのDBの情報を表示')
    info_parser.add_argument('db1_path', type=Path, help='1つ目のKuzuDBディレクトリパス')
    info_parser.add_argument('db2_path', type=Path, help='2つ目のKuzuDBディレクトリパス')
    info_parser.set_defaults(func=cmd_info)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # コマンドの実行
    args.func(args)


if __name__ == "__main__":
    main()