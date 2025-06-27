"""
要件管理システムの最適化機能実装
新DDLスキーマ対応版
"""
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, deque
import math


def optimize_implementation_order_with_layers(
    requirements: List[Dict], 
    code_entities: List[Dict], 
    implementation_relations: List[Tuple], 
    dependencies: List[Tuple]
) -> List[str]:
    """
    技術レイヤーを考慮した実装順序の最適化
    DB層→API層→UI層の順序を基本とする
    """
    # レイヤー優先度定義
    layer_priority = {
        "database": 1,
        "infrastructure": 2,
        "domain": 3,
        "api": 4,
        "service": 5,
        "ui": 6,
        "frontend": 7
    }
    
    # 要件IDとコードエンティティのマッピング
    req_to_code = {}
    for req_id, code_id, _ in implementation_relations:
        req_to_code[req_id] = code_id
    
    # コードエンティティの型マッピング
    code_types = {ce["persistent_id"]: ce["type"] for ce in code_entities}
    
    # 依存グラフ構築
    dep_graph = defaultdict(list)
    in_degree = defaultdict(int)
    
    for from_req, to_req, _ in dependencies:
        dep_graph[to_req].append(from_req)
        in_degree[from_req] += 1
    
    # トポロジカルソート with レイヤー優先度
    queue = []
    for req in requirements:
        if in_degree[req["id"]] == 0:
            code_id = req_to_code.get(req["id"])
            if code_id and code_id in code_types:
                priority = layer_priority.get(code_types[code_id], 999)
            else:
                priority = 999
            queue.append((priority, req["id"]))
    
    queue.sort()  # 優先度順
    result = []
    
    while queue:
        _, req_id = queue.pop(0)
        result.append(req_id)
        
        for dependent in dep_graph[req_id]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                code_id = req_to_code.get(dependent)
                if code_id and code_id in code_types:
                    priority = layer_priority.get(code_types[code_id], 999)
                else:
                    priority = 999
                queue.append((priority, dependent))
                queue.sort()
    
    return result


def find_critical_path(dependencies_graph: Dict[str, List[str]]) -> List[str]:
    """
    依存グラフから最長パス（クリティカルパス）を検出
    """
    # 終端ノード（依存先がないノード）を見つける
    all_nodes = set(dependencies_graph.keys())
    for deps in dependencies_graph.values():
        all_nodes.update(deps)
    
    terminal_nodes = [node for node in all_nodes if node not in dependencies_graph or not dependencies_graph[node]]
    
    # 各ノードへの最長パス長を計算
    distances = {}
    parent_map = {}
    
    def calculate_distance(node: str) -> int:
        if node in distances:
            return distances[node]
        
        if node not in dependencies_graph or not dependencies_graph[node]:
            distances[node] = 0
            return 0
        
        max_dist = 0
        best_child = None
        
        for child in dependencies_graph[node]:
            dist = calculate_distance(child) + 1
            if dist > max_dist:
                max_dist = dist
                best_child = child
        
        distances[node] = max_dist
        if best_child:
            parent_map[node] = best_child
        
        return max_dist
    
    # 全ノードから最長パスを探索
    max_length = 0
    start_node = None
    
    for node in dependencies_graph:
        length = calculate_distance(node)
        if length > max_length:
            max_length = length
            start_node = node
    
    # パスを構築
    path = []
    current = start_node
    while current:
        path.append(current)
        current = parent_map.get(current)
    
    return path


