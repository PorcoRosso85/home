"""
グラフ深さ検証器（インフラ層）
要件間の依存関係グラフの深さを検証
"""
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque


class GraphDepthValidator:
    """グラフの深さ制限を検証"""
    
    def __init__(self, max_depth: Optional[int] = None):
        """
        Args:
            max_depth: 許可される最大グラフ深さ（Noneの場合は無制限）
        """
        self.max_depth = max_depth
    
    def validate_graph_depth(self, dependencies: List[Tuple[str, str]]) -> Dict[str, any]:
        """
        依存関係グラフの深さを検証
        
        Args:
            dependencies: (from_id, to_id)のタプルリスト
            
        Returns:
            検証結果の辞書
        """
        # グラフを構築
        graph = defaultdict(list)
        reverse_graph = defaultdict(list)
        all_nodes = set()
        
        for from_id, to_id in dependencies:
            graph[from_id].append(to_id)
            reverse_graph[to_id].append(from_id)
            all_nodes.add(from_id)
            all_nodes.add(to_id)
        
        # ルートノード（依存されていないノード）を見つける
        root_nodes = [node for node in all_nodes if node not in reverse_graph]
        
        # 各ノードの深さを計算
        node_depths = self._calculate_depths(graph, root_nodes)
        
        # 最大深さを超えているパスを検出
        violations = []
        if self.max_depth is not None:
            for node, depth in node_depths.items():
                if depth > self.max_depth:
                    path = self._find_longest_path_to_node(reverse_graph, node)
                    violations.append({
                        "node": node,
                        "depth": depth,
                        "max_allowed": self.max_depth,
                        "path": path
                    })
        
        return {
            "is_valid": len(violations) == 0,
            "max_depth_found": max(node_depths.values()) if node_depths else 0,
            "violations": violations,
            "node_depths": dict(node_depths)
        }
    
    def _calculate_depths(self, graph: Dict[str, List[str]], root_nodes: List[str]) -> Dict[str, int]:
        """各ノードの深さを計算（BFS）"""
        depths = {}
        queue = deque([(node, 0) for node in root_nodes])
        
        while queue:
            node, depth = queue.popleft()
            
            # より深いパスが見つかった場合は更新
            if node not in depths or depth > depths[node]:
                depths[node] = depth
                
                # 子ノードをキューに追加
                for child in graph.get(node, []):
                    queue.append((child, depth + 1))
        
        return depths
    
    def _find_longest_path_to_node(self, reverse_graph: Dict[str, List[str]], target: str) -> List[str]:
        """ターゲットノードへの最長パスを見つける"""
        # DFSで最長パスを探索
        def dfs(node: str, visited: Set[str], path: List[str]) -> List[str]:
            if node not in reverse_graph:
                return path + [node]
            
            longest_path = path + [node]
            for parent in reverse_graph[node]:
                if parent not in visited:
                    visited.add(parent)
                    parent_path = dfs(parent, visited.copy(), path + [node])
                    if len(parent_path) > len(longest_path):
                        longest_path = parent_path
            
            return longest_path
        
        return list(reversed(dfs(target, {target}, [])))


def create_cypher_depth_query(max_depth: Optional[int] = None) -> str:
    """
    グラフ深さ制限を確認するCypherクエリを生成
    
    Args:
        max_depth: 最大深さ制限
        
    Returns:
        Cypherクエリ文字列
    """
    if max_depth is None:
        # 深さ制限なしの場合、全パスを返す
        return """
        MATCH path = (start:RequirementEntity)-[:DEPENDS_ON*]->(end:RequirementEntity)
        WHERE NOT (:RequirementEntity)-[:DEPENDS_ON]->(start)
        RETURN start.id as root_id, end.id as leaf_id, length(path) as depth
        ORDER BY depth DESC
        """
    else:
        # 深さ制限を超えるパスを検出
        return f"""
        MATCH path = (start:RequirementEntity)-[:DEPENDS_ON*{max_depth + 1},]->(end:RequirementEntity)
        WHERE NOT (:RequirementEntity)-[:DEPENDS_ON]->(start)
        RETURN start.id as root_id, end.id as leaf_id, length(path) as depth,
               [node in nodes(path) | node.id] as path_ids
        ORDER BY depth DESC
        """


def validate_with_kuzu(connection, max_depth: Optional[int] = None) -> Dict[str, any]:
    """
    KuzuDBを使用してグラフ深さを検証
    
    Args:
        connection: KuzuDB接続
        max_depth: 最大深さ制限
        
    Returns:
        検証結果
    """
    result = {
        "is_valid": True,
        "max_depth_found": 0,
        "violations": []
    }
    
    # 最大深さを取得
    depth_query = """
    MATCH path = (start:RequirementEntity)-[:DEPENDS_ON*]->(end:RequirementEntity)
    WHERE NOT (:RequirementEntity)-[:DEPENDS_ON]->(start)
    RETURN max(length(path)) as max_depth
    """
    
    max_depth_result = connection.execute(depth_query)
    if max_depth_result.has_next():
        result["max_depth_found"] = max_depth_result.get_next()[0] or 0
    
    # 深さ制限がある場合は違反をチェック
    if max_depth is not None and result["max_depth_found"] > max_depth:
        violation_query = create_cypher_depth_query(max_depth)
        violations_result = connection.execute(violation_query)
        
        while violations_result.has_next():
            row = violations_result.get_next()
            result["violations"].append({
                "root_id": row[0],
                "leaf_id": row[1],
                "depth": row[2],
                "path": row[3] if len(row) > 3 else []
            })
        
        result["is_valid"] = False
    
    return result