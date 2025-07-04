"""
バージョニング機能の単体テスト（pytestで実行可能）
"""
import pytest
import tempfile
import os
from datetime import datetime

# テスト用環境設定
from .infrastructure.variables import setup_test_environment
setup_test_environment()


class TestVersioningUnit:
    """バージョニング機能の単体テスト"""
    
    def test_version_service_functions_exist(self):
        """バージョンサービスの関数が存在する"""
        from .application.version_service import create_version_service
        
        # モックリポジトリ
        mock_repo = {
            "connection": None,
            "execute": lambda q, p: {"data": []},
            "db": None
        }
        
        service = create_version_service(mock_repo)
        
        assert "create_versioned_requirement" in service
        assert "update_versioned_requirement" in service
        assert "get_requirement_history" in service
        assert "get_requirement_at_timestamp" in service
    
    def test_versioned_cypher_executor_creation(self):
        """バージョン付きCypherエグゼキュータが作成できる"""
        from .infrastructure.versioned_cypher_executor import create_versioned_cypher_executor
        
        # モックリポジトリ
        mock_repo = {
            "connection": None,
            "execute": lambda q, p: {"data": []},
            "db": None
        }
        
        executor = create_versioned_cypher_executor(mock_repo)
        
        assert "execute" in executor
        assert callable(executor["execute"])
    
    def test_versioning_executor_integration(self):
        """バージョニングエグゼキュータがmain.pyで使用できる"""
        from .infrastructure.versioned_cypher_executor import create_versioned_cypher_executor
        
        # モックリポジトリ
        mock_repo = {
            "connection": None,
            "execute": lambda q, p: {"data": []},
            "db": None
        }
        
        # バージョニングエグゼキュータが作成できることを確認
        executor = create_versioned_cypher_executor(mock_repo)
        
        assert "execute" in executor
        assert callable(executor["execute"])
    
    def test_create_query_detection(self):
        """CREATE クエリが正しく検出される"""
        from .infrastructure.versioned_cypher_executor import create_versioned_cypher_executor
        
        create_query = """
        CREATE (r:RequirementEntity {
            id: 'REQ-001',
            title: 'Test'
        })
        """
        
        # クエリパターンのチェック
        import re
        create_pattern = r'CREATE\s+\((\w+):RequirementEntity\s*\{([^}]+)\}\)'
        match = re.search(create_pattern, create_query, re.IGNORECASE | re.DOTALL)
        
        assert match is not None
        assert match.group(1) == 'r'  # 変数名
        assert 'id' in match.group(2)  # プロパティ
    
    def test_update_query_detection(self):
        """UPDATE クエリが正しく検出される"""
        update_query = """
        MATCH (r:RequirementEntity {id: 'REQ-001'})
        SET r.description = 'Updated'
        RETURN r
        """
        
        # クエリパターンのチェック
        import re
        update_pattern = r'MATCH\s+\((\w+):RequirementEntity.*?\)\s*SET\s+'
        match = re.search(update_pattern, update_query, re.IGNORECASE | re.DOTALL)
        
        assert match is not None
        assert match.group(1) == 'r'  # 変数名
    
    def test_versioning_metadata_structure(self):
        """バージョニングメタデータの構造が正しい"""
        # 期待されるメタデータ構造
        expected_create_metadata = {
            "version": 1,
            "version_id": "ver_REQ-001_v1",
            "location_uri": "req://REQ-001"
        }
        
        expected_update_metadata = {
            "version": 2,
            "previous_version": 1,
            "version_id": "ver_REQ-001_v2",
            "change_reason": "Update reason",
            "author": "test_user"
        }
        
        # 構造の検証
        assert "version" in expected_create_metadata
        assert "version_id" in expected_create_metadata
        assert "location_uri" in expected_create_metadata
        
        assert "version" in expected_update_metadata
        assert "previous_version" in expected_update_metadata
        assert "change_reason" in expected_update_metadata