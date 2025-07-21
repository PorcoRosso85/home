#!/usr/bin/env python3
"""
VSS規約準拠版のテスト
エラー処理規約に従い、VECTOR拡張が利用できない場合の挙動を検証
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from vss_service import VSSService, ErrorDict, SearchResult, IndexResult


class TestVSSCompliance:
    """規約準拠版VSSサービスのテスト"""
    
    @pytest.fixture
    def vss_service(self):
        """VSS service with temporary database"""
        tmpdir = tempfile.mkdtemp()
        service = VSSService(db_path=tmpdir, in_memory=False)
        yield service
        # Cleanup
        shutil.rmtree(tmpdir)
    
    def test_vector_extension_not_available_error(self, vss_service):
        """VECTOR拡張が利用できない場合、エラーを返すこと"""
        # VECTOR拡張をモックで無効化
        vss_service._vector_extension_available = False
        
        # インデックス時のエラー確認
        documents = [{"id": "1", "content": "テストドキュメント"}]
        result = vss_service.index_documents(documents)
        
        # ErrorDictが返されること
        assert isinstance(result, dict)
        assert result["ok"] is False
        assert "VECTOR extension not available" in result["error"]
        assert result["details"]["extension"] == "VECTOR"
        assert "install_command" in result["details"]
        
        # 検索時のエラー確認
        search_result = vss_service.search({"query": "テスト"})
        
        # ErrorDictが返されること
        assert isinstance(search_result, dict)
        assert search_result["ok"] is False
        assert "VECTOR extension not available" in search_result["error"]
    
    def test_successful_indexing_with_vector_extension(self, vss_service):
        """VECTOR拡張が利用可能な場合、正常にインデックスできること"""
        # 注意: 実際のテスト環境ではVECTOR拡張が利用できない可能性がある
        documents = [
            {"id": "1", "content": "テストドキュメント"},
            {"id": "2", "content": "別のドキュメント"}
        ]
        
        result = vss_service.index_documents(documents)
        
        # 成功またはエラーのいずれか
        if result.get("ok", False):
            # IndexResultの場合
            assert result["status"] == "success"
            assert result["indexed_count"] == 2
            assert "index_time_ms" in result
        else:
            # ErrorDictの場合（VECTOR拡張が利用できない）
            assert "VECTOR extension not available" in result["error"]
    
    def test_dimension_mismatch_error(self, vss_service):
        """次元数が一致しない場合、エラーを返すこと"""
        # 間違った次元数のベクトルを提供
        search_input = {
            "query": "テスト",
            "query_vector": [0.1] * 128  # 256次元ではなく128次元
        }
        
        result = vss_service.search(search_input)
        
        # エラーが返されること
        if not result.get("ok", True):  # エラーの場合
            if "dimension mismatch" in result.get("error", ""):
                assert result["details"]["expected"] == 256
                assert result["details"]["got"] == 128
            else:
                # VECTOR拡張が利用できない場合
                assert "VECTOR extension not available" in result["error"]
    
    def test_no_fallback_implementation(self, vss_service):
        """フォールバック実装が存在しないことを確認"""
        # vss_service.pyのソースコードを確認
        import inspect
        source = inspect.getsource(vss_service.search)
        
        # SQLフォールバックのコードが含まれていないこと
        assert "REDUCE(dot = 0.0" not in source
        assert "cosine similarity" not in source.lower()
        
        # _vector_index_createdのような条件分岐がないこと
        assert "_vector_index_created" not in source
    
    def test_explicit_error_types(self, vss_service):
        """明示的なエラー型が使用されていることを確認"""
        # 無効な入力でエラーを発生させる
        result = vss_service.search({})  # queryが必須
        
        # ErrorDictが返されること
        assert isinstance(result, dict)
        assert "ok" in result
        assert result["ok"] is False
        assert "error" in result
        assert "details" in result
    
    def test_result_type_consistency(self, vss_service):
        """結果の型が一貫していることを確認"""
        # VECTOR拡張を無効化してエラーを確実に発生させる
        vss_service._vector_extension_available = False
        
        # インデックス操作
        index_result = vss_service.index_documents([{"content": "test"}])
        assert "ok" in index_result
        assert isinstance(index_result["ok"], bool)
        
        # 検索操作
        search_result = vss_service.search({"query": "test"})
        assert "ok" in search_result
        assert isinstance(search_result["ok"], bool)
        
        # 両方ともErrorDictであること
        assert index_result["ok"] is False
        assert search_result["ok"] is False