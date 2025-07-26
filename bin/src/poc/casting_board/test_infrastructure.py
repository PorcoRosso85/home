"""
Infrastructure layer tests for KuzuDB integration.

Tests focus on repository pattern and graph database operations.
"""
import pytest
from datetime import datetime
from typing import Union
import kuzu
from .domain import (
    create_resource,
    add_capability,
    ResourceDict,
    ErrorDict,
)


class TestResourceRepository:
    """Tests for Resource repository with KuzuDB."""
    
    def test_create_in_memory_database(self):
        """In-memoryのKuzuDBデータベースを作成できる"""
        # Act
        db = create_in_memory_database()
        
        # Assert
        assert db is not None
        assert isinstance(db, kuzu.Database)
    
    def test_save_resource_to_graph(self):
        """リソースをグラフデータベースに保存できる"""
        # Arrange
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        resource = create_resource("res-001", "田中太郎", "HUMAN")
        
        # Act
        result = repo.save(resource)
        
        # Assert
        assert "type" not in result  # Success case
        assert result["id"] == "res-001"
    
    def test_find_resource_by_id(self):
        """IDでリソースを検索できる"""
        # Arrange
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        resource = create_resource("res-001", "田中太郎", "HUMAN")
        repo.save(resource)
        
        # Act
        found = repo.find_by_id("res-001")
        
        # Assert
        assert found is not None
        assert found["id"] == "res-001"
        assert found["name"] == "田中太郎"
        assert found["resource_type"] == "HUMAN"
    
    def test_find_resources_by_capability(self):
        """能力でリソースを検索できる"""
        # Arrange
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        
        # Create resources with capabilities
        resource1 = create_resource("res-001", "田中太郎", "HUMAN")
        resource1 = add_capability(resource1, "PYTHON_SKILL", 5)
        repo.save(resource1)
        
        resource2 = create_resource("res-002", "佐藤花子", "HUMAN")
        resource2 = add_capability(resource2, "PYTHON_SKILL", 3)
        resource2 = add_capability(resource2, "JAVA_SKILL", 4)
        repo.save(resource2)
        
        resource3 = create_resource("res-003", "鈴木一郎", "HUMAN")
        resource3 = add_capability(resource3, "JAVA_SKILL", 5)
        repo.save(resource3)
        
        # Act
        python_resources = repo.find_by_capability("PYTHON_SKILL", minimum_level=4)
        
        # Assert
        assert len(python_resources) == 1
        assert python_resources[0]["id"] == "res-001"
    
    def test_update_resource_in_graph(self):
        """リソースの情報を更新できる"""
        # Arrange
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        resource = create_resource("res-001", "田中太郎", "HUMAN")
        repo.save(resource)
        
        # Act
        resource = add_capability(resource, "PYTHON_SKILL", 5)
        result = repo.save(resource)
        
        # Assert
        found = repo.find_by_id("res-001")
        assert len(found["capabilities"]) == 1
        assert found["capabilities"][0]["name"] == "PYTHON_SKILL"
    
    def test_graph_schema_initialization(self):
        """グラフスキーマが正しく初期化される"""
        # Arrange
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        
        # Act
        schema = repo.get_schema()
        
        # Assert
        assert "Resource" in schema["nodes"]
        assert "Capability" in schema["nodes"]
        assert "HAS_CAPABILITY" in schema["relationships"]


from .infrastructure import (
    create_in_memory_database,
    ResourceRepository,
)