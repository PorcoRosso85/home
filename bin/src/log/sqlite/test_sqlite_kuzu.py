#!/usr/bin/env python3
"""
SQLite → KuzuDB 統合テスト
TODO: 現在セグメンテーションフォルトが発生するため、KuzuDBの安定版待ち
実行方法: export LD_LIBRARY_PATH="/nix/store/4gk773fqcsv4fh2rfkhs9bgfih86fdq8-gcc-13.3.0-lib/lib/":$LD_LIBRARY_PATH && uv run pytest test_sqlite_kuzu.py -v
"""
import pytest
import sqlite3
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# TODO: libstdc++.so.6の問題でインポートエラーが発生
# 環境変数LD_LIBRARY_PATHの設定が必要
try:
    import kuzu
    KUZU_AVAILABLE = True
except ImportError:
    KUZU_AVAILABLE = False
    kuzu = None

from jsonlLogger import create_jsonl_table, insert_jsonl_batch

if KUZU_AVAILABLE:
    from kuzuIntegration import (
        attach_sqlite_to_kuzu,
        query_sqlite_from_kuzu,
        query_jsonl_logs_from_kuzu,
        detach_sqlite_from_kuzu,
        QuerySuccess,
        QueryError
    )


# TODO: KuzuDBのSQLite拡張機能が不安定でセグフォが発生
# 以下のテストは将来のバージョンで動作予定
@pytest.mark.skipif(not KUZU_AVAILABLE, reason="KuzuDB not available (libstdc++ issue)")
@pytest.mark.skip(reason="KuzuDB SQLite extension causes segmentation fault")
class TestSqliteToKuzu:
    """SQLite → KuzuDB の実動作テスト"""
    
    def test_basic_attach_detach(self):
        """基本的なアタッチ・デタッチの動作確認"""
        # SQLiteデータベースの準備
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            sqlite_path = tmp.name
        
        # KuzuDBの準備
        with tempfile.TemporaryDirectory() as tmpdir:
            kuzu_path = Path(tmpdir) / "test_kuzu"
            
            try:
                # SQLiteにテストデータを準備
                sqlite_conn = sqlite3.connect(sqlite_path)
                create_jsonl_table(sqlite_conn)
                
                test_data = [
                    '{"event": "start", "timestamp": "2024-01-01T10:00:00"}',
                    '{"event": "process", "timestamp": "2024-01-01T10:01:00"}',
                    '{"event": "end", "timestamp": "2024-01-01T10:02:00"}'
                ]
                result = insert_jsonl_batch(sqlite_conn, test_data)
                assert result.type == "success"
                sqlite_conn.close()
                
                # KuzuDBセットアップ
                kuzu_db = kuzu.Database(str(kuzu_path))
                kuzu_conn = kuzu.Connection(kuzu_db)
                
                # TODO: INSTALL sqlite; でセグフォが発生
                # アタッチ
                error = attach_sqlite_to_kuzu(kuzu_conn, sqlite_path, "test_logs")
                assert error is None
                
                # クエリ実行
                result = query_jsonl_logs_from_kuzu(kuzu_conn, "test_logs", limit=10)
                assert result.type == "success"
                assert len(result.results) == 3
                
                # デタッチ
                error = detach_sqlite_from_kuzu(kuzu_conn, "test_logs")
                assert error is None
                
                kuzu_conn.close()
                
            finally:
                Path(sqlite_path).unlink()
    
    def test_query_sqlite_data(self):
        """SQLiteデータのクエリ動作確認"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            sqlite_path = tmp.name
        
        with tempfile.TemporaryDirectory() as tmpdir:
            kuzu_path = Path(tmpdir) / "test_kuzu"
            
            try:
                # SQLiteにClaude形式のデータを準備
                sqlite_conn = sqlite3.connect(sqlite_path)
                create_jsonl_table(sqlite_conn)
                
                claude_data = [
                    '{"type": "message_start", "timestamp": "2024-01-01T10:00:00"}',
                    '{"type": "content_block_delta", "delta": {"text": "Hello"}, "timestamp": "2024-01-01T10:00:01"}',
                    '{"type": "content_block_delta", "delta": {"text": " KuzuDB"}, "timestamp": "2024-01-01T10:00:02"}',
                    '{"type": "message_stop", "timestamp": "2024-01-01T10:00:03"}'
                ]
                insert_jsonl_batch(sqlite_conn, claude_data)
                sqlite_conn.close()
                
                # KuzuDB接続
                kuzu_db = kuzu.Database(str(kuzu_path))
                kuzu_conn = kuzu.Connection(kuzu_db)
                
                # SQLiteアタッチ
                attach_sqlite_to_kuzu(kuzu_conn, sqlite_path, "claude_logs")
                
                # カスタムクエリ実行
                query = """
                CALL TABLE claude_logs.jsonl_logs
                WHERE claude_logs.jsonl_logs.data LIKE '%content_block_delta%'
                RETURN claude_logs.jsonl_logs.id, claude_logs.jsonl_logs.data;
                """
                
                result = query_sqlite_from_kuzu(kuzu_conn, query)
                assert result.type == "success"
                assert len(result.results) == 2  # content_block_deltaイベントのみ
                
                # クリーンアップ
                detach_sqlite_from_kuzu(kuzu_conn, "claude_logs")
                kuzu_conn.close()
                
            finally:
                Path(sqlite_path).unlink()
    
    def test_error_handling(self):
        """エラー処理の動作確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kuzu_path = Path(tmpdir) / "test_kuzu"
            kuzu_db = kuzu.Database(str(kuzu_path))
            kuzu_conn = kuzu.Connection(kuzu_db)
            
            try:
                # 存在しないファイルのアタッチ
                error = attach_sqlite_to_kuzu(kuzu_conn, "/nonexistent/file.db", "test")
                assert error is not None
                assert "Failed to attach" in error
                
                # 無効なクエリ
                result = query_sqlite_from_kuzu(kuzu_conn, "INVALID QUERY")
                assert result.type == "error"
                
                # 存在しないエイリアスのデタッチ
                error = detach_sqlite_from_kuzu(kuzu_conn, "nonexistent")
                assert error is not None
                
            finally:
                kuzu_conn.close()
    
    def test_performance(self):
        """パフォーマンステスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            sqlite_path = tmp.name
        
        with tempfile.TemporaryDirectory() as tmpdir:
            kuzu_path = Path(tmpdir) / "test_kuzu"
            
            try:
                # 大量データの準備
                sqlite_conn = sqlite3.connect(sqlite_path)
                create_jsonl_table(sqlite_conn)
                
                # 1000件のデータを生成
                large_data = []
                for i in range(1000):
                    data = {
                        "id": i,
                        "timestamp": datetime.now().isoformat(),
                        "event": f"event_{i % 10}",
                        "value": i * 100
                    }
                    large_data.append(json.dumps(data))
                
                insert_jsonl_batch(sqlite_conn, large_data)
                sqlite_conn.close()
                
                # KuzuDBでクエリ実行
                kuzu_db = kuzu.Database(str(kuzu_path))
                kuzu_conn = kuzu.Connection(kuzu_db)
                
                attach_sqlite_to_kuzu(kuzu_conn, sqlite_path, "perf_logs")
                
                # 集計クエリ
                import time
                start_time = time.time()
                
                query = """
                CALL TABLE perf_logs.jsonl_logs
                RETURN COUNT(*) AS total_count;
                """
                
                result = query_sqlite_from_kuzu(kuzu_conn, query)
                query_time = time.time() - start_time
                
                assert result.type == "success"
                assert query_time < 1.0  # 1秒以内
                
                detach_sqlite_from_kuzu(kuzu_conn, "perf_logs")
                kuzu_conn.close()
                
            finally:
                Path(sqlite_path).unlink()


if __name__ == "__main__":
    # TODO: セグフォ回避のため、個別実行時もスキップ
    print("WARNING: KuzuDB SQLite extension causes segmentation fault")
    print("Skipping all tests. Remove @pytest.mark.skip to test after KuzuDB fix.")
    pytest.main([__file__, "-v", "-k", "not TestSqliteToKuzu"])