"""
Query Validator - Cypherクエリのセキュリティチェック
依存: なし
外部依存: なし
"""
from typing import Dict, List, Optional, Tuple
import re


class QueryValidator:
    """
    LLMから受け取ったCypherクエリの安全性を検証
    """
    
    # 許可するCypherキーワード
    ALLOWED_KEYWORDS = {
        "MATCH", "CREATE", "MERGE", "SET", "DELETE", "RETURN", "WHERE", 
        "WITH", "ORDER", "BY", "LIMIT", "SKIP", "UNION", "CALL", "YIELD",
        "AND", "OR", "NOT", "EXISTS", "AS", "DISTINCT", "COUNT", "SUM",
        "AVG", "MIN", "MAX", "COLLECT", "CONTAINS", "STARTS", "ENDS"
    }
    
    # 禁止するパターン
    FORBIDDEN_PATTERNS = [
        r"DROP\s+(DATABASE|TABLE|INDEX)",
        r"DETACH\s+DELETE",
        r"REMOVE\s+.*\.\*",  # すべてのプロパティ削除
        r"SET\s+.*\s*=\s*\{\}",  # 空オブジェクトへの置換
    ]
    
    # 許可するノードラベル
    ALLOWED_LABELS = {
        "RequirementEntity", "LocationURI", "VersionState", 
        "RequirementSnapshot", "CodeEntity", "ReferenceEntity"
    }
    
    # 許可する関係タイプ
    ALLOWED_RELATIONSHIPS = {
        "DEPENDS_ON", "PARENT_OF", "LOCATED_WITH_REQUIREMENT",
        "FOLLOWS", "TRACKS_STATE_OF_LOCATED_ENTITY", "CONTAINS_LOCATION",
        "HAS_SNAPSHOT", "SNAPSHOT_OF_VERSION"
    }
    
    def validate(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        クエリの安全性を検証
        
        Args:
            query: 検証するCypherクエリ
            
        Returns:
            (is_valid, error_message)
        """
        # 空クエリチェック
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        # 大文字変換して検証
        query_upper = query.upper()
        
        # 禁止パターンのチェック
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Forbidden pattern detected: {pattern}"
        
        # DROP, DETACH DELETEの単純チェック
        if "DROP" in query_upper and ("DATABASE" in query_upper or "TABLE" in query_upper):
            return False, "DROP DATABASE/TABLE is not allowed"
        
        if "DETACH" in query_upper and "DELETE" in query_upper:
            return False, "DETACH DELETE is not allowed"
        
        # パラメータインジェクションの検出
        if ";" in query and not re.match(r"^[^'\"]*;[^'\"]*$", query):
            # セミコロンが文字列リテラル外にある場合
            if re.search(r"(DROP|DELETE|DETACH|REMOVE)\s", query_upper):
                return False, "Potential injection attempt detected"
        
        # ラベルの検証（ノードラベルのみ、関係タイプは除外）
        # ノードラベルは (x:Label) または (:Label) の形式
        label_pattern = r"\([\w\s]*:(\w+)[\w\s]*\)"
        found_labels = re.findall(label_pattern, query)
        for label in found_labels:
            if label not in self.ALLOWED_LABELS:
                return False, f"Unauthorized label: {label}"
        
        # 関係タイプの検証
        rel_pattern = r"\[:\s*(\w+)\s*\]"
        found_rels = re.findall(rel_pattern, query)
        for rel in found_rels:
            if rel not in self.ALLOWED_RELATIONSHIPS:
                # カスタムプロシージャ呼び出しは許可
                if not query_upper.startswith("CALL"):
                    return False, f"Unauthorized relationship: {rel}"
        
        return True, None
    
    def sanitize_parameters(self, parameters: Dict) -> Dict:
        """
        パラメータのサニタイズ
        
        Args:
            parameters: クエリパラメータ
            
        Returns:
            サニタイズされたパラメータ
        """
        if not parameters:
            return {}
        
        sanitized = {}
        
        # 危険な文字列パターン
        dangerous_patterns = [
            r";\s*(DROP|DELETE|DETACH|REMOVE)",
            r"--",  # SQLコメント
            r"/\*.*\*/",  # ブロックコメント
            r"(DROP|DELETE)\s+(DATABASE|TABLE)",
        ]
        
        for key, value in parameters.items():
            if isinstance(value, str):
                # 危険なパターンを除去
                clean_value = value
                for pattern in dangerous_patterns:
                    clean_value = re.sub(pattern, "", clean_value, flags=re.IGNORECASE)
                
                # セミコロンを安全な文字に置換
                clean_value = clean_value.replace(";", "")
                
                sanitized[key] = clean_value
            else:
                # 文字列以外はそのまま
                sanitized[key] = value
        
        return sanitized


# Test cases - TDD Red Phase
def test_validate_safe_read_query_returns_valid():
    """validate_安全な読み取りクエリ_有効を返す"""
    validator = QueryValidator()
    query = "MATCH (r:RequirementEntity) WHERE r.status = 'approved' RETURN r"
    
    is_valid, error = validator.validate(query)
    
    assert is_valid is True
    assert error is None


def test_validate_safe_create_query_returns_valid():
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


def test_validate_drop_database_query_returns_invalid():
    """validate_DROP_DATABASEクエリ_無効を返す"""
    validator = QueryValidator()
    query = "DROP DATABASE production"
    
    is_valid, error = validator.validate(query)
    
    assert is_valid is False, f"Expected invalid but got {is_valid}"
    assert error is not None, "Error message should not be None"
    assert "DROP" in error or "drop" in error, f"Expected 'DROP' in error but got: {error}"


def test_validate_detach_delete_query_returns_invalid():
    """validate_DETACH_DELETEクエリ_無効を返す"""
    validator = QueryValidator()
    query = "MATCH (n) DETACH DELETE n"
    
    is_valid, error = validator.validate(query)
    
    assert is_valid is False, f"Expected invalid but got {is_valid}"
    assert error is not None, "Error message should not be None"
    assert "DETACH" in error or "DELETE" in error, f"Expected 'DETACH DELETE' in error but got: {error}"


def test_validate_unauthorized_label_returns_invalid():
    """validate_未承認ラベル_無効を返す"""
    validator = QueryValidator()
    query = "MATCH (u:User) DELETE u"
    
    is_valid, error = validator.validate(query)
    
    assert is_valid is False
    assert "Unauthorized label" in error or "User" in error


def test_validate_parameter_injection_attempt_returns_invalid():
    """validate_パラメータインジェクション試行_無効を返す"""
    validator = QueryValidator()
    query = "MATCH (r:RequirementEntity) WHERE r.id = $id + '; DROP DATABASE prod;' RETURN r"
    
    is_valid, error = validator.validate(query)
    
    assert is_valid is False
    assert "injection" in error.lower() or "forbidden" in error.lower()


def test_sanitize_parameters_removes_dangerous_values():
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


def test_validate_custom_procedure_call_returns_valid():
    """validate_カスタムプロシージャ呼び出し_有効を返す"""
    validator = QueryValidator()
    query = "CALL requirement.score($req_id, $query_text, 'similarity') YIELD score, details RETURN score"
    
    is_valid, error = validator.validate(query)
    
    assert is_valid is True
    assert error is None


def test_validate_complex_valid_query_returns_valid():
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


def test_validate_empty_query_returns_invalid():
    """validate_空クエリ_無効を返す"""
    validator = QueryValidator()
    
    is_valid, error = validator.validate("")
    
    assert is_valid is False
    assert "empty" in error.lower()


# モッククラスは不要（純粋な検証ロジックのため）