#!/usr/bin/env python3
"""
JSONL → SQLite 統合テスト
実際に動作確認可能なテストのみを実装
"""
import pytest
import sqlite3
import json
import tempfile
import subprocess
import sys
from pathlib import Path
from datetime import datetime

from jsonlLogger import (
    create_jsonl_table,
    insert_jsonl_line,
    insert_jsonl_batch,
    query_jsonl_logs,
    InsertSuccess,
    InsertError
)


class TestJsonlToSqlite:
    """JSONL → SQLite の実動作テスト"""
    
    def test_basic_workflow(self):
        """基本的なワークフローの動作確認"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # データベース接続とテーブル作成
            conn = sqlite3.connect(db_path)
            error = create_jsonl_table(conn)
            assert error is None
            
            # JSONLデータの挿入
            test_data = {
                "timestamp": "2024-01-01T10:00:00",
                "event": "test_event",
                "data": {"key": "value"}
            }
            result = insert_jsonl_line(conn, json.dumps(test_data))
            assert result.type == "success"
            
            # データの取得
            records = query_jsonl_logs(conn, limit=10)
            assert len(records) == 1
            assert records[0]['data']['event'] == "test_event"
            
            conn.close()
        finally:
            Path(db_path).unlink()
    
    def test_claude_stream_format(self):
        """Claude stream-json形式の処理"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = sqlite3.connect(db_path)
            create_jsonl_table(conn)
            
            # Claude stream形式のデータ
            stream_events = [
                {"type": "content_block_start", "index": 0},
                {"type": "content_block_delta", "delta": {"text": "Hello"}},
                {"type": "content_block_delta", "delta": {"text": " world"}},
                {"type": "content_block_stop", "index": 0}
            ]
            
            # 各イベントに手動でタイムスタンプを追加して挿入
            for event in stream_events:
                event["timestamp"] = datetime.now().isoformat()
                result = insert_jsonl_line(conn, json.dumps(event))
                assert result.type == "success"
            
            # 取得と確認
            records = query_jsonl_logs(conn)
            assert len(records) == 4
            
            # content_block_deltaイベントのテキストを結合
            text_parts = []
            for record in reversed(records):  # 古い順に処理
                if record['data']['type'] == 'content_block_delta':
                    text_parts.append(record['data']['delta']['text'])
            
            assert ''.join(text_parts) == "Hello world"
            
            conn.close()
        finally:
            Path(db_path).unlink()
    
    def test_capture_script(self):
        """claudeStreamCapture.pyスクリプトの動作確認"""
        test_stream = [
            '{"type": "message_start", "message": {"id": "test"}}',
            '{"type": "content_block_delta", "delta": {"text": "Test"}}',
            '{"type": "message_stop"}'
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            # スクリプトを実行
            process = subprocess.Popen(
                [sys.executable, "claudeStreamCapture.py", "--db", db_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input='\n'.join(test_stream))
            assert process.returncode == 0
            assert "Captured 3 lines" in stderr
            
            # データベースの確認
            conn = sqlite3.connect(db_path)
            records = query_jsonl_logs(conn)
            conn.close()
            
            assert len(records) == 3
            types = [r['data']['type'] for r in reversed(records)]
            assert types == ['message_start', 'content_block_delta', 'message_stop']
            
        finally:
            Path(db_path).unlink()
    
    def test_error_handling(self):
        """エラー処理の動作確認"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            conn = sqlite3.connect(db_path)
            create_jsonl_table(conn)
            
            # 不正なJSONの処理
            invalid_json = '{"invalid": json}'
            result = insert_jsonl_line(conn, invalid_json)
            assert result.type == "error"
            assert "Invalid JSON" in result.message
            
            # 正常なデータと不正なデータの混在
            mixed_data = [
                '{"valid": true}',
                '{"invalid": json}',
                '{"also_valid": true}'
            ]
            
            result = insert_jsonl_batch(conn, mixed_data)
            assert result.type == "error"
            assert "partially failed" in result.message
            assert "Inserted: 2" in result.message
            
            conn.close()
        finally:
            Path(db_path).unlink()
    
    def test_persistence(self):
        """データの永続性確認"""
        db_path = "/tmp/test_persistence.db"
        
        try:
            # 最初の接続でデータを挿入
            conn1 = sqlite3.connect(db_path)
            create_jsonl_table(conn1)
            
            test_data = {"message": "persistent data", "timestamp": datetime.now().isoformat()}
            insert_jsonl_line(conn1, json.dumps(test_data))
            conn1.close()
            
            # 新しい接続でデータを取得
            conn2 = sqlite3.connect(db_path)
            records = query_jsonl_logs(conn2)
            conn2.close()
            
            assert len(records) == 1
            assert records[0]['data']['message'] == "persistent data"
            
        finally:
            if Path(db_path).exists():
                Path(db_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])