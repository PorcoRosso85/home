"""graph_docs POC - Dual KuzuDB Query Interface

責務:
- 2つのKuzuDBディレクトリに対する同時クエリ
- 2つのDB間のリレーション定義
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import kuzu

@dataclass
class QueryResult:
    """クエリ実行結果"""
    source: str  # "db1" or "db2"
    columns: List[str]
    rows: List[List[Any]]
    error: Optional[str] = None

@dataclass
class DualQueryResult:
    """2つのDBに対するクエリ結果"""
    db1_result: Optional[QueryResult]
    db2_result: Optional[QueryResult]
    combined: Optional[List[Dict[str, Any]]] = None

class DualKuzuDB:
    """2つのKuzuDBを管理するクラス"""
    
    def __init__(self, db1_path: Union[str, Path], db2_path: Union[str, Path]):
        """
        Args:
            db1_path: 1つ目のKuzuDBディレクトリパス
            db2_path: 2つ目のKuzuDBディレクトリパス
        """
        self.db1_path = Path(db1_path)
        self.db2_path = Path(db2_path)
        self._db1: Optional[kuzu.Database] = None
        self._db2: Optional[kuzu.Database] = None
        self._conn1: Optional[kuzu.Connection] = None
        self._conn2: Optional[kuzu.Connection] = None
    
    def connect(self) -> None:
        """両方のDBに接続"""
        self._db1 = kuzu.Database(str(self.db1_path))
        self._db2 = kuzu.Database(str(self.db2_path))
        self._conn1 = kuzu.Connection(self._db1)
        self._conn2 = kuzu.Connection(self._db2)
    
    def disconnect(self) -> None:
        """両方のDBから切断"""
        if self._conn1:
            self._conn1 = None
        if self._conn2:
            self._conn2 = None
        self._db1 = None
        self._db2 = None
    
    def query_single(self, db_name: str, query: str) -> QueryResult:
        """単一のDBに対してクエリを実行
        
        Args:
            db_name: "db1" or "db2"
            query: 実行するCypherクエリ
            
        Returns:
            QueryResult: クエリ結果
        """
        if db_name not in ["db1", "db2"]:
            return QueryResult(
                source=db_name,
                columns=[],
                rows=[],
                error=f"Invalid db_name: {db_name}. Must be 'db1' or 'db2'"
            )
        
        conn = self._conn1 if db_name == "db1" else self._conn2
        if not conn:
            return QueryResult(
                source=db_name,
                columns=[],
                rows=[],
                error=f"Not connected to {db_name}"
            )
        
        try:
            result = conn.execute(query)
            columns = result.get_column_names() if hasattr(result, 'get_column_names') else []
            rows = []
            while result.has_next():
                rows.append(result.get_next())
            
            return QueryResult(
                source=db_name,
                columns=columns,
                rows=rows
            )
        except Exception as e:
            return QueryResult(
                source=db_name,
                columns=[],
                rows=[],
                error=str(e)
            )
    
    def query_both(self, query: str) -> DualQueryResult:
        """両方のDBに対して同じクエリを実行
        
        Args:
            query: 実行するCypherクエリ
            
        Returns:
            DualQueryResult: 両DBの結果
        """
        db1_result = self.query_single("db1", query)
        db2_result = self.query_single("db2", query)
        
        return DualQueryResult(
            db1_result=db1_result if not db1_result.error else None,
            db2_result=db2_result if not db2_result.error else None
        )
    
    def query_parallel(self, db1_query: str, db2_query: str) -> DualQueryResult:
        """それぞれのDBに対して異なるクエリを実行
        
        Args:
            db1_query: DB1に対するクエリ
            db2_query: DB2に対するクエリ
            
        Returns:
            DualQueryResult: 両DBの結果
        """
        db1_result = self.query_single("db1", db1_query)
        db2_result = self.query_single("db2", db2_query)
        
        return DualQueryResult(
            db1_result=db1_result if not db1_result.error else None,
            db2_result=db2_result if not db2_result.error else None
        )
    
    def __enter__(self):
        """コンテキストマネージャーのエントリー"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーのエグジット"""
        self.disconnect()

# 公開API
__all__ = ['DualKuzuDB', 'QueryResult', 'DualQueryResult']