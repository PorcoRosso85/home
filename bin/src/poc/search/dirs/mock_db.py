#!/usr/bin/env python3
"""Mock database for testing without KuzuDB - 規約準拠版"""

from typing import Dict, List, Any, Optional


def create_mock_result(data: Optional[List[Any]]) -> Dict[str, Any]:
    """モック結果オブジェクトを作成
    
    Args:
        data: 結果データのリスト
        
    Returns:
        結果を表す辞書
    """
    return {
        'data': data or [],
        'index': 0
    }


def has_next(result: Dict[str, Any]) -> bool:
    """次の結果があるか確認
    
    Args:
        result: 結果辞書
        
    Returns:
        True: 次の結果あり
        False: 次の結果なし
    """
    return result['index'] < len(result['data'])


def get_next(result: Dict[str, Any]) -> Optional[Any]:
    """次の結果を取得
    
    Args:
        result: 結果辞書
        
    Returns:
        次の結果データまたはNone
    """
    if has_next(result):
        data = result['data'][result['index']]
        result['index'] += 1
        return data
    return None


def create_mock_connection() -> Dict[str, Any]:
    """モック接続オブジェクトを作成
    
    Returns:
        接続を表す辞書
    """
    return {
        'nodes': {},
        'node_counter': 0
    }


def execute_query(conn: Dict[str, Any], query: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """クエリを実行（モック実装）
    
    Args:
        conn: 接続辞書
        query: 実行するクエリ
        params: クエリパラメータ
        
    Returns:
        結果を表す辞書
    """
    query_lower = query.lower()
    
    # CREATE NODE TABLE
    if "create node table" in query_lower:
        return create_mock_result([])
    
    # CREATE node
    if query_lower.startswith("create ("):
        # Extract node type
        if ":directory" in query_lower:
            node_id = f"dir_{conn['node_counter']}"
            conn['nodes'][node_id] = params or {}
            conn['node_counter'] += 1
        elif ":readme" in query_lower:
            node_id = f"readme_{conn['node_counter']}"
            conn['nodes'][node_id] = params or {}
            conn['node_counter'] += 1
        return create_mock_result([])
    
    # MATCH and DELETE
    if query_lower.startswith("match") and "delete" in query_lower:
        if ":directory" in query_lower:
            conn['nodes'] = {k: v for k, v in conn['nodes'].items() if not k.startswith("dir_")}
        elif ":readme" in query_lower:
            conn['nodes'] = {k: v for k, v in conn['nodes'].items() if not k.startswith("readme_")}
        return create_mock_result([])
    
    # MATCH and RETURN count
    if "return count(*)" in query_lower:
        if ":directory" in query_lower:
            # Check for WHERE clause about embeddings
            if "where d.embedding is not null" in query_lower:
                count = sum(1 for k, v in conn['nodes'].items() 
                           if k.startswith("dir_") and v.get('embedding'))
            else:
                count = sum(1 for k in conn['nodes'] if k.startswith("dir_"))
            return create_mock_result([[count]])
        return create_mock_result([[0]])
    
    # MATCH and RETURN path
    if "return d.path" in query_lower:
        paths = []
        for k, v in conn['nodes'].items():
            if k.startswith("dir_") and 'path' in v:
                paths.append([v['path']])
        return create_mock_result(paths)
    
    # MATCH specific node
    if "return d.has_readme" in query_lower:
        if params and 'path' in params:
            for k, v in conn['nodes'].items():
                if k.startswith("dir_") and v.get('path') == params['path']:
                    return create_mock_result([[v.get('has_readme', False)]])
        return create_mock_result([])
    
    # Default empty result
    return create_mock_result([])


def create_mock_connection_wrapper() -> Any:
    """KuzuDB互換のモック接続を作成
    
    Returns:
        execute メソッドを持つオブジェクト
    """
    conn = create_mock_connection()
    
    # 辞書の代わりにMockConnectionObjectを使用
    class MockConnectionObject:
        def execute(self, query: str, params: Optional[Dict[str, Any]] = None):
            return MockResultWrapper(execute_query(conn, query, params))
    
    return MockConnectionObject()


class MockResultWrapper:
    """結果ラッパー（互換性のため最小限のクラス使用）"""
    def __init__(self, result: Dict[str, Any]):
        self._result = result
    
    def has_next(self) -> bool:
        return has_next(self._result)
    
    def get_next(self) -> Optional[Any]:
        return get_next(self._result)


def get_mock_connection(db_path: str) -> Any:
    """モック接続を取得
    
    Args:
        db_path: データベースパス（使用されない）
        
    Returns:
        モック接続オブジェクト
    """
    return create_mock_connection_wrapper()