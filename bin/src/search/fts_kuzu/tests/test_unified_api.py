#!/usr/bin/env python3
"""
FTS統一APIのテスト

create_fts()関数とFTSクラスの統合テスト
VSSとの互換性を確認
"""

import os
import shutil
import tempfile
import pytest
from fts_kuzu.application import create_fts, FTS


class TestUnifiedAPI:
    """統一APIのテストクラス"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_db")

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_fts_returns_fts_instance(self):
        """create_fts()がFTSインスタンスを返すことを確認"""
        fts = create_fts(in_memory=True)
        assert isinstance(fts, FTS)
        assert hasattr(fts, 'index')
        assert hasattr(fts, 'search')
        assert hasattr(fts, 'close')

    def test_create_fts_with_custom_config(self):
        """カスタム設定でFTSを作成"""
        fts = create_fts(
            db_path=self.db_path,
            in_memory=False,
            default_limit=20
        )
        assert isinstance(fts, FTS)
        assert fts.config.db_path == self.db_path
        assert fts.config.default_limit == 20

    def test_index_method_basic(self):
        """index()メソッドの基本動作"""
        fts = create_fts(in_memory=True)
        
        documents = [
            {"id": "1", "title": "Test Document", "content": "This is a test document"},
            {"id": "2", "title": "Another Test", "content": "Another test document here"}
        ]
        
        result = fts.index(documents)
        
        assert result["ok"] is True
        assert result["indexed_count"] == 2
        assert "index_time_ms" in result

    def test_index_method_empty_documents(self):
        """空のドキュメントリストでのindex()"""
        fts = create_fts(in_memory=True)
        
        result = fts.index([])
        
        assert result["ok"] is False
        assert "error" in result
        assert "No documents provided" in result["error"]

    def test_search_method_basic(self):
        """search()メソッドの基本動作"""
        fts = create_fts(in_memory=True)
        
        # ドキュメントをインデックス
        documents = [
            {"id": "1", "title": "Python Programming", "content": "Learn Python programming basics"},
            {"id": "2", "title": "Java Programming", "content": "Java programming for beginners"}
        ]
        fts.index(documents)
        
        # 検索実行
        result = fts.search("Python", limit=5)
        
        assert result["ok"] is True
        assert "results" in result
        assert "metadata" in result
        assert result["metadata"]["query"] == "Python"

    def test_search_with_custom_limit(self):
        """カスタムlimitでの検索"""
        fts = create_fts(in_memory=True)
        
        # 複数のドキュメントをインデックス
        documents = []
        for i in range(10):
            documents.append({
                "id": f"{i}",
                "title": f"Document {i}",
                "content": f"This is test document number {i}"
            })
        fts.index(documents)
        
        # limit=3で検索
        result = fts.search("document", limit=3)
        
        assert result["ok"] is True
        assert len(result["results"]) <= 3

    def test_close_method(self):
        """close()メソッドの動作確認"""
        fts = create_fts(db_path=self.db_path, in_memory=False)
        
        # インデックス作成
        fts.index([{"id": "1", "title": "Test", "content": "Test content"}])
        
        # 検索が正常に動作することを確認
        result = fts.search("test")
        assert result["ok"] is True
        
        # クローズメソッドが存在し、エラーなく実行できることを確認
        fts.close()
        
        # Note: 現在の実装ではclose()後も新しい接続が作成されるため、
        # 検索は継続して動作する

    def test_resource_management_basic(self):
        """基本的なリソース管理"""
        fts = create_fts(in_memory=True)
        
        # インデックスと検索
        fts.index([{"id": "1", "title": "Test", "content": "Test content"}])
        result = fts.search("test")
        assert result["ok"] is True
        
        # closeメソッドが存在することを確認
        assert hasattr(fts, 'close')
        fts.close()

    def test_compatibility_with_vss_api(self):
        """VSS APIとの互換性確認"""
        fts = create_fts(in_memory=True)
        
        # VSSと同じ形式のドキュメント（titleなし）
        documents = [
            {"id": "1", "content": "This is a test document"},
            {"id": "2", "content": "Another test document"}
        ]
        
        # titleがなくても動作することを確認
        result = fts.index(documents)
        assert result["ok"] is True
        
        # 検索も動作確認
        search_result = fts.search("test")
        assert search_result["ok"] is True

    def test_search_result_format(self):
        """検索結果のフォーマット確認"""
        fts = create_fts(in_memory=True)
        
        fts.index([
            {"id": "1", "title": "Test", "content": "Test content with Python"},
            {"id": "2", "title": "Another", "content": "Another document"}
        ])
        
        result = fts.search("Python")
        
        assert result["ok"] is True
        assert "results" in result
        assert "metadata" in result
        
        # 各結果のフォーマットを確認
        if len(result["results"]) > 0:
            first_result = result["results"][0]
            assert "id" in first_result
            assert "content" in first_result
            assert "score" in first_result
            assert "highlights" in first_result

    def test_error_handling(self):
        """エラーハンドリングの確認"""
        fts = create_fts(in_memory=True)
        
        # 不正なドキュメント形式
        invalid_docs = [
            {"wrong_field": "value"}  # id, content/titleがない
        ]
        
        result = fts.index(invalid_docs)
        assert result["ok"] is False
        assert "error" in result

    def test_multiple_instances(self):
        """複数のFTSインスタンスの同時使用"""
        fts1 = create_fts(in_memory=True)
        fts2 = create_fts(in_memory=True)
        
        # それぞれ別のデータをインデックス
        fts1.index([{"id": "1", "content": "First FTS instance"}])
        fts2.index([{"id": "2", "content": "Second FTS instance"}])
        
        # それぞれで検索
        result1 = fts1.search("First")
        result2 = fts2.search("Second")
        
        assert result1["ok"] is True
        assert result2["ok"] is True
        
        # 独立していることを確認
        result1_cross = fts1.search("Second")
        result2_cross = fts2.search("First")
        
        # インメモリDBなので、それぞれ独立している
        assert len(result1_cross.get("results", [])) == 0
        assert len(result2_cross.get("results", [])) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])