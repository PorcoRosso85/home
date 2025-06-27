#!/usr/bin/env python3
"""
動的階層管理システム - 代替実装
LocationURIとエッジの関係から階層レベルを動的に計算
"""
import sys
import os
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

# 環境変数設定
os.environ["LD_LIBRARY_PATH"] = "/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/"
os.environ["RGL_DB_PATH"] = "/home/nixos/bin/src/kuzu/kuzu_db"

from graph.infrastructure.cypher_executor import CypherExecutor


class AlternativeHierarchyAnalyzer:
    """LocationURIの関係から階層を動的に分析"""
    
    def __init__(self, connection):
        self.executor = CypherExecutor(connection)
        self.hierarchy_info = {}  # req_id -> hierarchy_info
    
    def analyze_dynamic_hierarchy(self) -> Dict[str, Dict]:
        """
        既存のCONTAINS_LOCATION関係から階層構造を動的に分析
        """
        print("=== 動的階層分析（ハードコーディングなし） ===\n")
        
        # 1. ルートノードを動的に検出（親を持たないLocationURI）
        root_query = """
        MATCH (l:LocationURI)
        WHERE NOT (:LocationURI)-[:CONTAINS_LOCATION]->(l)
        MATCH (l)-[:LOCATES_LocationURI_RequirementEntity]->(r:RequirementEntity)
        RETURN l.id as loc_id, r.id as req_id, r.title
        """
        
        result = self.executor.execute(root_query)
        
        roots = []
        for loc_id, req_id, title in result.get("data", []):
            roots.append({
                "loc_id": loc_id,
                "req_id": req_id,
                "title": title,
                "level": 0  # ルートは常にレベル0
            })
            self.hierarchy_info[req_id] = {
                "level": 0,
                "title": title,
                "parent": None,
                "children": []
            }
        
        print(f"検出されたルート要件: {len(roots)}件")
        for root in roots:
            print(f"  - {root['title']} (Level 0)")
        
        # 2. 再帰的に子要件を探索し、階層レベルを動的に割り当て
        self._explore_children_recursively(roots)
        
        return self.hierarchy_info
    
    def _explore_children_recursively(self, nodes: List[Dict], current_level: int = 0):
        """子要件を再帰的に探索"""
        if not nodes:
            return
        
        next_level_nodes = []
        
        for node in nodes:
            # このノードの子を取得
            children_query = """
            MATCH (parent:LocationURI {id: $parent_loc_id})-[:CONTAINS_LOCATION]->(child:LocationURI)
            MATCH (child)-[:LOCATES_LocationURI_RequirementEntity]->(r:RequirementEntity)
            RETURN child.id as loc_id, r.id as req_id, r.title
            """
            
            result = self.executor.execute(children_query, {"parent_loc_id": node["loc_id"]})
            
            for child_loc_id, child_req_id, child_title in result.get("data", []):
                child_level = current_level + 1
                
                # 階層情報を記録
                self.hierarchy_info[child_req_id] = {
                    "level": child_level,
                    "title": child_title,
                    "parent": node["req_id"],
                    "children": []
                }
                
                # 親の子リストに追加
                if node["req_id"] in self.hierarchy_info:
                    self.hierarchy_info[node["req_id"]]["children"].append(child_req_id)
                
                next_level_nodes.append({
                    "loc_id": child_loc_id,
                    "req_id": child_req_id,
                    "title": child_title,
                    "level": child_level
                })
                
                print(f"  {'  ' * child_level}└─ {child_title} (Level {child_level})")
        
        # 次のレベルを探索
        if next_level_nodes:
            self._explore_children_recursively(next_level_nodes, current_level + 1)
    
    def get_hierarchy_statistics(self) -> Dict:
        """階層の統計情報を動的に計算"""
        stats = {
            "total_requirements": len(self.hierarchy_info),
            "level_distribution": defaultdict(int),
            "max_depth": 0,
            "avg_children_per_node": 0,
            "leaf_nodes": 0,
            "branch_nodes": 0
        }
        
        total_children = 0
        
        for req_id, info in self.hierarchy_info.items():
            level = info["level"]
            stats["level_distribution"][level] += 1
            stats["max_depth"] = max(stats["max_depth"], level)
            
            children_count = len(info["children"])
            total_children += children_count
            
            if children_count == 0:
                stats["leaf_nodes"] += 1
            else:
                stats["branch_nodes"] += 1
        
        if stats["branch_nodes"] > 0:
            stats["avg_children_per_node"] = total_children / stats["branch_nodes"]
        
        return stats
    
    def generate_dynamic_hierarchy_report(self) -> str:
        """動的に階層レポートを生成"""
        report = []
        report.append("=== 動的階層構造レポート ===\n")
        
        # 統計情報
        stats = self.get_hierarchy_statistics()
        report.append(f"総要件数: {stats['total_requirements']}")
        report.append(f"最大階層深さ: {stats['max_depth'] + 1}レベル")
        report.append(f"葉ノード: {stats['leaf_nodes']}件")
        report.append(f"分岐ノード: {stats['branch_nodes']}件")
        report.append(f"平均子要件数: {stats['avg_children_per_node']:.2f}\n")
        
        # レベル別分布
        report.append("レベル別要件数（動的に計算）:")
        for level in sorted(stats["level_distribution"].keys()):
            count = stats["level_distribution"][level]
            percentage = (count / stats["total_requirements"]) * 100
            report.append(f"  Level {level}: {count}件 ({percentage:.1f}%)")
        
        # 階層パスの例
        report.append("\n階層パスの例:")
        paths = self._get_sample_paths(3)
        for path in paths:
            report.append(f"  {' -> '.join(path)}")
        
        return "\n".join(report)
    
    def _get_sample_paths(self, count: int) -> List[List[str]]:
        """サンプル階層パスを取得"""
        paths = []
        
        # ルートから葉までのパスを構築
        for req_id, info in self.hierarchy_info.items():
            if len(info["children"]) == 0:  # 葉ノード
                path = []
                current = req_id
                
                # ルートまで遡る
                while current:
                    path.insert(0, self.hierarchy_info[current]["title"])
                    current = self.hierarchy_info[current]["parent"]
                
                paths.append(path)
                
                if len(paths) >= count:
                    break
        
        return paths
    
    def validate_dynamic_consistency(self) -> List[Dict]:
        """動的に階層の一貫性を検証"""
        issues = []
        
        # 1. 循環参照のチェック
        for req_id in self.hierarchy_info:
            visited = set()
            current = req_id
            
            while current:
                if current in visited:
                    issues.append({
                        "type": "circular_reference",
                        "requirement": req_id,
                        "message": f"循環参照が検出されました: {req_id}"
                    })
                    break
                
                visited.add(current)
                current = self.hierarchy_info.get(current, {}).get("parent")
        
        # 2. 孤立ノードのチェック
        all_req_ids = set(self.hierarchy_info.keys())
        connected_ids = set()
        
        for info in self.hierarchy_info.values():
            if info["parent"]:
                connected_ids.add(info["parent"])
            connected_ids.update(info["children"])
        
        # 実際にはルートノードは孤立していないので除外
        orphaned = all_req_ids - connected_ids
        roots = {req_id for req_id, info in self.hierarchy_info.items() if info["level"] == 0}
        orphaned = orphaned - roots
        
        for req_id in orphaned:
            issues.append({
                "type": "orphaned_node",
                "requirement": req_id,
                "message": f"孤立した要件: {self.hierarchy_info[req_id]['title']}"
            })
        
        return issues