def calculate_foundation_priority(
    requirements: List[Dict], 
    dependencies: List[Tuple[str, str]]
) -> Dict[str, float]:
    """
    共通基盤の優先度を計算
    多くの要件から依存されるほど高スコア
    """
    # 依存カウント
    dep_count = defaultdict(int)
    reverse_deps = defaultdict(set)
    
    for from_req, to_req in dependencies:
        dep_count[to_req] += 1
        reverse_deps[to_req].add(from_req)
    
    # 推移的な依存も考慮
    def count_transitive_deps(req_id: str, visited: Set[str]) -> int:
        if req_id in visited:
            return 0
        visited.add(req_id)
        
        count = len(reverse_deps[req_id])
        for dep in reverse_deps[req_id]:
            count += count_transitive_deps(dep, visited)
        
        return count
    
    scores = {}
    for req in requirements:
        req_id = req["id"]
        direct_count = dep_count[req_id]
        transitive_count = count_transitive_deps(req_id, set())
        
        # スコア = 直接依存数 + 推移的依存数 * 0.5
        scores[req_id] = direct_count + transitive_count * 0.5
    
    return scores


def suggest_requirement_split(
    requirement: Dict,
    code_entities: List[Dict],
    threshold: int = 50
) -> Optional[List[Dict]]:
    """
    複雑度に基づく要件分割提案
    """
    total_complexity = sum(ce.get("complexity", 0) for ce in code_entities)
    
    if total_complexity <= threshold:
        return None
    
    # 機能単位で分割を提案
    suggestions = []
    
    # コードエンティティをタイプ別にグループ化
    type_groups = defaultdict(list)
    for ce in code_entities:
        type_groups[ce.get("type", "unknown")].append(ce)
    
    # 各グループを独立した要件として提案
    for ce_type, entities in type_groups.items():
        group_complexity = sum(e.get("complexity", 0) for e in entities)
        if group_complexity > 0:
            suggestions.append({
                "title": f"{requirement['title']} - {ce_type}部分",
                "estimated_complexity": group_complexity,
                "code_entities": [e["persistent_id"] for e in entities]
            })
    
    return suggestions if len(suggestions) > 1 else None


def check_technical_feasibility(
    requirement: Dict,
    references: List[Dict],
    existing_code: List[Dict]
) -> Dict[str, any]:
    """
    技術的実現可能性をチェック
    """
    issues = []
    confidence = 1.0
    
    # 外部参照の利用可能性チェック
    for ref in references:
        if ref.get("source_type") == "external":
            if ref.get("type") == "library":
                # ライブラリの互換性チェック（簡易版）
                if "deprecated" in ref.get("description", "").lower():
                    issues.append(f"Library {ref['id']} may be deprecated")
                    confidence *= 0.8
            elif ref.get("type") == "specification":
                # 仕様の実装難易度（簡易版）
                if "draft" in ref.get("description", "").lower():
                    issues.append(f"Specification {ref['id']} is still in draft")
                    confidence *= 0.9
    
    # 既存コードとの統合性チェック
    integration_complexity = 0
    for code in existing_code:
        if code.get("type") in ["legacy", "external"]:
            integration_complexity += code.get("complexity", 0) * 0.5
    
    if integration_complexity > 100:
        issues.append("High integration complexity with existing code")
        confidence *= 0.7
    
    return {
        "feasible": confidence > 0.5,
        "confidence": confidence,
        "issues": issues,
        "recommendations": [
            "Consider phased implementation" if confidence < 0.7 else "Direct implementation possible"
        ]
    }


def extract_common_components(
    requirements: List[Dict],
    code_entities: List[Dict],
    implementation_relations: List[Tuple]
) -> List[Dict]:
    """
    共通コンポーネントを抽出
    """
    # 要件ごとのコードエンティティをマッピング
    req_to_codes = defaultdict(set)
    for req_id, code_id, _ in implementation_relations:
        req_to_codes[req_id].add(code_id)
    
    # コードエンティティの詳細マッピング
    code_details = {ce["persistent_id"]: ce for ce in code_entities}
    
    # 類似性に基づく共通コンポーネント候補
    common_candidates = defaultdict(list)
    
    for ce in code_entities:
        # シグネチャやタイプに基づくグループ化
        key = (ce.get("type"), ce.get("name", "").split("_")[0])  # 簡易的な類似性判定
        common_candidates[key].append(ce["persistent_id"])
    
    # 2つ以上の要件で使われる可能性のあるコンポーネント
    common_components = []
    
    for key, code_ids in common_candidates.items():
        if len(code_ids) > 1:
            # 実際に複数の要件から参照されているか確認
            referring_reqs = set()
            for req_id, codes in req_to_codes.items():
                if any(cid in codes for cid in code_ids):
                    referring_reqs.add(req_id)
            
            if len(referring_reqs) > 1:
                common_components.append({
                    "component_type": key[0],
                    "component_base": key[1],
                    "code_entities": code_ids,
                    "used_by_requirements": list(referring_reqs),
                    "potential_savings": len(code_ids) - 1  # 重複実装を避けられる数
                })
    
    return common_components


