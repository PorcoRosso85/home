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
                "is_valid": bool,       # 検証成功かどうか
                "violation_type": str,  # 違反タイプ
                "error": str,          # エラーメッセージ（違反時）
                "warning": str,        # 警告メッセージ（非推奨時）
                "details": List[str],  # 詳細情報
                "violation_info": Dict # 違反の詳細情報（ScoringService用）
            }
        """
        result = {
            "is_valid": True,
            "violation_type": "no_violation",
            "error": None,
            "warning": None,
            "details": [],
            "violation_info": {}
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
                result["violation_type"] = "hierarchy_violation"
                result["error"] = "階層違反"
                result["details"].append(f"Level {parent_level} cannot be parent of Level {child_level}")
                result["violation_info"] = {
                    "from_level": parent_level,
                    "to_level": child_level
                }
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
            # A DEPENDS_ON B の場合、Aが依存元（dependent）、Bが依存先（dependency）
            dependent_var = create_depends.group(1).strip()  # 依存元
            dependency_var = create_depends.group(2).strip()  # 依存先
            
            if dependent_var in entities and dependency_var in entities:
                dependent_info = entities[dependent_var]
                dependency_info = entities[dependency_var]
                
                if dependent_info["level"] is not None and dependency_info["level"] is not None:
                    # 階層違反チェック: 下位階層（大きい数字）が上位階層（小さい数字）に依存することはできない
                    # OK: アーキテクチャ(1) -> モジュール(2) - 上位が下位に依存
                    # OK: ビジョン(0) -> アーキテクチャ(1) - 上位が下位に依存
                    # NG: モジュール(2) -> アーキテクチャ(1) - 下位が上位に依存
                    # NG: タスク(4) -> ビジョン(0) - 下位が上位に依存
                    if dependent_info["level"] > dependency_info["level"]:
                        result["is_valid"] = False
                        result["violation_type"] = "hierarchy_violation"
                        result["error"] = "階層違反"
                        result["details"].append(
                            f"{dependent_info['title']}(Level {dependent_info['level']})が"
                            f"{dependency_info['title']}(Level {dependency_info['level']})に依存しています。"
                            f"下位階層は上位階層に依存できません。"
                        )
                        result["violation_info"] = {
                            "from_level": dependent_info["level"],
                            "to_level": dependency_info["level"],
                            "from_title": dependent_info["title"],
                            "to_title": dependency_info["title"]
                        }
                        
            # 自己参照チェック
            if dependent_var == dependency_var:
                result["is_valid"] = False
                result["violation_type"] = "self_reference"
                result["error"] = "自己参照エラー"
                result["details"].append(
                    f"ノード'{dependent_var}'が自分自身に依存しています。"
                    f"自己参照は許可されていません。"
                )
                result["violation_info"] = {
                    "node_id": dependent_var,
                    "node_title": entities.get(dependent_var, {}).get("title", dependent_var)
                }
                
        # 3. 間接的循環参照チェック（A→B→C→A）
        # CREATE文から全ての依存関係を抽出
        dependencies = []
        depends_pattern = re.findall(
            r"\((\w+)\)-\[:DEPENDS_ON\]->\((\w+)\)",
            cypher
        )
        
        for from_var, to_var in depends_pattern:
            # 各変数のIDを取得
            from_id = None
            to_id = None
            
            # CREATE文からIDを抽出
            for var_name, entity_info in entities.items():
                # IDパターンを探す
                id_match = re.search(
                    rf"\({var_name}:[^{{]*\{{[^}}]*id:\s*['\"]([^'\"]+)['\"]",
                    cypher
                )
                if id_match:
                    if var_name == from_var:
                        from_id = id_match.group(1)
                    elif var_name == to_var:
                        to_id = id_match.group(1)
            
            if from_id and to_id:
                dependencies.append((from_id, to_id))
        
        # 循環参照の検出（深さ優先探索）
        def find_cycle(graph, start, current, visited, path):
            """循環を検出し、循環パスを返す"""
            if current == start and len(path) > 1:
                return path + [start]
            
            if current in visited:
                return None
            
            visited.add(current)
            
            for from_id, to_id in graph:
                if from_id == current:
                    cycle = find_cycle(graph, start, to_id, visited.copy(), path + [current])
                    if cycle:
                        return cycle
            
            return None
        
        # 各ノードから循環をチェック
        all_nodes = set()
        for from_id, to_id in dependencies:
            all_nodes.add(from_id)
            all_nodes.add(to_id)
        
        for node in all_nodes:
            cycle = find_cycle(dependencies, node, node, set(), [])
            if cycle and len(cycle) > 2:  # 自己参照でない循環
                result["is_valid"] = False
                result["violation_type"] = "circular_reference"
                result["error"] = "循環参照"
                cycle_str = " → ".join(cycle)
                result["details"].append(
                    f"循環参照が検出されました: {cycle_str}"
                )
                result["violation_info"] = {
                    "cycle_path": cycle
                }
        
        # 3. タイトルと階層レベルの整合性チェック（既存）
        title_match = re.search(r"title:\s*'([^']+)'.*?hierarchy_level:\s*(\d+)", cypher, re.DOTALL)
        
        if title_match:
            title = title_match.group(1)
            level = int(title_match.group(2))
            
            for expected_level, definition in self.HIERARCHY_DEFINITIONS.items():
                for keyword in definition["keywords"]:
                    if keyword in title and level != expected_level:
                        result["violation_type"] = "title_level_mismatch"
                        result["warning"] = f"{keyword}は通常Level {expected_level}"
                        result["violation_info"] = {
                            "title": title,
                            "actual_level": level,
                            "expected_level": expected_level
                        }
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
