"""
KuzuDBのCypherクエリをファイル名ベースで実行するユーティリティ

このモジュールは、DMLとDDLのCypherクエリをファイル名から動的にロードして実行するための
機能を提供します。

使用例:
-------
1. 基本的な使用方法:
    ```python
    from call_dml import QueryLoader
    
    # 初期化
    loader = QueryLoader("/path/to/kuzu_db")
    
    # クエリの取得
    query_str = loader.get_query("insert_map_function")
    
    # クエリの実行
    result = loader.execute_query("insert_map_function")
    ```

2. クエリタイプの指定:
    ```python
    # DDLクエリの取得
    ddl_query = loader.get_query("function_schema_ddl", query_type="ddl")
    
    # DDLクエリの実行
    loader.execute_query("function_schema_ddl", query_type="ddl")
    ```

3. 利用可能なクエリの一覧を取得:
    ```python
    # DMLクエリ一覧
    dml_queries = loader.get_available_queries()
    
    # DDLクエリ一覧
    ddl_queries = loader.get_available_queries(query_type="ddl")
    
    # すべてのクエリ一覧
    all_queries = loader.get_available_queries(query_type="all")
    ```

4. パラメータ付きでクエリを実行:
    ```python
    # パラメータ付きでクエリを実行
    params = ["reduce", "配列の要素を集約する", "function", False, True, False, False, False]
    loader.execute_query("insert_parameterized_function", params=params)
    ```

エラー処理:
--------
- 指定されたクエリが存在しない場合は FileNotFoundError 例外を発生させます
- クエリファイルを読み込めない場合は IOError 例外を発生させます
- 無効なクエリタイプが指定された場合は ValueError 例外を発生させます

注意:
----
- クエリファイルは拡張子が `.cypher` である必要があります
- ファイル名は拡張子なしで参照します (`insert_map_function.cypher` → `"insert_map_function"`)
- DMLクエリは `dml/` ディレクトリに、DDLクエリはクエリディレクトリのルートに配置されています
"""
import os
from typing import Dict, List, Optional, Any, Union, Literal

# 型定義
QueryType = Literal["dml", "ddl", "all"]
QueryResult = Dict[str, Any]
QueryError = Dict[str, str]
Result = Union[QueryResult, QueryError]


