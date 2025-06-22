#!/usr/bin/env python3
import sqlite3
import json
from typing import Union, List, Dict, Any
from dataclasses import dataclass
import datetime
from pathlib import Path


@dataclass
class InsertSuccess:
    type: str = "success"
    inserted_count: int = 0
    message: str = ""


@dataclass
class InsertError:
    type: str = "error"
    message: str = ""


InsertResult = Union[InsertSuccess, InsertError]


def create_jsonl_table(conn: sqlite3.Connection) -> Union[None, str]:
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jsonl_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON jsonl_logs(timestamp)
        """)
        conn.commit()
        return None
    except Exception as e:
        return f"Table creation failed: {e}"


def insert_jsonl_line(conn: sqlite3.Connection, line: str) -> InsertResult:
    try:
        data = json.loads(line.strip())
        timestamp = data.get("timestamp", datetime.datetime.now().isoformat())
        
        conn.execute(
            "INSERT INTO jsonl_logs (timestamp, data) VALUES (?, ?)",
            (timestamp, line.strip())
        )
        conn.commit()
        
        return InsertSuccess(
            inserted_count=1,
            message="Successfully inserted JSONL line"
        )
    except json.JSONDecodeError as e:
        return InsertError(
            message=f"Invalid JSON: {e}"
        )
    except Exception as e:
        return InsertError(
            message=f"Insert failed: {e}"
        )


def insert_jsonl_batch(conn: sqlite3.Connection, lines: List[str]) -> InsertResult:
    successful_inserts = 0
    errors = []
    
    for line in lines:
        if not line.strip():
            continue
            
        result = insert_jsonl_line(conn, line)
        
        if result.type == "success":
            successful_inserts += 1
        else:
            errors.append(result.message)
    
    if errors:
        return InsertError(
            message=f"Batch insert partially failed. Inserted: {successful_inserts}, Errors: {'; '.join(errors)}"
        )
    
    return InsertSuccess(
        inserted_count=successful_inserts,
        message=f"Successfully inserted {successful_inserts} records"
    )


def query_jsonl_logs(conn: sqlite3.Connection, limit: int = 100) -> Union[List[Dict[str, Any]], str]:
    try:
        cursor = conn.execute(
            "SELECT id, timestamp, data, created_at FROM jsonl_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        
        results = []
        for row in cursor:
            results.append({
                "id": row[0],
                "timestamp": row[1],
                "data": json.loads(row[2]),
                "created_at": row[3]
            })
        
        return results
    except Exception as e:
        return f"Query failed: {e}"