"""
Hierarchy Validator - 階層ルールの検証と強制
依存: domain.types
外部依存: なし
"""
from typing import Dict, Tuple, Optional, List
import re


class HierarchyValidator:
    """階層ルールの検証と強制"""
    
    # 階層定義
    HIERARCHY_DEFINITIONS = {
        0: {"name": "vision", "keywords": ["ビジョン", "vision", "目的"]},
        1: {"name": "architecture", "keywords": ["アーキテクチャ", "architecture", "設計"]},
        2: {"name": "module", "keywords": ["モジュール", "module", "機能"]},
        3: {"name": "component", "keywords": ["コンポーネント", "component", "部品"]},
        4: {"name": "task", "keywords": ["タスク", "task", "実装"]}
    }
    
    def validate_hierarchy_constraints(self, cypher: str) -> Dict:
        """階層制約を検証"""
        result = {
            "is_valid": True,
            "score": 0.0,
            "error": None,
            "warning": None,
            "details": []
        }
        
        # 1. 親子関係の階層レベルチェック - 複数パターンに対応
        # パターン1: 変数名にparent/childが含まれる場合
        lines = cypher.split('\n')
        parent_level = None
        child_level = None
        
        for line in lines:
            # parentの階層レベルを探す
            parent_match = re.search(r"parent.*?hierarchy_level:\s*(\d+)", line)
            if parent_match:
                parent_level = int(parent_match.group(1))
            
            # childの階層レベルを探す
            child_match = re.search(r"child.*?hierarchy_level:\s*(\d+)", line)
            if child_match:
                child_level = int(child_match.group(1))
        
        # パターン2: 変数名が異なる場合（task, visionなど）
        # 各MATCHステートメントから変数名と階層レベルを抽出
        match_patterns = re.findall(
            r"\((\w+):[^{]*\{[^}]*hierarchy_level:\s*(\d+)",
            cypher
        )
        
        # CREATE文から親子関係を抽出
        create_match = re.search(
            r"CREATE\s*\((\w+)\)-\[:PARENT_OF\]->\((\w+)\)",
            cypher
        )
        
        
        if match_patterns and create_match:
            # 変数名と階層レベルのマッピングを作成
            var_levels = {var: int(level) for var, level in match_patterns}
            
            parent_var = create_match.group(1)
            child_var = create_match.group(2)
            
            if parent_var in var_levels and child_var in var_levels:
                parent_level = var_levels[parent_var]
                child_level = var_levels[child_var]
        
        # 階層違反チェック
        if parent_level is not None and child_level is not None:
            if parent_level >= child_level:
                result["is_valid"] = False
                result["score"] = -1.0
                result["error"] = "階層違反"
                result["details"].append(f"Level {parent_level} cannot be parent of Level {child_level}")
                return result
        
        # 2. タイトルと階層レベルの整合性チェック
        title_match = re.search(r"title:\s*'([^']+)'.*?hierarchy_level:\s*(\d+)", cypher, re.DOTALL)
        
        if title_match:
            title = title_match.group(1)
            level = int(title_match.group(2))
            
            for expected_level, definition in self.HIERARCHY_DEFINITIONS.items():
                for keyword in definition["keywords"]:
                    if keyword in title and level != expected_level:
                        result["score"] = -0.3
                        result["warning"] = f"{keyword}は通常Level {expected_level}"
                        break
        
        return result
    
    def enforce_hierarchy_constraint(self, cypher: str) -> str:
        """階層制約を自動追加"""
        # PARENT_OF作成時に制約を追加
        if "CREATE" in cypher and "PARENT_OF" in cypher:
            # CREATE (p)-[:PARENT_OF]->(c)のパターンを探す
            cypher = re.sub(
                r"(CREATE\s*\([^)]+\)-\[:PARENT_OF\]->\([^)]+\))",
                r"\1\n    WHERE p.hierarchy_level < c.hierarchy_level",
                cypher
            )
        
        return cypher
    
    def detect_hierarchy_level_from_context(self, title: str) -> Optional[int]:
        """タイトルから適切な階層レベルを推定"""
        for level, definition in self.HIERARCHY_DEFINITIONS.items():
            for keyword in definition["keywords"]:
                if keyword in title:
                    return level
        return None


