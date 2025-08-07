"""
test_json_processing.py - JSON入力処理の基本テスト

JSON形式でのスキーマ適用、テンプレート処理、およびCLI削除後の動作保証をテストする。

規約準拠:
- testing.md: isolated tests, descriptive names, single responsibility
- layered_architecture.md: テストはapplication層の動作を検証
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import io

# Import modules to test
from requirement.graph.application.template_processor import process_template
from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository
from requirement.graph.infrastructure.apply_ddl_schema import apply_ddl_schema


@pytest.fixture
def temp_db_path():
    """テスト用の一時的なデータベースパスを作成"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_db.kuzu"
    yield str(db_path)
    # Clean up
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def initialized_repository(temp_db_path):
    """初期化済みのテストリポジトリを提供"""
    # Apply schema
    apply_ddl_schema(temp_db_path, create_test_data=False)
    # Create repository
    repository = create_kuzu_repository(temp_db_path)
    return repository


class TestSchemaApplication:
    """スキーマ適用のJSON処理テスト"""
    
    def test_schema_apply_json_input(self, temp_db_path):
        """JSON形式でのスキーマ適用テスト"""
        # Prepare JSON input
        schema_input = {
            "type": "schema",
            "action": "apply",
            "create_test_data": False
        }
        
        # Apply schema
        apply_ddl_schema(temp_db_path, schema_input.get("create_test_data", False))
        
        # Verify database was created
        db_path = Path(temp_db_path)
        assert db_path.exists()
        # KuzuDB creates db.kuzu directory structure
        assert (db_path / "db.kuzu").exists()


class TestTemplateProcessing:
    """テンプレート処理のJSON入力テスト"""
    
    def test_create_requirement_template(self, initialized_repository):
        """create_requirementテンプレートのJSON処理テスト"""
        # Prepare template input
        template_input = {
            "template": "create_requirement",
            "parameters": {
                "id": "test_req_001",
                "title": "テスト要件",
                "description": "JSON処理のテスト用要件",
                "status": "proposed"
            }
        }
        
        # Process template
        result = process_template(template_input, initialized_repository, None)
        
        # Verify result
        assert result is not None
        assert result.get("status") == "success"
    
    def test_find_requirement_template(self, initialized_repository):
        """find_requirementテンプレートのJSON処理テスト"""
        # First create a requirement
        create_input = {
            "template": "create_requirement", 
            "parameters": {
                "id": "find_test_001",
                "title": "検索テスト要件",
                "description": "検索用のテスト要件"
            }
        }
        process_template(create_input, initialized_repository, None)
        
        # Then find it
        find_input = {
            "template": "find_requirement",
            "parameters": {
                "id": "find_test_001"
            }
        }
        
        result = process_template(find_input, initialized_repository, None)
        
        # Verify result
        assert result is not None
        assert result.get("status") == "success"
        assert result.get("data") is not None
    
    def test_list_requirements_template(self, initialized_repository):
        """list_requirementsテンプレートのJSON処理テスト"""
        # Create some requirements first
        for i in range(3):
            create_input = {
                "template": "create_requirement",
                "parameters": {
                    "id": f"list_test_{i:03d}",
                    "title": f"リスト用要件{i+1}",
                    "description": f"リスト表示用テスト要件 #{i+1}"
                }
            }
            process_template(create_input, initialized_repository, None)
        
        # List requirements
        list_input = {
            "template": "list_requirements",
            "parameters": {
                "limit": 10
            }
        }
        
        result = process_template(list_input, initialized_repository, None)
        
        # Verify result
        assert result is not None
        assert result.get("status") == "success"
        assert result.get("data") is not None
        # Should have at least the 3 requirements we created
        assert len(result.get("data", [])) >= 3
    
    def test_missing_parameters_error(self, initialized_repository):
        """必須パラメータ不足時のエラーハンドリングテスト"""
        # Missing required parameters
        invalid_input = {
            "template": "create_requirement",
            "parameters": {
                "id": "incomplete_req"
                # Missing title (required)
            }
        }
        
        result = process_template(invalid_input, initialized_repository, None)
        
        # Verify error response
        assert result is not None
        assert "error" in result
        assert result["error"]["type"] == "MissingParameterError"
        assert "title" in result["error"]["message"]
    
    def test_unknown_template_error(self, initialized_repository):
        """不明なテンプレート指定時のエラーハンドリングテスト"""
        unknown_input = {
            "template": "unknown_template",
            "parameters": {}
        }
        
        result = process_template(unknown_input, initialized_repository, None)
        
        # Verify error response
        assert result is not None
        # Should return NotFoundError object
        assert hasattr(result, 'type') or isinstance(result, dict)