def estimate_effort(
    requirement: Dict,
    code_entities: List[Dict],
    dependencies: List[str],
    team_velocity: float = 1.0
) -> Dict[str, float]:
    """
    工数見積もり
    """
    # 基本工数 = 複雑度の合計
    base_effort = sum(ce.get("complexity", 10) for ce in code_entities)
    
    # 依存関係による追加工数
    dependency_factor = 1.0 + (len(dependencies) * 0.1)
    
    # コードエンティティの種類による調整
    type_factors = {
        "database": 1.5,  # DB設計は時間がかかる
        "api": 1.2,
        "ui": 1.3,  # UI実装も時間がかかる
        "function": 1.0,
        "class": 1.1
    }
    
    type_adjustment = 1.0
    for ce in code_entities:
        ce_type = ce.get("type", "function")
        type_adjustment += (type_factors.get(ce_type, 1.0) - 1.0) / len(code_entities)
    
    # 最終工数計算
    total_effort = base_effort * dependency_factor * type_adjustment / team_velocity
    
    # 工数を時間単位に変換（複雑度10 = 1時間と仮定）
    hours = total_effort / 10
    
    return {
        "estimated_hours": round(hours, 1),
        "estimated_days": round(hours / 8, 1),
        "confidence_range": {
            "optimistic": round(hours * 0.7, 1),
            "pessimistic": round(hours * 1.5, 1)
        },
        "breakdown": {
            "base_complexity": base_effort,
            "dependency_factor": dependency_factor,
            "type_adjustment": type_adjustment
        }
    }


# In-source tests
def test_optimize_implementation_order_レイヤー順序_正しく並ぶ():
    """optimize_implementation_order_with_layers_DB→API→UI_正しい順序"""
    requirements = [
        {"id": "ui", "title": "UI"},
        {"id": "api", "title": "API"},
        {"id": "db", "title": "DB"}
    ]
    code_entities = [
        {"persistent_id": "ui_code", "type": "ui"},
        {"persistent_id": "api_code", "type": "api"},
        {"persistent_id": "db_code", "type": "database"}
    ]
    implementation_relations = [
        ("ui", "ui_code", "direct"),
        ("api", "api_code", "direct"),
        ("db", "db_code", "direct")
    ]
    dependencies = [
        ("ui", "api", "technical"),
        ("api", "db", "technical")
    ]
    
    result = optimize_implementation_order_with_layers(
        requirements, code_entities, implementation_relations, dependencies
    )
    
    assert result == ["db", "api", "ui"]


def test_find_critical_path_ダイヤモンド_最長パス():
    """find_critical_path_ダイヤモンド依存_最長パスを返す"""
    graph = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        "D": [],
    }
    
    path = find_critical_path(graph)
    
    assert len(path) == 3
    assert path[0] == "A"
    assert path[-1] == "D"


def test_calculate_foundation_priority_共通基盤_高スコア():
    """calculate_foundation_priority_複数依存_高優先度"""
    requirements = [
        {"id": "A", "title": "A"},
        {"id": "B", "title": "B"},
        {"id": "common", "title": "Common"}
    ]
    dependencies = [
        ("A", "common"),
        ("B", "common")
    ]
    
    scores = calculate_foundation_priority(requirements, dependencies)
    
    assert scores["common"] > scores["A"]
    assert scores["common"] > scores["B"]
