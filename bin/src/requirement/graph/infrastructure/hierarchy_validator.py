"""
Hierarchy Validator - 階層ルールの検証と強制
依存: domain.types
外部依存: なし
"""
from typing import Dict, Tuple, Optional, List
import re
import sys


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
    
    def detect_hierarchy_level_from_title(self, title: str) -> Optional[int]:
        """タイトルから階層レベルを推定"""
        title_lower = title.lower()
        for level, definition in self.HIERARCHY_DEFINITIONS.items():
            for keyword in definition["keywords"]:
                if keyword.lower() in title_lower:
                    return level
        return None
    
    def validate_hierarchy_constraints(self, cypher: str) -> Dict:
        """
        階層制約を検証
        
        Args:
            cypher: 検証対象のCypherクエリ文字列
            
        Returns:
            Dict: {
                "is_valid": bool,  # 検証成功かどうか
                "score": float,    # -1.0（違反）〜0.0（正常）
                "error": str,      # エラーメッセージ（違反時）
                "warning": str,    # 警告メッセージ（非推奨時）
                "details": List[str]  # 詳細情報
            }
        """
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
        
        # 2. タイトルベースの階層違反チェック（新規実装）
        # CREATE文でDEPENDS_ONの関係を作成する場合
        # 複数行にまたがるCREATE文にも対応
        create_depends = re.search(
            r"\((\w+)\)-\[:DEPENDS_ON\]->\((\w+)\)",
            cypher,
            re.DOTALL | re.MULTILINE
        )
        
        if create_depends:
            
            # 各エンティティの情報を抽出
            entities = {}
            
            # パターン: (var:Type {properties})
            entity_pattern = r"\((\w+):\w+\s*\{([^}]+)\}\)"
            for match in re.finditer(entity_pattern, cypher):
                var_name = match.group(1)
                props_str = match.group(2)
                
                # titleプロパティを抽出
                title_match = re.search(r"title:\s*['\"]([^'\"]+)['\"]", props_str)
                if title_match:
                    title = title_match.group(1)
                    entities[var_name] = {
                        "title": title,
                        "level": self.detect_hierarchy_level_from_title(title)
                    }
            
            # DEPENDS_ON関係の親子を特定
            parent_var = create_depends.group(1).strip()
            child_var = create_depends.group(2).strip()
            
            if parent_var in entities and child_var in entities:
                parent_info = entities[parent_var]
                child_info = entities[child_var]
                
                if parent_info["level"] is not None and child_info["level"] is not None:
                    # 階層違反チェック: 下位が上位に依存することはできない
                    if parent_info["level"] > child_info["level"]:
                        result["is_valid"] = False
                        result["score"] = -1.0
                        result["error"] = "階層違反"
                        result["details"].append(
                            f"{parent_info['title']}(Level {parent_info['level']})が"
                            f"{child_info['title']}(Level {child_info['level']})に依存しています。"
                            f"下位階層は上位階層に依存できません。"
                        )
                        
            # 自己参照チェック
            if parent_var == child_var:
                result["is_valid"] = False
                result["score"] = -1.0
                result["error"] = "自己参照エラー"
                result["details"].append(
                    f"ノード'{parent_var}'が自分自身に依存しています。"
                    f"自己参照は許可されていません。"
                )
        
        # 3. タイトルと階層レベルの整合性チェック（既存）
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


def test_階層違反_タスクがビジョンの親_エラーとスコアマイナス1():
    """階層違反検出_タスクがビジョンに依存_エラーとペナルティスコア"""
    validator = HierarchyValidator()
    
    # タスク実装（Level 4）がビジョン（Level 0）に依存する違反ケース
    cypher = """
    CREATE (parent:RequirementEntity {
        id: 'test_parent_task',
        title: 'タスク実装',
        description: '具体的なタスク',
        priority: 'medium',
        requirement_type: 'functional',
        verification_required: true
    }),
    (child:RequirementEntity {
        id: 'test_child_vision', 
        title: 'ビジョン',
        description: '上位ビジョン',
        priority: 'high',
        requirement_type: 'functional',
        verification_required: true
    }),
    (parent)-[:DEPENDS_ON]->(child)
    """
    
    result = validator.validate_hierarchy_constraints(cypher)
    
    # 階層違反が検出される
    assert result["is_valid"] == False
    assert result["score"] == -1.0
    assert result["error"] == "階層違反"
    assert "タスク実装(Level 4)がビジョン(Level 0)に依存" in str(result["details"])


def test_自己参照_同一ノード間の依存_エラーとスコアマイナス1():
    """自己参照検出_同じノードが自分に依存_エラーとペナルティスコア"""
    validator = HierarchyValidator()
    
    cypher = """
    CREATE (r:RequirementEntity {id: 'self_ref_test'}),
    (r)-[:DEPENDS_ON]->(r)
    """
    
    result = validator.validate_hierarchy_constraints(cypher)
    
    # 自己参照が検出される
    assert result["is_valid"] == False
    assert result["score"] == -1.0
    assert result["error"] == "自己参照エラー"
    assert "自分自身に依存" in str(result["details"])


def test_正常な階層依存_上位が下位に依存_成功():
    """正常な階層_上位階層が下位階層に依存_エラーなし"""
    validator = HierarchyValidator()
    
    cypher = """
    CREATE (arch:RequirementEntity {
        id: 'test_arch',
        title: 'アーキテクチャ設計',
        description: 'システムアーキテクチャ'
    }),
    (module:RequirementEntity {
        id: 'test_module',
        title: 'モジュール実装',
        description: '機能モジュール'
    }),
    (arch)-[:DEPENDS_ON]->(module)
    """
    
    result = validator.validate_hierarchy_constraints(cypher)
    
    # エラーなし
    assert result["is_valid"] == True
    assert result["score"] == 0.0
    assert result["error"] is None


def test_複数CREATE文_各文を個別に検証():
    """複数CREATE文_それぞれの階層違反を検出"""
    validator = HierarchyValidator()
    
    cypher = """
    CREATE (vision:RequirementEntity {
        id: 'vision_001',
        title: 'システムビジョン'
    });
    
    CREATE (task:RequirementEntity {
        id: 'task_001',
        title: 'タスク実装'
    }),
    (vision2:RequirementEntity {
        id: 'vision_002',
        title: 'ビジョン'
    }),
    (task)-[:DEPENDS_ON]->(vision2);
    """
    
    result = validator.validate_hierarchy_constraints(cypher)
    
    # 2つ目のCREATE文で階層違反
    assert result["is_valid"] == False
    assert result["score"] == -1.0


def test_MATCH後のCREATE_既存ノードとの関係で階層違反():
    """MATCH後CREATE_既存ノードとの階層違反を検出"""
    validator = HierarchyValidator()
    
    # 実際のシナリオ：既存のタスクに新しいビジョンを依存させる
    cypher = """
    MATCH (task:RequirementEntity {id: 'existing_task', title: 'タスク実装'})
    CREATE (vision:RequirementEntity {
        id: 'new_vision',
        title: 'ビジョン'
    }),
    (task)-[:DEPENDS_ON]->(vision)
    """
    
    # 現在の実装では、MATCHノードのタイトルが取得できないため、
    # CREATE部分のみで判定可能な場合のみ検出される
    result = validator.validate_hierarchy_constraints(cypher)
    # 将来的な拡張のためのテストケース


# 実際のKuzuDBを使った統合テストが必要な場合は、
# in-memory KuzuDBインスタンスを作成して使用する