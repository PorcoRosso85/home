"""
循環参照検出器（インフラ層）
要件間の依存関係グラフから循環参照を検出
"""
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


class CircularReferenceDetector:
    """循環参照を検出"""
    
    def detect_cycles(self, dependencies: List[Tuple[str, str]]) -> Dict[str, any]:
        """
        依存関係グラフから循環参照を検出
        
        Args:
            dependencies: (from_id, to_id)のタプルリスト
            
        Returns:
            検出結果の辞書
        """
        # グラフを構築
        graph = defaultdict(list)
        all_nodes = set()
        
        for from_id, to_id in dependencies:
            graph[from_id].append(to_id)
            all_nodes.add(from_id)
            all_nodes.add(to_id)
        
        # 循環を検出
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            """DFSを使用して循環を検出"""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # 循環を発見
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        # すべてのノードから探索
        for node in all_nodes:
            if node not in visited:
                dfs(node)
        
        # 自己参照を検出
        self_references = []
        for from_id, to_id in dependencies:
            if from_id == to_id:
                self_references.append(from_id)
        
        return {
            "has_cycles": len(cycles) > 0 or len(self_references) > 0,
            "cycles": cycles,
            "self_references": list(set(self_references)),
            "total_violations": len(cycles) + len(set(self_references))
        }
    
    def find_all_cycles(self, dependencies: List[Tuple[str, str]]) -> List[List[str]]:
        """
        すべての循環を検出（Tarjanのアルゴリズム）
        
        Args:
            dependencies: (from_id, to_id)のタプルリスト
            
        Returns:
            検出されたすべての循環のリスト
        """
        # グラフを構築
        graph = defaultdict(list)
        for from_id, to_id in dependencies:
            graph[from_id].append(to_id)
        
        # Tarjanのアルゴリズムで強連結成分を見つける
        index = 0
        stack = []
        indices = {}
        lowlinks = {}
        on_stack = set()
        sccs = []
        
        def strongconnect(v):
            nonlocal index
            indices[v] = index
            lowlinks[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)
            
            for w in graph.get(v, []):
                if w not in indices:
                    strongconnect(w)
                    lowlinks[v] = min(lowlinks[v], lowlinks[w])
                elif w in on_stack:
                    lowlinks[v] = min(lowlinks[v], indices[w])
            
            if lowlinks[v] == indices[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.append(w)
                    if w == v:
                        break
                if len(scc) > 1:  # 循環がある場合
                    sccs.append(list(reversed(scc)))
        
        for v in graph:
            if v not in indices:
                strongconnect(v)
        
        return sccs


def create_cypher_cycle_query() -> str:
    """
    循環参照を検出するCypherクエリを生成
    
    Returns:
        Cypherクエリ文字列
    """
    return """
    // 自己参照を検出
    MATCH (r:RequirementEntity)-[:DEPENDS_ON]->(r)
    RETURN r.id as self_reference_id
    
    UNION
    
    // 循環参照を検出（最大深さ10まで）
    MATCH path = (start:RequirementEntity)-[:DEPENDS_ON*2..10]->(start)
    RETURN start.id as cycle_start_id, 
           [node in nodes(path) | node.id] as cycle_path
    """


def validate_with_kuzu(connection) -> Dict[str, any]:
    """
    KuzuDBを使用して循環参照を検証
    
    Args:
        connection: KuzuDB接続
        
    Returns:
        検証結果
    """
    result = {
        "has_cycles": False,
        "cycles": [],
        "self_references": [],
        "total_violations": 0
    }
    
    # 自己参照を検出
    self_ref_query = """
    MATCH (r:RequirementEntity)-[:DEPENDS_ON]->(r)
    RETURN r.id as self_reference_id
    """
    
    self_ref_result = connection.execute(self_ref_query)
    while self_ref_result.has_next():
        row = self_ref_result.get_next()
        result["self_references"].append(row[0])
    
    # 循環参照を検出（パスの長さを変えて探索）
    for length in range(2, 11):  # 2から10までの長さ
        cycle_query = f"""
        MATCH path = (start:RequirementEntity)-[:DEPENDS_ON*{length}]->(start)
        RETURN DISTINCT start.id as cycle_start_id, 
               [node in nodes(path) | node.id] as cycle_path
        LIMIT 100
        """
        
        cycle_result = connection.execute(cycle_query)
        while cycle_result.has_next():
            row = cycle_result.get_next()
            cycle_path = row[1]
            # 重複を避けるため、正規化（最小IDから開始）
            min_idx = cycle_path.index(min(cycle_path))
            normalized_cycle = cycle_path[min_idx:] + cycle_path[:min_idx]
            
            # まだ追加されていない循環のみ追加
            if normalized_cycle not in result["cycles"]:
                result["cycles"].append(normalized_cycle)
    
    result["has_cycles"] = len(result["cycles"]) > 0 or len(result["self_references"]) > 0
    result["total_violations"] = len(result["cycles"]) + len(result["self_references"])
    
    return result


def get_cycle_impact_score(cycle_length: int) -> int:
    """
    循環の長さに基づいて影響スコアを計算
    
    Args:
        cycle_length: 循環の長さ
        
    Returns:
        影響スコア（負の値）
    """
    if cycle_length == 1:  # 自己参照
        return -100
    elif cycle_length <= 3:  # 短い循環
        return -80
    elif cycle_length <= 5:  # 中程度の循環
        return -60
    else:  # 長い循環
        return -40