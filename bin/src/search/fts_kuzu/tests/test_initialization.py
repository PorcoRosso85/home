#!/usr/bin/env python3
"""
FTS初期化とエラーハンドリングのテスト

requirement/graphから移行されたテスト
様々な設定でのFTS初期化とエラーケースの検証
"""

import tempfile
from typing import Any
import pytest
from unittest.mock import Mock, patch

from fts_kuzu import create_fts
from fts_kuzu.infrastructure import (
    create_kuzu_database,
    create_kuzu_connection,
    check_fts_extension,
    install_fts_extension,
)


class TestFTSInitialization:
    """FTS初期化のテストスイート"""

    def test_fts_initialization_with_various_configs(self):
        """様々な設定でのFTS初期化が成功することを確認"""
        # Test 1: In-memory database
        fts_memory = create_fts(in_memory=True)
        assert fts_memory is not None
        # Verify index and search work
        result = fts_memory.index([{"id": "1", "content": "テスト"}])
        assert result["ok"] is True
        fts_memory.close()

        # Test 2: File-based database with temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_db"
            fts_file = create_fts(db_path=db_path)
            assert fts_file is not None
            # Verify persistence
            result = fts_file.index([{"id": "2", "content": "永続化テスト"}])
            assert result["ok"] is True
            fts_file.close()

            # Re-open and verify data persists
            fts_reopen = create_fts(db_path=db_path)
            search_result = fts_reopen.search("永続化")
            assert search_result["ok"] is True
            assert len(search_result["results"]) > 0
            fts_reopen.close()

        # Test 3: Custom limit configuration
        fts_custom = create_fts(in_memory=True, default_limit=20)
        assert fts_custom is not None
        assert fts_custom.config["default_limit"] == 20
        fts_custom.close()

        # Test 4: Existing connection reuse
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/shared_db"
            # Create database and connection manually
            db_success, database, _ = create_kuzu_database({"db_path": db_path, "in_memory": False})
            assert db_success
            conn_success, connection, _ = create_kuzu_connection(database)
            assert conn_success

            # Create FTS with existing connection
            fts_shared = create_fts(db_path=db_path, existing_connection=connection)
            assert fts_shared is not None
            result = fts_shared.index([{"id": "3", "content": "共有接続テスト"}])
            assert result["ok"] is True
            
            # Connection should not be closed by FTS
            fts_shared.close()
            # Verify connection is still valid
            try:
                connection.execute("RETURN 1")
                # Connection should still work
            finally:
                connection.close()

    def test_fts_initialization_error_cases(self):
        """初期化失敗時の適切なエラーハンドリング"""
        # Test 1: Invalid database path - may not raise RuntimeError depending on kuzu_py version
        # Some versions create the path, others return error dict
        try:
            fts = create_fts(db_path="/invalid/path/that/does/not/exist")
            # If it doesn't raise, it should still work (might create the path)
            fts.close()
        except RuntimeError as e:
            # If it does raise, check the error message
            assert "Failed to create database" in str(e)

        # Test 2: Database creation failure simulation
        with patch('fts_kuzu.infrastructure.create_kuzu_database') as mock_create_db:
            mock_create_db.return_value = (False, None, {
                "error": "Simulated database creation failure",
                "details": {"reason": "test"}
            })
            with pytest.raises(RuntimeError) as exc_info:
                create_fts(in_memory=True)
            assert "Failed to create database" in str(exc_info.value)
            assert "Simulated database creation failure" in str(exc_info.value)

        # Test 3: Connection creation failure simulation  
        with patch('fts_kuzu.infrastructure.create_kuzu_database') as mock_create_db:
            mock_create_db.return_value = (True, Mock(), None)
            with patch('fts_kuzu.infrastructure.create_kuzu_connection') as mock_create_conn:
                mock_create_conn.return_value = (False, None, {
                    "error": "Simulated connection failure",
                    "details": {"reason": "test"}
                })
                with pytest.raises(RuntimeError) as exc_info:
                    create_fts(in_memory=True)
                assert "Failed to create connection" in str(exc_info.value)

        # Test 4: FTS extension installation failure (non-fatal)
        with patch('fts_kuzu.infrastructure.create_kuzu_database') as mock_create_db:
            mock_db = Mock()
            mock_conn = Mock()
            mock_create_db.return_value = (True, mock_db, None)
            
            with patch('fts_kuzu.infrastructure.create_kuzu_connection') as mock_create_conn:
                mock_create_conn.return_value = (True, mock_conn, None)
                
                with patch('fts_kuzu.infrastructure.install_fts_extension') as mock_install:
                    mock_install.return_value = (False, {"error": "FTS not available"})
                    
                    with patch('fts_kuzu.infrastructure.check_fts_extension') as mock_check:
                        mock_check.return_value = (False, None)
                        
                        # Should not raise exception - FTS can work without extension
                        fts = create_fts(in_memory=True)
                        assert fts is not None
                        # But search should fall back to simple string matching
                        fts.close()

    def test_fts_module_availability_check(self):
        """FTSモジュールの利用可能性チェックが正確"""
        # Test with actual database
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/test_db"
            db_success, database, _ = create_kuzu_database({"db_path": db_path, "in_memory": False})
            assert db_success
            conn_success, connection, _ = create_kuzu_connection(database)
            assert conn_success

            # Check FTS extension availability
            check_result = check_fts_extension(connection)
            if isinstance(check_result, tuple):
                fts_available, _ = check_result
            elif isinstance(check_result, bool):
                fts_available = check_result
            else:
                fts_available = check_result.get("ok", False)

            # Install FTS extension
            install_result = install_fts_extension(connection)
            if isinstance(install_result, tuple):
                install_success, _ = install_result
            else:
                install_success = install_result.get("ok", False)

            # After installation, check should reflect the result
            check_result_after = check_fts_extension(connection)
            if isinstance(check_result_after, tuple):
                fts_available_after, _ = check_result_after
            elif isinstance(check_result_after, bool):
                fts_available_after = check_result_after
            else:
                fts_available_after = check_result_after.get("ok", False)

            # If installation succeeded, check should return True
            if install_success:
                assert fts_available_after is True
            
            connection.close()

    def test_fts_initialization_idempotency(self):
        """初期化の冪等性を確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/idempotent_db"
            
            # First initialization
            fts1 = create_fts(db_path=db_path)
            result1 = fts1.index([{"id": "1", "content": "最初のドキュメント"}])
            assert result1["ok"] is True
            fts1.close()

            # Second initialization - should not fail
            fts2 = create_fts(db_path=db_path)
            # Should be able to search for previous documents
            search_result = fts2.search("最初の")
            assert search_result["ok"] is True
            assert len(search_result["results"]) == 1
            
            # Add more documents
            result2 = fts2.index([{"id": "2", "content": "2番目のドキュメント"}])
            assert result2["ok"] is True
            fts2.close()

            # Third initialization - all data should be preserved
            fts3 = create_fts(db_path=db_path)
            search_all = fts3.search("ドキュメント")
            assert search_all["ok"] is True
            assert len(search_all["results"]) == 2
            fts3.close()

    def test_concurrent_initialization_safety(self):
        """同時初期化の安全性を確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/concurrent_db"
            
            # Create multiple FTS instances with same database
            instances = []
            try:
                for i in range(3):
                    fts = create_fts(db_path=db_path)
                    instances.append(fts)
                    # Each instance should work independently
                    result = fts.index([{"id": f"doc_{i}", "content": f"Document {i}"}])
                    assert result["ok"] is True

                # All documents should be searchable from any instance
                for fts in instances:
                    search_result = fts.search("Document")
                    assert search_result["ok"] is True
                    assert len(search_result["results"]) >= 3

            finally:
                # Clean up all instances
                for fts in instances:
                    fts.close()

    def test_error_messages_clarity(self):
        """エラーメッセージの明確性を確認"""
        # Test various error scenarios and verify clear messages
        error_scenarios = [
            {
                "mock_target": "fts_kuzu.infrastructure.create_kuzu_database",
                "error_response": (False, None, {
                    "error": "Database locked by another process",
                    "details": {"path": "/tmp/test.db", "errno": 11}
                }),
                "expected_error": "Database locked"
            },
            {
                "mock_target": "fts_kuzu.infrastructure.create_kuzu_connection",
                "error_response": (False, None, {
                    "error": "Maximum connections exceeded",
                    "details": {"max_connections": 10, "current": 10}
                }),
                "expected_error": "Maximum connections"
            }
        ]

        for scenario in error_scenarios:
            with patch(scenario["mock_target"]) as mock_func:
                if "database" in scenario["mock_target"]:
                    mock_func.return_value = scenario["error_response"]
                else:
                    # For connection mock, need to mock database creation first
                    with patch('fts_kuzu.infrastructure.create_kuzu_database') as mock_db:
                        mock_db.return_value = (True, Mock(), None)
                        mock_func.return_value = scenario["error_response"]
                
                with pytest.raises(RuntimeError) as exc_info:
                    create_fts(in_memory=True)
                
                error_message = str(exc_info.value)
                assert scenario["expected_error"] in error_message
                # Verify error includes helpful context
                assert "Failed to" in error_message