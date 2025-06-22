#!/usr/bin/env python3
import sqlite3
import sys
import json
import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from log.sqlite.jsonlLogger import create_jsonl_table, insert_jsonl_line


def capture_claude_stream(db_path: str = "/tmp/claude_stream.db"):
    conn = sqlite3.connect(db_path)
    
    error = create_jsonl_table(conn)
    if error:
        print(f"Failed to create table: {error}", file=sys.stderr)
        return 1
    
    print(f"Capturing Claude stream-json output to {db_path}...", file=sys.stderr)
    print("Reading from stdin (pipe claude output here)...", file=sys.stderr)
    
    line_count = 0
    error_count = 0
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                data["captured_at"] = datetime.datetime.now().isoformat()
                
                if "timestamp" not in data:
                    data["timestamp"] = data["captured_at"]
                
                enriched_line = json.dumps(data)
                result = insert_jsonl_line(conn, enriched_line)
                
                if result.type == "success":
                    line_count += 1
                else:
                    error_count += 1
                    print(f"Insert error: {result.message}", file=sys.stderr)
                
            except json.JSONDecodeError as e:
                error_count += 1
                print(f"Invalid JSON: {e}", file=sys.stderr)
                
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
    
    finally:
        conn.close()
        print(f"\nCaptured {line_count} lines ({error_count} errors) to {db_path}", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Capture Claude stream-json output to SQLite")
    parser.add_argument(
        "--db", 
        default="/tmp/claude_stream.db",
        help="Path to SQLite database (default: /tmp/claude_stream.db)"
    )
    
    args = parser.parse_args()
    
    sys.exit(capture_claude_stream(args.db))