class TestJSONProcessingWithoutCLI:
    """CLI削除後のJSON処理動作保証テスト"""
    
    def test_direct_template_processing(self, initialized_repository):
        """CLIを経由せずに直接テンプレート処理が動作することを確認"""
        # This test ensures that JSON processing works independently of CLI
        # by directly calling the application layer functions
        
        # Create requirement without CLI
        template_data = {
            "template": "create_requirement",
            "parameters": {
                "id": "direct_test_001", 
                "title": "直接処理テスト",
                "description": "CLIなしでの処理テスト"
            }
        }
        
        create_result = process_template(template_data, initialized_repository, None)
        assert create_result.get("status") == "success"
        
        # Find requirement without CLI
        find_data = {
            "template": "find_requirement",
            "parameters": {
                "id": "direct_test_001"
            }
        }
        
        find_result = process_template(find_data, initialized_repository, None)
        assert find_result.get("status") == "success"
        assert find_result.get("data") is not None
    
    def test_schema_application_without_cli(self, temp_db_path):
        """CLIを経由せずに直接スキーマ適用が動作することを確認"""
        # Apply schema directly without CLI
        apply_ddl_schema(temp_db_path, create_test_data=False)
        
        # Verify database creation
        db_path = Path(temp_db_path)
        assert db_path.exists()
        
        # Verify repository can be created
        repository = create_kuzu_repository(temp_db_path)
        assert repository is not None
        assert repository.get("connection") is not None


class TestJSONInputValidation:
    """JSON入力の検証テスト"""
    
    def test_malformed_json_handling(self):
        """不正なJSON形式の処理テスト"""
        # This would typically be tested at the main.py level
        # Here we test that our core functions handle None/empty inputs gracefully
        
        with pytest.raises((TypeError, KeyError, AttributeError)):
            # Invalid template data should raise appropriate errors
            process_template(None, None, None)
    
    def test_missing_template_field(self, initialized_repository):
        """templateフィールド欠如時の処理テスト"""
        invalid_data = {
            "parameters": {
                "id": "test"
            }
            # Missing "template" field
        }
        
        result = process_template(invalid_data, initialized_repository, None)
        
        # Should handle gracefully - empty template becomes ""
        assert result is not None


class TestEndToEndJSONWorkflow:
    """JSON処理のエンドツーエンドワークフローテスト"""
    
    def test_complete_requirement_lifecycle(self, temp_db_path):
        """要件のライフサイクル全体をJSONで処理するテスト"""
        # 1. Apply schema
        apply_ddl_schema(temp_db_path, create_test_data=False)
        repository = create_kuzu_repository(temp_db_path)
        
        # 2. Create requirement
        create_data = {
            "template": "create_requirement",
            "parameters": {
                "id": "lifecycle_test_001",
                "title": "ライフサイクルテスト",
                "description": "完全なライフサイクルのテスト要件",
                "status": "proposed"
            }
        }
        create_result = process_template(create_data, repository, None)
        assert create_result.get("status") == "success"
        
        # 3. Find the created requirement
        find_data = {
            "template": "find_requirement", 
            "parameters": {
                "id": "lifecycle_test_001"
            }
        }
        find_result = process_template(find_data, repository, None)
        assert find_result.get("status") == "success"
        
        # 4. Update requirement (creates new version)
        update_data = {
            "template": "update_requirement",
            "parameters": {
                "id": "lifecycle_test_001",
                "status": "approved"
            }
        }
        update_result = process_template(update_data, repository, None)
        assert update_result.get("status") == "success"
        
        # 5. Get requirement history
        history_data = {
            "template": "get_requirement_history",
            "parameters": {
                "id": "lifecycle_test_001"
            }
        }
        history_result = process_template(history_data, repository, None)
        assert history_result.get("status") == "success"
        assert history_result.get("data", {}).get("total_versions", 0) >= 2


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])