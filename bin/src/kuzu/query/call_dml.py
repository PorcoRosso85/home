"""
KuzuDBのDMLクエリを名前で実行するためのユーティリティ

使用方法:
---------
1. 基本的な使用方法:
    ```python
    from call_dml import DMLQueryExecutor
    
    # 初期化
    executor = DMLQueryExecutor("/path/to/kuzu_db")
    
    # 単一のクエリを実行
    executor.execute_query("insert_map_function")
    ```

2. 複数のクエリをグループとして実行:
    ```python
    # map関数関連のすべてのクエリを順番に実行
    map_queries = [
        "insert_map_function",
        "insert_map_parameters", 
        "insert_map_return_type",
        "link_map_parameters", 
        "link_map_return_type"
    ]
    executor.execute_multiple_queries(map_queries)
    ```

3. 利用可能なクエリの一覧を取得:
    ```python
    available_queries = executor.get_available_queries()
    print("Available queries:", available_queries)
    ```

4. パラメータ付きでクエリを実行:
    ```python
    # パラメータ付きのクエリを実行
    # (クエリ内で「?」プレースホルダーが使用されている場合)
    params = ["reduce", "配列の要素を集約する", "function", False, True, False, False, False]
    executor.execute_query("insert_parameterized_function", params)
    ```

5. すべてのクエリを実行:
    ```python
    # dmlディレクトリにあるすべてのクエリを実行
    executor.execute_all_queries()
    ```

注意:
----
- クエリファイルは拡張子が`.cypher`である必要があります
- ファイル名は拡張子なしで参照します (`insert_map_function.cypher` → `"insert_map_function"`)
- クエリは `/home/nixos/bin/src/kuzu/query/dml/` ディレクトリに配置されています
"""
import os
from typing import Dict, List, Optional, Any, Union
from kuzu import Database, Connection


class DMLQueryExecutor:
    """KuzuDBのDMLクエリをファイル名ベースで実行するクラス"""

    def __init__(self, db_path: str, dml_dir: str = None):
        """
        初期化
        
        Args:
            db_path: KuzuDBのパス
            dml_dir: DMLクエリが保存されているディレクトリパス
        """
        self.db = Database(db_path)
        self.conn = self.db.get_connection()
        
        if dml_dir is None:
            # デフォルトのDMLディレクトリパスを設定
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.dml_dir = os.path.join(script_dir, 'dml')
        else:
            self.dml_dir = dml_dir
        
        # クエリのキャッシュ
        self._query_cache: Dict[str, str] = {}
    
    def get_available_queries(self) -> List[str]:
        """
        利用可能なDMLクエリのリストを取得
        
        Returns:
            クエリファイル名のリスト（拡張子なし）
        """
        query_files = []
        for filename in os.listdir(self.dml_dir):
            if filename.endswith('.cypher'):
                # 拡張子を除外してリストに追加
                query_name = os.path.splitext(filename)[0]
                query_files.append(query_name)
        return query_files
    
    def get_query_content(self, query_name: str) -> str:
        """
        クエリの内容を取得
        
        Args:
            query_name: クエリ名（拡張子なし）
            
        Returns:
            クエリの内容
            
        Raises:
            FileNotFoundError: クエリが見つからない場合
        """
        if query_name in self._query_cache:
            return self._query_cache[query_name]
        
        query_path = os.path.join(self.dml_dir, f"{query_name}.cypher")
        
        if not os.path.exists(query_path):
            raise FileNotFoundError(f"クエリファイルが見つかりません: {query_path}")
        
        with open(query_path, 'r') as f:
            query_content = f.read()
            self._query_cache[query_name] = query_content
            return query_content
    
    def execute_query(self, query_name: str, params: Optional[List[Any]] = None) -> Any:
        """
        指定した名前のクエリを実行
        
        Args:
            query_name: 実行するクエリ名（拡張子なし）
            params: クエリパラメータ（あれば）
            
        Returns:
            クエリ実行結果
            
        Raises:
            FileNotFoundError: クエリが見つからない場合
        """
        query_content = self.get_query_content(query_name)
        
        if params:
            return self.conn.execute(query_content, params)
        else:
            return self.conn.execute(query_content)
    
    def execute_multiple_queries(self, query_names: List[str]) -> None:
        """
        複数のクエリを順番に実行
        
        Args:
            query_names: 実行するクエリ名のリスト
        """
        for query_name in query_names:
            print(f"Executing query: {query_name}")
            self.execute_query(query_name)
    
    def execute_all_queries(self) -> None:
        """
        すべての利用可能なクエリを実行
        """
        query_names = self.get_available_queries()
        self.execute_multiple_queries(query_names)


# 使用例
if __name__ == "__main__":
    # 使用例
    executor = DMLQueryExecutor("/path/to/kuzu_db")
    
    # 利用可能なクエリを表示
    print("Available queries:")
    for query in executor.get_available_queries():
        print(f"- {query}")
    
    # 特定のクエリを実行
    executor.execute_query("insert_map_function")
    
    # 関連クエリを順番に実行
    map_related_queries = [
        "insert_map_function",
        "insert_map_parameters",
        "insert_map_return_type",
        "link_map_parameters",
        "link_map_return_type"
    ]
    executor.execute_multiple_queries(map_related_queries)
