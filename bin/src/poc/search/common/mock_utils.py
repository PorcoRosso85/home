#!/usr/bin/env python3
"""
テスト用モックユーティリティ（クラス不使用）
"""

from typing import List, Dict, Any, Callable


def create_mock_connection(data: List[List[Any]] = None) -> Dict[str, Any]:
    """
    モック接続オブジェクトを作成
    
    Args:
        data: クエリ結果として返すデータ
        
    Returns:
        execute, has_next, get_nextメソッドを持つ辞書
    """
    connection_state = {
        "data": data or [],
        "current_result": None
    }
    
    def execute(query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """クエリ実行をモック"""
        # 新しい結果オブジェクトを作成
        result_state = {
            "data": connection_state["data"],
            "index": 0
        }
        
        def has_next() -> bool:
            return result_state["index"] < len(result_state["data"])
        
        def get_next() -> List[Any]:
            if has_next():
                value = result_state["data"][result_state["index"]]
                result_state["index"] += 1
                return value
            return None
        
        result = {
            "has_next": has_next,
            "get_next": get_next
        }
        
        connection_state["current_result"] = result
        return result
    
    return {
        "execute": execute,
        "state": connection_state
    }


def create_mock_requirement(req_id: str, title: str, description: str) -> Dict[str, Any]:
    """モック要件データを作成"""
    return {
        "id": req_id,
        "title": title,
        "description": description,
        "status": "proposed",
        "priority": 1
    }


def create_mock_node(properties: Dict[str, Any]) -> Dict[str, Any]:
    """KuzuDBのノードオブジェクトをモック"""
    def get(key: str, default: Any = None) -> Any:
        return properties.get(key, default)
    
    def __getitem__(key: str) -> Any:
        return properties[key]
    
    return {
        **properties,
        "get": get,
        "__getitem__": __getitem__
    }