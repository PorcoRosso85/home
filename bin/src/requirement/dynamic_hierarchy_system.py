#!/usr/bin/env python3
"""
動的階層管理システム
階層レベルを自動計算し、要件ノードに動的に割り当てる
"""
import sys
import os
from typing import Dict, List, Optional, Tuple, Set
from collections import deque

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

# 環境変数設定
os.environ["LD_LIBRARY_PATH"] = "/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/"
os.environ["RGL_DB_PATH"] = "/home/nixos/bin/src/kuzu/kuzu_db"

from graph.infrastructure.cypher_executor import CypherExecutor


class DynamicHierarchyManager:
    """動的階層管理マネージャー"""
    
    def __init__(self, connection):
        self.executor = CypherExecutor(connection)
        # 階層定義（動的に変更可能）
        self.hierarchy_definitions = {
            0: {"name": "vision", "description": "ビジョン・戦略レベル"},
            1: {"name": "architecture", "description": "アーキテクチャレベル"},
            2: {"name": "module", "description": "モジュールレベル"},
            3: {"name": "component", "description": "コンポーネントレベル"},
            4: {"name": "task", "description": "タスクレベル"}
        }
    
    def calculate_hierarchy_levels(self) -> Dict[str, int]:
        """
        全要件の階層レベルを動的に計算
        ルートノードから開始し、BFSで階層を決定
        """
        # ルートノード（親を持たない要件）を特定
        root_query = """
        MATCH (r:RequirementEntity)
        WHERE NOT (r)-[:DEPENDS_ON]->(:RequirementEntity)
        RETURN r.id, r.title
        """
        
        root_result = self.executor.execute(root_query)
        if root_result.get("error"):
            print(f"エラー: {root_result['error']}")
            return {}
        
        # 階層レベルマップを初期化
        hierarchy_levels = {}
        
        # ルートノードはレベル0または1（設定可能）
        root_level = 1  # アーキテクチャレベルから開始
        
        for root_id, root_title in root_result.get("data", []):
            print(f"ルート要件発見: {root_title} (Level {root_level})")
            hierarchy_levels[root_id] = root_level
        
        # BFSで子要件の階層を計算
        visited = set()
        queue = deque()
        
        # ルートノードをキューに追加
        for root_id in hierarchy_levels:
            queue.append((root_id, root_level))
            visited.add(root_id)
        
        while queue:
            current_id, current_level = queue.popleft()
            
            # 子要件を取得
            children_query = """
            MATCH (child:RequirementEntity)-[:DEPENDS_ON]->(parent:RequirementEntity {id: $parent_id})
            RETURN child.id, child.title
            """
            
            children_result = self.executor.execute(children_query, {"parent_id": current_id})
            
            for child_id, child_title in children_result.get("data", []):
                if child_id not in visited:
                    child_level = current_level + 1
                    hierarchy_levels[child_id] = child_level
                    queue.append((child_id, child_level))
                    visited.add(child_id)
                    print(f"  → {child_title} (Level {child_level})")
        
        return hierarchy_levels
    
    def update_hierarchy_properties(self, hierarchy_levels: Dict[str, int]):
        """
        計算された階層レベルをデータベースに保存
        """
        print("\n=== 階層レベルをデータベースに更新 ===")
        
        success_count = 0
        for req_id, level in hierarchy_levels.items():
            # 階層レベルと階層名を更新
            hierarchy_name = self.hierarchy_definitions.get(level, {}).get("name", "unknown")
            
            update_query = """
            MATCH (r:RequirementEntity {id: $req_id})
            SET r.hierarchy_level = $level,
                r.hierarchy_name = $hierarchy_name
            RETURN r.id, r.title, r.hierarchy_level, r.hierarchy_name
            """
            
            result = self.executor.execute(update_query, {
                "req_id": req_id,
                "level": level,
                "hierarchy_name": hierarchy_name
            })
            
            if result.get("error"):
                print(f"エラー: {req_id} - {result['error']}")
            elif result.get("data") and len(result["data"]) > 0:
                data = result["data"][0]
                print(f"更新: {data[1]} - Level {data[2]} ({data[3]})")
                success_count += 1
        
        print(f"\n{success_count}/{len(hierarchy_levels)}件の更新に成功しました")
    
    def validate_hierarchy_rules(self) -> List[Dict]:
        """
        階層ルールの違反を検出
        親は必ず子より上位の階層でなければならない
        """
        print("\n=== 階層ルールの検証 ===")
        
        violations = []
        
        # 親子関係で階層ルール違反をチェック
        violation_query = """
        MATCH (child:RequirementEntity)-[:DEPENDS_ON]->(parent:RequirementEntity)
        WHERE child.hierarchy_level <= parent.hierarchy_level
        RETURN child.id, child.title, child.hierarchy_level,
               parent.id, parent.title, parent.hierarchy_level
        """
        
        result = self.executor.execute(violation_query)
        
        for row in result.get("data", []):
            violation = {
                "child_id": row[0],
                "child_title": row[1],
                "child_level": row[2],
                "parent_id": row[3],
                "parent_title": row[4],
                "parent_level": row[5]
            }
            violations.append(violation)
            print(f"違反: {row[1]}(Level {row[2]}) -> {row[4]}(Level {row[5]})")
        
        if not violations:
            print("階層ルール違反なし")
        
        return violations
    
    def get_hierarchy_statistics(self) -> Dict:
        """
        階層の統計情報を取得
        """
        stats_query = """
        MATCH (r:RequirementEntity)
        WHERE r.hierarchy_level IS NOT NULL
        WITH r.hierarchy_level as level, count(r) as count
        RETURN level, count
        ORDER BY level
        """
        
        result = self.executor.execute(stats_query)
        
        stats = {
            "level_counts": {},
            "total_requirements": 0,
            "max_level": 0,
            "min_level": float('inf')
        }
        
        if result.get("data"):
            for level, count in result["data"]:
                stats["level_counts"][level] = count
                stats["total_requirements"] += count
                stats["max_level"] = max(stats["max_level"], level)
                stats["min_level"] = min(stats["min_level"], level)
        
        # データがない場合のデフォルト値
        if stats["min_level"] == float('inf'):
            stats["min_level"] = 0
        
        return stats
    
    def auto_assign_hierarchy_type(self):
        """
        要件の内容から階層タイプを自動推定
        """
        print("\n=== 階層タイプの自動割り当て ===")
        
        # キーワードベースの階層タイプ推定
        type_keywords = {
            "vision": ["ビジョン", "戦略", "目標", "ミッション"],
            "architecture": ["システム", "アーキテクチャ", "基盤", "全体"],
            "module": ["モジュール", "サブシステム", "機能群"],
            "component": ["コンポーネント", "機能", "要件", "アルゴリズム"],
            "task": ["タスク", "実装", "詳細", "具体的"]
        }
        
        # 各要件のタイトルと説明から階層タイプを推定
        requirements_query = """
        MATCH (r:RequirementEntity)
        RETURN r.id, r.title, r.description, r.hierarchy_level
        """
        
        result = self.executor.execute(requirements_query)
        
        for req_id, title, description, current_level in result.get("data", []):
            # キーワードマッチング
            text = f"{title} {description}".lower()
            
            for level, def_info in self.hierarchy_definitions.items():
                type_name = def_info["name"]
                keywords = type_keywords.get(type_name, [])
                
                if any(keyword.lower() in text for keyword in keywords):
                    # 推定された階層タイプを設定
                    update_query = """
                    MATCH (r:RequirementEntity {id: $req_id})
                    SET r.estimated_hierarchy_type = $type_name
                    """
                    self.executor.execute(update_query, {
                        "req_id": req_id,
                        "type_name": type_name
                    })
                    break
    
    def create_hierarchy_view(self) -> str:
        """
        階層構造の視覚的表現を生成
        """
        view_query = """
        MATCH path = (root:RequirementEntity)-[:DEPENDS_ON*0..]->(leaf:RequirementEntity)
        WHERE root.hierarchy_level = 1
        RETURN path
        """
        
        # 簡略化された階層ビューを返す
        hierarchy_view = []
        
        # 各レベルごとに要件を取得
        for level in range(5):
            level_query = """
            MATCH (r:RequirementEntity)
            WHERE r.hierarchy_level = $level
            RETURN r.title
            ORDER BY r.title
            """
            
            result = self.executor.execute(level_query, {"level": level})
            
            if result.get("data"):
                hierarchy_view.append(f"\nLevel {level} ({self.hierarchy_definitions.get(level, {}).get('name', 'unknown')}):")
                for title, in result["data"]:
                    hierarchy_view.append(f"  {'  ' * level}└─ {title}")
        
        return "\n".join(hierarchy_view)


