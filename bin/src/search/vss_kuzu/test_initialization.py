#!/usr/bin/env python3
"""
初期化エラーハンドリングの統合テスト
規約に従い、モックを使わず実際のKuzuDBで動作をテスト
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from vss_kuzu import VSSService


class TestInitializationErrors:
    """初期化エラーハンドリングのテストクラス"""
    
    def test_service_with_valid_database_handles_vector_extension(self):
        """データベースでVECTOR拡張の状態を適切に処理すること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = VSSService(db_path=tmpdir, in_memory=False)
            
            # 初期化が完了していること（成功または適切なエラー）
            if service._is_initialized:
                # VECTOR拡張が利用可能な場合
                assert service._init_error is None
                
                # 正常に動作することを確認
                result = service.index_documents([
                    {"id": "doc1", "content": "test document"}
                ])
                assert result["ok"] is True
            else:
                # VECTOR拡張が利用できない場合
                assert service._init_error is not None
                assert service._init_error["ok"] is False
                assert "error" in service._init_error
                
                # 操作を試みるとエラーが返ること
                result = service.index_documents([
                    {"id": "doc1", "content": "test document"}
                ])
                assert result["ok"] is False
    
    def test_service_with_readonly_path_returns_error(self):
        """読み取り専用パスでエラーが適切に処理されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # ディレクトリを読み取り専用にする
            Path(tmpdir).chmod(0o444)
            
            try:
                service = VSSService(db_path=f"{tmpdir}/readonly_db", in_memory=False)
                
                # 初期化エラーが記録されていること
                assert service._is_initialized is False
                assert service._init_error is not None
                assert service._init_error["ok"] is False
                assert "error" in service._init_error
                
                # 操作を試みるとエラーが返ること
                result = service.index_documents([
                    {"id": "doc1", "content": "test"}
                ])
                assert result["ok"] is False
                assert "error" in result
                
            finally:
                # 権限を戻す
                Path(tmpdir).chmod(0o755)
    
    def test_service_with_invalid_path_characters_returns_error(self):
        """無効なパス文字でエラーが適切に処理されること"""
        # NUL文字を含む無効なパス
        invalid_path = "/tmp/test\x00db"
        
        service = VSSService(db_path=invalid_path, in_memory=False)
        
        # 初期化エラーが記録されていること
        assert service._is_initialized is False
        assert service._init_error is not None
        
        # 操作を試みるとエラーが返ること
        result = service.search({"query": "test"})
        assert result["ok"] is False
    
    def test_service_operations_fail_gracefully_when_not_initialized(self):
        """初期化失敗時にすべての操作が適切にエラーを返すこと"""
        # 無効なパスでサービスを作成
        service = VSSService(db_path="/nonexistent/path/\x00/db", in_memory=False)
        
        # index_documents
        index_result = service.index_documents([
            {"id": "doc1", "content": "test"}
        ])
        assert index_result["ok"] is False
        assert "error" in index_result
        assert "details" in index_result
        
        # search
        search_result = service.search({"query": "test"})
        assert search_result["ok"] is False
        assert "error" in search_result
        assert "details" in search_result
        
        # Legacy API - add_document
        add_result = service.add_document("doc1", "test content")
        assert add_result["ok"] is False
        assert "error" in add_result
        
        # Legacy API - search_similar
        similar_results = service.search_similar("test query")
        assert similar_results == []  # Legacy APIは空リストを返す
    
    def test_in_memory_database_handles_vector_extension(self):
        """インメモリデータベースでVECTOR拡張の状態を適切に処理すること"""
        service = VSSService(db_path=":memory:", in_memory=True)
        
        # 初期化が完了していること（成功または適切なエラー）
        if service._is_initialized:
            # VECTOR拡張が利用可能な場合
            assert service._init_error is None
            
            # 正常に動作することを確認
            result = service.index_documents([
                {"id": "doc1", "content": "in-memory test"}
            ])
            assert result["ok"] is True
            assert result["indexed_count"] == 1
        else:
            # VECTOR拡張が利用できない場合
            assert service._init_error is not None
            assert service._init_error["ok"] is False
            assert "error" in service._init_error
    
    def test_initialization_error_details_contain_useful_information(self):
        """初期化エラーの詳細に有用な情報が含まれること"""
        # 無効なパスでサービスを作成
        invalid_path = "/root/no_permission_db"
        service = VSSService(db_path=invalid_path, in_memory=False)
        
        if service._init_error:
            # エラーに必要な情報が含まれていること
            assert service._init_error["ok"] is False
            assert "error" in service._init_error
            assert "details" in service._init_error
            assert isinstance(service._init_error["details"], dict)
            
            # パス情報が含まれていること（デバッグに有用）
            error_str = str(service._init_error)
            assert "db_path" in error_str or invalid_path in error_str
    
    def test_multiple_services_handle_vector_extension_consistently(self):
        """複数のサービスインスタンスがVECTOR拡張を一貫して処理すること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 最初のサービス
            service1 = VSSService(db_path=tmpdir, in_memory=False)
            
            # 2番目のサービスで同じデータベースにアクセス
            service2 = VSSService(db_path=tmpdir, in_memory=False)
            
            # 両サービスの初期化状態が一致すること
            assert service1._is_initialized == service2._is_initialized
            
            if service1._is_initialized:
                # 両方とも初期化成功
                assert service1._init_error is None
                assert service2._init_error is None
                
                # データ操作が可能
                result1 = service1.index_documents([
                    {"id": "shared1", "content": "shared document"}
                ])
                assert result1["ok"] is True
                
                result2 = service2.index_documents([
                    {"id": "shared2", "content": "another shared document"}
                ])
                assert result2["ok"] is True
            else:
                # 両方とも初期化失敗（VECTOR拡張なし）
                assert service1._init_error is not None
                assert service2._init_error is not None
                assert service1._init_error["ok"] is False
                assert service2._init_error["ok"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])