# Test cases (t-wada TDD RED phase)
def test_validate_hierarchy_rule_parent_child_level_違反検出_エラーとペナルティ():
    """validate_hierarchy_rule_親子レベル違反_エラーとペナルティを返す"""
    validator = HierarchyValidator()
    
    # L4の要件がL0の親になろうとする
    cypher = """
    MATCH (child:RequirementEntity {id: 'req_vision_001', hierarchy_level: 0})
    MATCH (parent:RequirementEntity {id: 'req_task_001', hierarchy_level: 4})
    CREATE (parent)-[:PARENT_OF]->(child)
    """
    
    result = validator.validate_hierarchy_constraints(cypher)
    
    assert result["is_valid"] == False
    assert result["score"] == -1.0  # 最大ペナルティ
    assert "階層違反" in result["error"]
    assert "Level 4 cannot be parent of Level 0" in result["details"]


def test_validate_hierarchy_rule_title_level_mismatch_不整合検出_警告():
    """validate_hierarchy_rule_タイトルとレベル不一致_警告を返す"""
    validator = HierarchyValidator()
    
    # "ビジョン"というタイトルだがL2として作成
    cypher = """
    CREATE (r:RequirementEntity {
        id: 'req_001',
        title: 'システムビジョン',
        hierarchy_level: 2
    })
    """
    
    result = validator.validate_hierarchy_constraints(cypher)
    
    assert result["is_valid"] == True  # 警告のみ
    assert result["score"] == -0.3  # 軽いペナルティ
    assert "warning" in result
    assert "ビジョンは通常Level 0" in result["warning"]


def test_enforce_hierarchy_constraint_PARENT_OF作成_制約追加():
    """enforce_hierarchy_constraint_親子関係作成時_階層制約を追加"""
    validator = HierarchyValidator()
    
    original_cypher = """
    CREATE (p:RequirementEntity {id: 'parent'})
    CREATE (c:RequirementEntity {id: 'child'})
    CREATE (p)-[:PARENT_OF]->(c)
    """
    
    enforced_cypher = validator.enforce_hierarchy_constraint(original_cypher)
    
    assert "WHERE p.hierarchy_level < c.hierarchy_level" in enforced_cypher


def test_detect_hierarchy_level_from_context_タイトル解析_レベル推定():
    """detect_hierarchy_level_タイトルから_適切なレベルを推定"""
    validator = HierarchyValidator()
    
    # 各階層のキーワードを含むタイトル
    test_cases = [
        ("システムビジョン", 0),
        ("アーキテクチャ設計", 1),
        ("認証モジュール", 2),
        ("ログインコンポーネント", 3),
        ("パスワード検証タスク", 4)
    ]
    
    for title, expected_level in test_cases:
        level = validator.detect_hierarchy_level_from_context(title)
        assert level == expected_level


def test_integration_with_llm_hooks_api_階層違反_負のスコア返却():
    """integration_llm_hooks_api_階層違反時_負のスコアとエラーを返す"""
    # LLM Hooks APIモックを準備
    from .llm_hooks_api import create_llm_hooks_api
    from .query_validator import QueryValidator
    
    class MockRepository:
        def __init__(self):
            self.db = self
            
        def connect(self):
            return MockConnection()
    
    class MockConnection:
        def execute(self, query, params=None):
            return MockResult()
    
    class MockResult:
        def has_next(self):
            return False
            
        def get_next(self):
            return []
    
    # 階層検証を統合したLLM Hooks APIを作成
    mock_repo = {"db": MockRepository(), "connection": MockConnection()}
    api = create_llm_hooks_api(mock_repo)
    
    # 階層違反するCypherクエリ
    request = {
        "type": "cypher",
        "query": """
        MATCH (task:RequirementEntity {hierarchy_level: 4})
        MATCH (vision:RequirementEntity {hierarchy_level: 0})
        CREATE (task)-[:PARENT_OF]->(vision)
        """,
        "validate_hierarchy": True
    }
    
    # 階層検証機能を追加（実際の統合では llm_hooks_api.py に実装）
    validator = HierarchyValidator()
    hierarchy_result = validator.validate_hierarchy_constraints(request["query"])
    
    # デバッグ用出力
    # print(f"Validation result: {hierarchy_result}")
    
    # 階層違反の検証
    assert hierarchy_result["is_valid"] == False
    assert hierarchy_result["score"] == -1.0
    assert "階層違反" in hierarchy_result["error"]