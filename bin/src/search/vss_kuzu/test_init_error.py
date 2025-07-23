#!/usr/bin/env python3
"""
初期化エラー処理のテスト
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from vss_kuzu import VSSService


class TestInitializationError:
    """初期化エラー処理のテストクラス"""
    
    def test_init_with_invalid_db_path(self):
        """無効なデータベースパスでの初期化"""
        # 書き込み権限のないパスを指定
        invalid_path = "/root/no_permission_db"
        
        # VSSServiceを作成（エラーは内部で保持される）
        service = VSSService(db_path=invalid_path)
        
        # 操作を試みる
        result = service.index_documents([{"id": "test", "content": "test"}])
        
        # エラーが返されること
        assert isinstance(result, dict)
        assert result.get("ok") is False
        assert "error" in result
        assert "details" in result
    
    def test_init_error_propagates_to_search(self):
        """初期化エラーが検索操作にも伝播すること"""
        # 無効なパスでサービスを作成
        service = VSSService(db_path="/invalid/path/to/db")
        
        # 検索を試みる
        search_result = service.search({"query": "test"})
        
        # エラーが返されること
        assert search_result.get("ok") is False
        assert "error" in search_result
    
    def test_init_error_propagates_to_legacy_api(self):
        """初期化エラーがレガシーAPIにも伝播すること"""
        # 無効なパスでサービスを作成
        service = VSSService(db_path="/invalid/path/to/db")
        
        # add_documentを試みる
        add_result = service.add_document("doc1", "content")
        assert add_result.get("ok") is False
        
        # search_similarを試みる（空リストが返される）
        search_results = service.search_similar("query")
        assert isinstance(search_results, list)
        assert len(search_results) == 0
    
    @patch('vss_kuzu.application.check_vector_extension')
    def test_vector_extension_not_available(self, mock_check_vector):
        """VECTOR拡張が利用できない場合のエラー処理"""
        # VECTOR拡張が利用できないことをシミュレート
        mock_check_vector.return_value = (False, {
            "ok": False,
            "error": "VECTOR extension not available",
            "details": {
                "extension": "VECTOR",
                "install_command": "INSTALL VECTOR;"
            }
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = VSSService(db_path=tmpdir)
            
            # 操作を試みる
            result = service.index_documents([{"id": "test", "content": "test"}])
            
            # エラーが返されること
            assert result.get("ok") is False
            assert "VECTOR extension" in result.get("error", "")
    
    @patch('vss_kuzu.application.initialize_vector_schema')
    def test_schema_initialization_failure(self, mock_init_schema):
        """スキーマ初期化失敗時のエラー処理"""
        # スキーマ初期化の失敗をシミュレート
        mock_init_schema.return_value = (False, {
            "ok": False,
            "error": "Failed to create table",
            "details": {
                "reason": "Permission denied"
            }
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = VSSService(db_path=tmpdir)
            
            # 操作を試みる
            result = service.search({"query": "test"})
            
            # エラーが返されること
            assert result.get("ok") is False
    
    def test_successful_initialization_allows_operations(self):
        """正常な初期化後は操作が可能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = VSSService(db_path=tmpdir)
            
            # 正常に初期化された場合、操作が可能
            # （VECTOR拡張の有無により結果は異なる）
            result = service.index_documents([{"id": "test", "content": "test"}])
            
            # 少なくともエラー形式は一貫している
            assert isinstance(result, dict)
            assert "ok" in result
    
    def test_in_memory_database_initialization(self):
        """インメモリデータベースでの初期化"""
        # インメモリデータベースを使用
        service = VSSService(in_memory=True)
        
        # 操作を試みる
        result = service.index_documents([{"id": "test", "content": "test"}])
        
        # 結果の形式を確認
        assert isinstance(result, dict)
        assert "ok" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])