def demonstrate_alternative_hierarchy():
    """代替階層管理システムのデモンストレーション"""
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
    
    # 動的階層アナライザーを作成
    analyzer = AlternativeHierarchyAnalyzer(conn)
    
    # 1. 階層構造を動的に分析
    hierarchy_info = analyzer.analyze_dynamic_hierarchy()
    
    # 2. レポートを生成
    print("\n" + analyzer.generate_dynamic_hierarchy_report())
    
    # 3. 一貫性を検証
    print("\n=== 階層一貫性検証 ===")
    issues = analyzer.validate_dynamic_consistency()
    if issues:
        for issue in issues:
            print(f"⚠️  {issue['type']}: {issue['message']}")
    else:
        print("✓ 階層構造に問題はありません")
    
    # 4. 動的階層管理の利点
    print("\n=== 動的階層管理の利点（ハードコーディングなし） ===")
    print("✓ 階層レベルの定義が不要（0,1,2...は単なる深さ）")
    print("✓ 階層名（vision/architecture等）に依存しない")
    print("✓ 既存の関係（CONTAINS_LOCATION）から自動的に階層を導出")
    print("✓ 新しい要件追加時も自動的に適切な位置に配置")
    print("✓ 階層の深さ制限なし（データ構造が許す限り）")
    print("✓ スキーマ変更不要")


if __name__ == "__main__":
    demonstrate_alternative_hierarchy()