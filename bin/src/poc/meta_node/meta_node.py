"""
Meta Node POC - Cypherクエリをノードに格納して動的実行する仕組み

このモジュールは、グラフノード自体にクエリロジックを持たせ、
メタプログラミング的なアプローチでグラフ操作を実現します。
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import kuzu


@dataclass
class QueryNode:
    """Cypherクエリを格納するノードのデータ構造"""
    name: str
    description: str
    cypher_query: str


class MetaNode:
    """メタノードシステムのメインクラス"""
    
    def __init__(self, db: kuzu.Database):
        """
        メタノードシステムを初期化
        
        Args:
            db: KuzuDatabase インスタンス
        """
        self.db = db
        self._initialize_schema()
    
    def _initialize_schema(self):
        """QueryNodeテーブルのスキーマを初期化"""
        conn = kuzu.Connection(self.db)
        # QueryNodeテーブルが存在しない場合は作成
        try:
            conn.execute("""
                CREATE NODE TABLE QueryNode(
                    name STRING,
                    description STRING,
                    cypher_query STRING,
                    PRIMARY KEY(name)
                )
            """)
        except:
            # テーブルが既に存在する場合は無視
            pass
    
    def create_query_node(self, query_node: QueryNode) -> str:
        """
        クエリノードを作成して保存
        
        Args:
            query_node: 保存するQueryNodeインスタンス
            
        Returns:
            作成されたノードのname（ID）
        """
        conn = kuzu.Connection(self.db)
        conn.execute(
            """
            CREATE (:QueryNode {
                name: $name,
                description: $description,
                cypher_query: $cypher_query
            })
            """,
            {
                "name": query_node.name,
                "description": query_node.description,
                "cypher_query": query_node.cypher_query
            }
        )
        return query_node.name
    
    def get_query_node(self, name: str) -> Optional[QueryNode]:
        """
        名前でクエリノードを取得
        
        Args:
            name: 取得するクエリノードの名前
            
        Returns:
            QueryNodeインスタンス、存在しない場合はNone
        """
        conn = kuzu.Connection(self.db)
        result = conn.execute(
            "MATCH (q:QueryNode {name: $name}) RETURN q",
            {"name": name}
        )
        
        if result.has_next():
            row = result.get_next()
            node_data = row[0]
            return QueryNode(
                name=node_data["name"],
                description=node_data["description"],
                cypher_query=node_data["cypher_query"]
            )
        return None


class QueryExecutor:
    """動的クエリ実行エンジン"""
    
    def __init__(self, meta_node: MetaNode):
        """
        QueryExecutorを初期化
        
        Args:
            meta_node: MetaNodeインスタンス
        """
        self.meta_node = meta_node
    
    def execute_query(self, query_name: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        保存されたクエリを名前で実行
        
        Args:
            query_name: 実行するクエリの名前
            parameters: クエリパラメータ（オプション）
            
        Returns:
            クエリ結果のリスト
        """
        # クエリノードを取得
        query_node = self.meta_node.get_query_node(query_name)
        if not query_node:
            raise ValueError(f"Query node '{query_name}' not found")
        
        # クエリを実行
        conn = kuzu.Connection(self.meta_node.db)
        result = conn.execute(query_node.cypher_query, parameters or {})
        
        # 結果を辞書のリストに変換
        results = []
        while result.has_next():
            row = result.get_next()
            # 各行を辞書に変換
            row_dict = {}
            for i, col_name in enumerate(result.get_column_names()):
                row_dict[col_name] = row[i]
            results.append(row_dict)
        
        return results