"""
認可グラフの実装

KuzuDBを使用してURI間の権限関係を管理
"""
import kuzu
from pathlib import Path


class AuthGraph:
    """KuzuDBベースの認可グラフ"""
    
    def __init__(self, db_path: str):
        """
        認可グラフの初期化
        
        Args:
            db_path: データベースファイルのパス（":memory:"でインメモリDB）
        """
        # KuzuDBデータベース接続
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        
        # スキーマの初期化
        self._init_schema()
    
    def _init_schema(self):
        """グラフスキーマの初期化"""
        # Entityノードテーブル作成（すべてのURIエンティティ）
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Entity(
                uri STRING PRIMARY KEY
            )
        """)
        
        # auth関係テーブル作成
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS auth(
                FROM Entity TO Entity
            )
        """)
    
    def grant_permission(self, subject_uri: str, resource_uri: str):
        """
        権限を付与する
        
        Args:
            subject_uri: 権限を持つ主体のURI
            resource_uri: アクセス対象リソースのURI
        """
        # ノードが存在しない場合は作成
        self.conn.execute(
            "MERGE (e:Entity {uri: $uri})",
            {"uri": subject_uri}
        )
        self.conn.execute(
            "MERGE (e:Entity {uri: $uri})",
            {"uri": resource_uri}
        )
        
        # auth関係を作成（冪等性を保証）
        self.conn.execute(
            """
            MATCH (s:Entity {uri: $subject_uri}), (r:Entity {uri: $resource_uri})
            MERGE (s)-[:auth]->(r)
            """,
            {"subject_uri": subject_uri, "resource_uri": resource_uri}
        )
    
    def has_permission(self, subject_uri: str, resource_uri: str) -> bool:
        """
        権限の有無を確認する
        
        Args:
            subject_uri: 権限を確認する主体のURI
            resource_uri: アクセス対象リソースのURI
            
        Returns:
            権限がある場合True
        """
        result = self.conn.execute(
            """
            MATCH (s:Entity {uri: $subject_uri})-[:auth]->(r:Entity {uri: $resource_uri})
            RETURN count(*) > 0 as has_permission
            """,
            {"subject_uri": subject_uri, "resource_uri": resource_uri}
        )
        
        # 結果を取得
        if result.has_next():
            return result.get_next()[0]
        return False