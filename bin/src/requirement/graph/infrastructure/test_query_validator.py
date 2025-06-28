"""Query Validatorのテスト"""

import pytest
from .query_validator import QueryValidator


class TestQueryValidator:
    """QueryValidatorのテスト"""
    
    def test_validate_safe_read_query_returns_valid(self):
        """validate_安全な読み取りクエリ_有効を返す"""
        validator = QueryValidator()
        query = "MATCH (r:RequirementEntity) WHERE r.status = 'approved' RETURN r"
        
        is_valid, error = validator.validate(query)
        
        assert is_valid is True
        assert error is None

    def test_validate_safe_create_query_returns_valid(self):
        """validate_安全な作成クエリ_有効を返す"""
        validator = QueryValidator()
        query = """
        CREATE (r:RequirementEntity {
            id: $id,
            title: $title,
            description: $description
        })
        RETURN r
        """
        
        is_valid, error = validator.validate(query)
        
        assert is_valid is True
        assert error is None

    def test_validate_drop_database_query_returns_invalid(self):
        """validate_DROP_DATABASEクエリ_無効を返す"""
        validator = QueryValidator()
        query = "DROP DATABASE production"
        
        is_valid, error = validator.validate(query)
        
        assert is_valid is False, f"Expected invalid but got {is_valid}"
        assert error is not None, "Error message should not be None"
        assert "DROP" in error or "drop" in error, f"Expected 'DROP' in error but got: {error}"

    def test_validate_detach_delete_query_returns_invalid(self):
        """validate_DETACH_DELETEクエリ_無効を返す"""
        validator = QueryValidator()
        query = "MATCH (n) DETACH DELETE n"
        
        is_valid, error = validator.validate(query)
        
        assert is_valid is False, f"Expected invalid but got {is_valid}"
        assert error is not None, "Error message should not be None"
        assert "DETACH" in error or "DELETE" in error, f"Expected 'DETACH DELETE' in error but got: {error}"

    def test_validate_unauthorized_label_returns_invalid(self):
        """validate_未承認ラベル_無効を返す"""
        validator = QueryValidator()
        query = "MATCH (u:User) DELETE u"
        
        is_valid, error = validator.validate(query)
        
        assert is_valid is False
        assert "Unauthorized label" in error or "User" in error

    def test_validate_parameter_injection_attempt_returns_invalid(self):
        """validate_パラメータインジェクション試行_無効を返す"""
        validator = QueryValidator()
        query = "MATCH (r:RequirementEntity) WHERE r.id = $id + '; DROP DATABASE prod;' RETURN r"
        
        is_valid, error = validator.validate(query)
        
        assert is_valid is False
        assert "injection" in error.lower() or "forbidden" in error.lower()

    def test_sanitize_parameters_removes_dangerous_values(self):
        """sanitize_parameters_危険な値_削除される"""
        validator = QueryValidator()
        params = {
            "id": "req_001",
            "title": "Normal title",
            "description": "'; DROP TABLE RequirementEntity; --"
        }
        
        sanitized = validator.sanitize_parameters(params)
        
        assert sanitized["id"] == "req_001"
        assert sanitized["title"] == "Normal title"
        assert "DROP" not in sanitized["description"]
        assert ";" not in sanitized["description"]

    def test_validate_custom_procedure_call_returns_valid(self):
        """validate_カスタムプロシージャ呼び出し_有効を返す"""
        validator = QueryValidator()
        query = "CALL requirement.score($req_id, $query_text, 'similarity') YIELD score, details RETURN score"
        
        is_valid, error = validator.validate(query)
        
        assert is_valid is True
        assert error is None

    def test_validate_complex_valid_query_returns_valid(self):
        """validate_複雑な有効クエリ_有効を返す"""
        validator = QueryValidator()
        query = """
        MATCH (parent:RequirementEntity)-[:PARENT_OF]->(child:RequirementEntity)
        WHERE parent.id = $parent_id
        WITH parent, COUNT(child) as child_count
        MATCH (parent)-[:DEPENDS_ON]->(dep:RequirementEntity)
        RETURN parent.id, parent.title, child_count, COLLECT(dep.id) as dependencies
        ORDER BY child_count DESC
        LIMIT 10
        """
        
        is_valid, error = validator.validate(query)
        
        assert is_valid is True, f"Expected valid but got invalid. Error: {error}"
        assert error is None

    def test_validate_empty_query_returns_invalid(self):
        """validate_空クエリ_無効を返す"""
        validator = QueryValidator()
        
        is_valid, error = validator.validate("")
        
        assert is_valid is False
        assert "empty" in error.lower()

    def test_validate_allowed_relationships_valid(self):
        """validate_許可された関係タイプ_有効を返す"""
        validator = QueryValidator()
        query = """
        MATCH (r1:RequirementEntity)-[:DEPENDS_ON]->(r2:RequirementEntity)
        CREATE (r1)-[:PARENT_OF]->(r3:RequirementEntity)
        RETURN r1, r2, r3
        """
        
        is_valid, error = validator.validate(query)
        
        assert is_valid is True
        assert error is None

    def test_validate_unauthorized_relationship_invalid(self):
        """validate_未承認の関係タイプ_無効を返す"""
        validator = QueryValidator()
        query = "MATCH (r1:RequirementEntity)-[:UNKNOWN_REL]->(r2:RequirementEntity) RETURN r1"
        
        is_valid, error = validator.validate(query)
        
        assert is_valid is False
        assert "Unauthorized relationship" in error

    def test_sanitize_parameters_handles_non_string_values(self):
        """sanitize_parameters_非文字列値_そのまま返す"""
        validator = QueryValidator()
        params = {
            "id": "req_001",
            "count": 42,
            "is_active": True,
            "tags": ["tag1", "tag2"],
            "metadata": {"key": "value"}
        }
        
        sanitized = validator.sanitize_parameters(params)
        
        assert sanitized["id"] == "req_001"
        assert sanitized["count"] == 42
        assert sanitized["is_active"] is True
        assert sanitized["tags"] == ["tag1", "tag2"]
        assert sanitized["metadata"] == {"key": "value"}