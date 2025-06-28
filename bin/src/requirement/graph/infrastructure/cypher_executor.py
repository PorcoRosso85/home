"""
Cypher Executor - Cypherクエリ実行層
依存: domain
外部依存: kuzu
"""
from typing import Dict, List, Any, Optional, Union
from .logger import debug, info, warn, error


class CypherExecutor:
    """
    LLMからのCypherクエリを安全に実行するエグゼキュータ
    """
    def __init__(self, connection):
        self.connection = connection
    
    def execute(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Cypherクエリを実行
        
        Args:
            query: Cypherクエリ文字列
            parameters: クエリパラメータ
            
        Returns:
            Dict[str, Any]: 実行結果またはerrorキーを含む辞書
        """
        # 空クエリチェック
        if not query or not query.strip():
            return {
                "error": {
                    "type": "EmptyQueryError",
                    "message": "Query cannot be empty"
                }
            }
        
        try:
            # KuzuDB実行
            result = self.connection.execute(query, parameters)
            
            # 結果をパース
            columns = []
            data = []
            
            # カラム名を推測（簡易実装）
            if "RETURN" in query:
                return_part = query.split("RETURN")[1].split("LIMIT")[0].split("ORDER")[0]
                columns = [col.strip() for col in return_part.split(",")]
            
            # データ取得
            while result.has_next():
                data.append(result.get_next())
            
            debug("rgl.executor", "Returning results", row_count=len(data), column_count=len(columns))
            return {
                "columns": columns,
                "data": data,
                "row_count": len(data)
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # エラータイプを判定
            if "Syntax error" in error_msg or ")" in error_msg or "(" in error_msg:
                error_type = "SyntaxError"
            elif "Connection" in error_msg:
                error_type = "ConnectionError"
            else:
                error_type = "ExecutionError"
            
            error("rgl.executor", "Query execution failed", 
                  error_type=error_type, error_message=error_msg)
            
            return {
                "error": {
                    "type": error_type,
                    "message": error_msg,
                    "query": query
                }
            }
    
    def execute_batch(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        複数のCypherクエリをバッチ実行
        
        Args:
            queries: [{"query": str, "parameters": dict}, ...]
            
        Returns:
            List[Dict[str, Any]]: 各クエリの実行結果
        """
        results = []
        for query_item in queries:
            query = query_item.get("query", "")
            parameters = query_item.get("parameters", None)
            result = self.execute(query, parameters)
            results.append(result)
        return results