def demonstrate_dynamic_hierarchy():
    """動的階層管理のデモンストレーション"""
    # KuzuDB接続
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "kuzu", 
        "/home/nixos/bin/src/.venv/lib/python3.11/site-packages/kuzu/__init__.py"
    )
    kuzu = importlib.util.module_from_spec(spec)
    sys.modules['kuzu'] = kuzu
    spec.loader.exec_module(kuzu)
    
    db = kuzu.Database("/home/nixos/bin/src/kuzu/kuzu_db")
    conn = kuzu.Connection(db)
    
    # 動的階層マネージャーを作成
    manager = DynamicHierarchyManager(conn)
    
    print("=== 動的階層管理システムのデモンストレーション ===\n")
    
    # 1. 階層レベルを自動計算
    print("1. 階層レベルの自動計算:")
    hierarchy_levels = manager.calculate_hierarchy_levels()
    
    # 2. データベースに階層情報を保存
    if hierarchy_levels:
        manager.update_hierarchy_properties(hierarchy_levels)
    
    # 3. 階層ルールの検証
    violations = manager.validate_hierarchy_rules()
    
    # 4. 統計情報の表示
    print("\n=== 階層統計情報 ===")
    stats = manager.get_hierarchy_statistics()
    print(f"総要件数: {stats['total_requirements']}")
    print(f"階層範囲: Level {stats['min_level']} - Level {stats['max_level']}")
    print("各レベルの要件数:")
    for level, count in sorted(stats['level_counts'].items()):
        hierarchy_name = manager.hierarchy_definitions.get(level, {}).get('name', 'unknown')
        print(f"  Level {level} ({hierarchy_name}): {count}件")
    
    # 5. 階層タイプの自動推定
    manager.auto_assign_hierarchy_type()
    
    # 6. 階層ビューの表示
    print("\n=== 階層構造ビュー ===")
    view = manager.create_hierarchy_view()
    print(view)
    
    print("\n=== 動的階層管理の利点 ===")
    print("✓ 階層レベルが自動計算される")
    print("✓ 新しい要件追加時も自動的に適切な階層に配置")
    print("✓ 階層ルール違反を自動検出")
    print("✓ 階層定義を柔軟に変更可能")
    print("✓ 統計情報で全体構造を把握")


if __name__ == "__main__":
    demonstrate_dynamic_hierarchy()