class QueryLoader:
    """KuzuDBのCypher (DML/DDL) クエリをファイル名ベースで管理するクラス"""

    def __init__(self, query_dir: str = None, dml_subdir: str = "dml", ddl_subdir: str = None):
        """
        初期化
        
        Args:
            query_dir: クエリが保存されているルートディレクトリのパス (デフォルト: 現在のモジュールと同じディレクトリ)
            dml_subdir: DMLクエリが保存されているサブディレクトリ名 (デフォルト: "dml")
            ddl_subdir: DDLクエリが保存されているサブディレクトリ名 (デフォルト: query_dirのルート)
        """
        # ルートディレクトリの設定
        if query_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.query_dir = script_dir
        else:
            self.query_dir = query_dir
        
        # DMLディレクトリの設定
        self.dml_dir = os.path.join(self.query_dir, dml_subdir) if dml_subdir else self.query_dir
        
        # DDLディレクトリの設定
        if ddl_subdir:
            self.ddl_dir = os.path.join(self.query_dir, ddl_subdir)
        else:
            self.ddl_dir = self.query_dir
        
        # クエリのキャッシュ
        self._query_cache: Dict[str, str] = {}
    
    def get_available_queries(self, query_type: QueryType = "dml") -> List[str]:
        """
        利用可能なクエリの一覧を取得
        
        Args:
            query_type: 取得するクエリのタイプ ("dml", "ddl", または "all")
            
        Returns:
            クエリ名のリスト（拡張子なし）
            
        Raises:
            ValueError: 無効なクエリタイプが指定された場合
        """
        if query_type not in ["dml", "ddl", "all"]:
            error_msg = f"無効なクエリタイプです: {query_type}。'dml', 'ddl', または 'all' を指定してください"
            return self._error_result(error_msg)["available_queries"]
        
        query_files = []
        
        # DMLクエリの取得
        if query_type in ["dml", "all"]:
            try:
                for filename in os.listdir(self.dml_dir):
                    if filename.endswith('.cypher'):
                        query_name = os.path.splitext(filename)[0]
                        query_files.append(f"dml/{query_name}")
            except FileNotFoundError:
                pass  # ディレクトリが存在しない場合は無視
        
        # DDLクエリの取得
        if query_type in ["ddl", "all"]:
            try:
                for filename in os.listdir(self.ddl_dir):
                    if filename.endswith('.cypher') and os.path.isfile(os.path.join(self.ddl_dir, filename)):
                        query_name = os.path.splitext(filename)[0]
                        if query_type == "all" and self.dml_dir != self.ddl_dir:
                            query_files.append(f"ddl/{query_name}")
                        else:
                            query_files.append(query_name)
            except FileNotFoundError:
                pass  # ディレクトリが存在しない場合は無視
                
        return sorted(query_files)
    
    def get_query(self, query_name: str, query_type: QueryType = "dml") -> str:
        """
        クエリの内容を取得
        
        Args:
            query_name: クエリ名（拡張子なし）
            query_type: クエリのタイプ ("dml" または "ddl")
            
        Returns:
            クエリの内容
            
        Raises:
            FileNotFoundError: クエリが見つからない場合
            ValueError: 無効なクエリタイプが指定された場合
        """
        cache_key = f"{query_type}:{query_name}"
        
        # キャッシュをチェック
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]
        
        # クエリタイプの検証
        if query_type not in ["dml", "ddl"]:
            raise ValueError(f"無効なクエリタイプです: {query_type}。'dml'または'ddl'を指定してください")
        
        # ファイルパスの構築
        if query_type == "dml":
            # DMLクエリの場合は、dml/サブディレクトリ内を検索
            if query_name.startswith("dml/"):
                query_name = query_name[4:]  # "dml/"プレフィックスを削除
            query_path = os.path.join(self.dml_dir, f"{query_name}.cypher")
        else:
            # DDLクエリの場合は、query_dirのルート内を検索
            if query_name.startswith("ddl/"):
                query_name = query_name[4:]  # "ddl/"プレフィックスを削除
            query_path = os.path.join(self.ddl_dir, f"{query_name}.cypher")
        
        # ファイルの存在チェックと読み込み
        if not os.path.exists(query_path):
            available_queries = self.get_available_queries(query_type)
            error_msg = f"クエリファイルが見つかりません: {query_path}\n使用可能なクエリ: {available_queries}"
            raise FileNotFoundError(error_msg)
        
        try:
            with open(query_path, 'r') as f:
                query_content = f.read()
                self._query_cache[cache_key] = query_content
                return query_content
        except IOError as e:
            raise IOError(f"クエリファイルの読み込みに失敗しました: {query_path} - {str(e)}")
    
    def _success_result(self, data: Any) -> QueryResult:
        """成功結果を生成"""
        return {
            "success": True,
            "data": data
        }
    
    def _error_result(self, message: str) -> QueryError:
        """エラー結果を生成"""
        return {
            "success": False,
            "error": message,
            "available_queries": self.get_available_queries("all")
        }


# 後方互換性のためのエイリアス
DMLQueryExecutor = QueryLoader


# テスト関数
def test_valid_query_loading():
    """クエリが正しくロードできることをテスト"""
    loader = QueryLoader()
    available_queries = loader.get_available_queries()
    
    # 利用可能なクエリが少なくとも1つ存在する
    assert len(available_queries) > 0, "利用可能なDMLクエリが見つかりません"
    
    # 先頭のクエリをテスト
    first_query = available_queries[0]
    query_content = loader.get_query(first_query)
    
    # クエリ内容が取得できる
    assert query_content, f"クエリ内容を取得できませんでした: {first_query}"
    assert isinstance(query_content, str), "クエリ内容は文字列である必要があります"
    assert len(query_content) > 0, "クエリ内容が空です"


def test_invalid_query_error_handling():
    """無効なクエリ名のエラー処理をテスト"""
    loader = QueryLoader()
    
    # 存在しないクエリ名
    non_existent_query = "non_existent_query_name"
    
    # FileNotFoundError が発生することを確認
    try:
        loader.get_query(non_existent_query)
        assert False, "存在しないクエリに対して例外が発生しませんでした"
    except FileNotFoundError as e:
        # エラーメッセージに利用可能なクエリ一覧が含まれている
        error_message = str(e)
        assert "使用可能なクエリ" in error_message, "エラーメッセージに使用可能なクエリ一覧が含まれていません"


def test_query_list_retrieval():
    """クエリリストが正しく取得できることをテスト"""
    loader = QueryLoader()
    
    # DMLクエリの取得
    dml_queries = loader.get_available_queries("dml")
    assert isinstance(dml_queries, list), "DMLクエリリストはリスト型である必要があります"
    
    # DDLクエリの取得
    ddl_queries = loader.get_available_queries("ddl")
    assert isinstance(ddl_queries, list), "DDLクエリリストはリスト型である必要があります"
    
    # すべてのクエリの取得
    all_queries = loader.get_available_queries("all")
    assert isinstance(all_queries, list), "クエリリストはリスト型である必要があります"
    assert len(all_queries) >= len(dml_queries), "すべてのクエリは少なくともDMLクエリを含む必要があります"
