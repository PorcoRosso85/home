#!/usr/bin/env python3
import kuzu
from typing import Union, List, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class QuerySuccess:
    type: str = "success"
    results: List[Dict[str, Any]] = None
    message: str = ""


@dataclass
class QueryError:
    type: str = "error"
    message: str = ""


QueryResult = Union[QuerySuccess, QueryError]


def attach_sqlite_to_kuzu(conn: kuzu.Connection, sqlite_path: str, alias: str = "sqlite_db") -> Union[None, str]:
    try:
        # TODO: KuzuDB 0.10.0でINSTALL sqlite実行時にセグメンテーションフォルトが発生
        # 将来のバージョンで修正される予定
        
        # SQLite拡張機能をインストール
        try:
            conn.execute("INSTALL sqlite;")
        except:
            pass  # 既にインストール済みの場合
        
        # SQLite拡張機能をロード
        conn.execute("LOAD EXTENSION sqlite;")
        
        # SQLiteデータベースをアタッチ
        query = f"ATTACH '{sqlite_path}' AS {alias} (DBTYPE sqlite);"
        conn.execute(query)
        return None
    except Exception as e:
        return f"Failed to attach SQLite database: {e}"


def query_sqlite_from_kuzu(conn: kuzu.Connection, query: str) -> QueryResult:
    try:
        result = conn.execute(query)
        
        rows = []
        while result.has_next():
            rows.append(result.get_next())
        
        return QuerySuccess(
            results=rows,
            message=f"Query executed successfully, returned {len(rows)} rows"
        )
    except Exception as e:
        return QueryError(
            message=f"Query execution failed: {e}"
        )


def query_jsonl_logs_from_kuzu(conn: kuzu.Connection, sqlite_alias: str = "sqlite_db", limit: int = 100) -> QueryResult:
    query = f"""
    CALL TABLE {sqlite_alias}.jsonl_logs 
    ORDER BY created_at DESC 
    LIMIT {limit}
    RETURN *;
    """
    
    return query_sqlite_from_kuzu(conn, query)


def cross_query_example(conn: kuzu.Connection, sqlite_alias: str = "sqlite_db") -> QueryResult:
    query = f"""
    MATCH (n:Node)
    OPTIONAL CALL TABLE {sqlite_alias}.jsonl_logs 
    WHERE jsonl_logs.timestamp > '2024-01-01'
    RETURN n.id AS node_id, jsonl_logs.data AS log_data
    LIMIT 10;
    """
    
    return query_sqlite_from_kuzu(conn, query)


def detach_sqlite_from_kuzu(conn: kuzu.Connection, alias: str = "sqlite_db") -> Union[None, str]:
    try:
        query = f"DETACH {alias};"
        conn.execute(query)
        return None
    except Exception as e:
        return f"Failed to detach SQLite database: {e}"