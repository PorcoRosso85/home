"""JSONL Repositoryのテスト"""

import os
import tempfile
from datetime import datetime
import pytest
from .jsonl_repository import create_jsonl_repository


class TestJsonlRepository:
    """JSONLリポジトリのテスト"""
    
    def test_jsonl_repository_crud_operations_returns_expected_results(self):
        """jsonl_repository_CRUD操作_期待する結果を返す"""
        # テンポラリファイルを使用
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_path = f.name
        
        try:
            repo = create_jsonl_repository(temp_path)
            
            # Create
            decision = {
                "id": "test_001",
                "title": "Test Decision",
                "description": "Test description",
                "status": "proposed",
                "created_at": datetime.now(),
                "embedding": [0.1] * 50
            }
            
            saved = repo["save"](decision)
            assert saved["id"] == "test_001"
            
            # Read
            found = repo["find"]("test_001")
            assert "type" not in found
            assert found["title"] == "Test Decision"
            
            # Update (using save for consistency with immutable design)
            decision["status"] = "approved"
            updated = repo["save"](decision)
            assert updated["status"] == "approved"
            
            # Find all
            all_decisions = repo["find_all"]()
            assert len(all_decisions) == 1
            assert all_decisions[0]["status"] == "approved"
            
        finally:
            os.unlink(temp_path)

    def test_jsonl_repository_find_nonexistent_id_returns_error(self):
        """jsonl_repository_存在しないID検索_エラーを返す"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_path = f.name
        
        try:
            repo = create_jsonl_repository(temp_path)
            
            result = repo["find"]("nonexistent")
            assert result["type"] == "DecisionNotFoundError"
            assert result["decision_id"] == "nonexistent"
            
        finally:
            os.unlink(temp_path)