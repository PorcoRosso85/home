"""
バージョニング機能の単体テスト（簡単なテストから始める）
"""
import tempfile
import os
import sys

# テスト用環境設定
from .infrastructure.variables import setup_test_environment
setup_test_environment()

from .infrastructure.kuzu_repository import create_kuzu_repository
from .application.version_service import create_version_service
from .infrastructure.ddl_schema_manager import DDLSchemaManager
from pathlib import Path




def test_create_versioned_requirement():
    """バージョン付き要件を作成できる"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = f"{tmpdir}/test.db"
        os.environ["RGL_DB_PATH"] = db_path
        
        # リポジトリ作成
        repo = create_kuzu_repository(db_path)
        
        # スキーマ適用
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = Path(__file__).parent / "ddl" / "schema.cypher"
        if schema_path.exists():
            success, results = schema_manager.apply_schema(str(schema_path))
            assert success
        
        # バージョンサービス作成
        version_service = create_version_service(repo)
        
        # 要件作成
        result = version_service["create_versioned_requirement"]({
            "id": "REQ-001",
            "title": "ユーザー認証機能",
            "description": "安全なログイン機能を提供",
            "author": "test_user",
            "reason": "新規機能追加"
        })
        
        print(f"Create result: {result}")
        
        assert "entity_id" in result
        assert "version_id" in result
        assert "location_uri" in result
        assert result["version"] == 1
        assert result["location_uri"] == "req://REQ-001"


def test_update_versioned_requirement():
    """既存要件を更新すると新しいバージョンが作成される"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = f"{tmpdir}/test.db"
        os.environ["RGL_DB_PATH"] = db_path
        
        # リポジトリ作成
        repo = create_kuzu_repository(db_path)
        
        # スキーマ適用
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = Path(__file__).parent / "ddl" / "schema.cypher"
        if schema_path.exists():
            success, results = schema_manager.apply_schema(str(schema_path))
            assert success
        
        # バージョンサービス作成
        version_service = create_version_service(repo)
        
        # 要件作成
        create_result = version_service["create_versioned_requirement"]({
            "id": "REQ-001",
            "title": "ユーザー認証機能",
            "description": "安全なログイン機能を提供"
        })
        
        # 要件更新
        update_result = version_service["update_versioned_requirement"]({
            "id": "REQ-001",
            "description": "二要素認証を含む安全なログイン機能",
            "author": "security_team",
            "reason": "セキュリティ要件の強化"
        })
        
        print(f"Update result: {update_result}")
        
        assert update_result["version"] == 2
        assert update_result["previous_version"] == 1
        assert update_result["author"] == "security_team"
        assert update_result["change_reason"] == "セキュリティ要件の強化"


def test_get_requirement_history():
    """要件の変更履歴を取得できる"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = f"{tmpdir}/test.db"
        os.environ["RGL_DB_PATH"] = db_path
        
        # リポジトリ作成
        repo = create_kuzu_repository(db_path)
        
        # スキーマ適用
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = Path(__file__).parent / "ddl" / "schema.cypher"
        if schema_path.exists():
            success, results = schema_manager.apply_schema(str(schema_path))
            assert success
        
        # バージョンサービス作成
        version_service = create_version_service(repo)
        
        # 要件作成
        version_service["create_versioned_requirement"]({
            "id": "REQ-001",
            "title": "ユーザー認証機能",
            "description": "安全なログイン機能を提供"
        })
        
        # 要件更新
        version_service["update_versioned_requirement"]({
            "id": "REQ-001",
            "description": "二要素認証を含む安全なログイン機能",
            "author": "security_team",
            "reason": "セキュリティ要件の強化"
        })
        
        # 履歴取得
        history = version_service["get_requirement_history"]("REQ-001")
        
        print(f"History: {history}")
        
        assert len(history) == 2
        assert history[0]["version"] == 1
        assert history[0]["operation"] == "CREATE"
        assert history[1]["version"] == 2
        assert history[1]["operation"] == "UPDATE"
        assert history[1]["change_reason"] == "セキュリティ要件の強化"


if __name__ == "__main__":
    test_create_versioned_requirement()
    print("✓ test_create_versioned_requirement passed")
    
    test_update_versioned_requirement()
    print("✓ test_update_versioned_requirement passed")
    
    test_get_requirement_history()
    print("✓ test_get_requirement_history passed")
    
    print("\nAll tests passed!")