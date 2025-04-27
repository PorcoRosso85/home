"""
KuzuDBのCypherクエリをファイル名ベースで実行するユーティリティ

このモジュールは、DMLとDDLのCypherクエリをファイル名から動的にロードして実行するための
機能を提供します。

使用例:
-------
1. 基本的な使用方法:
    ```python
    from call_dml import create_query_loader
    import kuzu  # データベース接続用（例）
    
    # 初期化
    loader = create_query_loader("/path/to/kuzu_db")
    
    # クエリの取得
    query_str = loader["get_query"]("insert_map_function")
    
    # クエリの実行
    conn = kuzu.Connection("path/to/db")  # 実際のKuzu DB接続
    result = loader["execute_query"]("insert_map_function", connection=conn)
    ```

2. クエリタイプの指定:
    ```python
    # DDLクエリの取得
    ddl_query = loader["get_query"]("function_schema_ddl", query_type="ddl")
    
    # DDLクエリの実行
    conn = kuzu.Connection("path/to/db")
    loader["execute_query"]("function_schema_ddl", query_type="ddl", connection=conn)
    ```

3. 利用可能なクエリの一覧を取得:
    ```python
    # DMLクエリ一覧
    dml_queries = loader["get_available_queries"]()
    
    # DDLクエリ一覧
    ddl_queries = loader["get_available_queries"](query_type="ddl")
    
    # すべてのクエリ一覧
    all_queries = loader["get_available_queries"](query_type="all")
    ```

4. パラメータ付きでクエリを実行:
    ```python
    # パラメータ付きでクエリを実行
    params = ["reduce", "配列の要素を集約する", "function", False, True, False, False, False]
    conn = kuzu.Connection("path/to/db")
    result = loader["execute_query"]("insert_parameterized_function", params=params, connection=conn)
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
from typing import Dict, List, Optional, Any, Union, Literal, Callable

# 型定義
QueryType = Literal["dml", "ddl", "all"]
QueryResult = Dict[str, Any]
QueryError = Dict[str, str]
Result = Union[QueryResult, QueryError]
QueryDict = Dict[str, Callable]

def setup_directories(query_dir: Optional[str] = None, dml_subdir: str = "dml", ddl_subdir: Optional[str] = None) -> Dict[str, str]:
    """
    ディレクトリ設定を行い、パス情報を返す
    
    Args:
        query_dir: クエリが保存されているルートディレクトリのパス (デフォルト: 現在のモジュールと同じディレクトリ)
        dml_subdir: DMLクエリが保存されているサブディレクトリ名 (デフォルト: "dml")
        ddl_subdir: DDLクエリが保存されているサブディレクトリ名 (デフォルト: query_dirのルート)
    
    Returns:
        ディレクトリパスを含む辞書
    """
    if query_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        query_dir = script_dir
    
    dml_dir = os.path.join(query_dir, dml_subdir) if dml_subdir else query_dir
    ddl_dir = os.path.join(query_dir, ddl_subdir) if ddl_subdir else query_dir
    
    return {
        "query_dir": query_dir,
        "dml_dir": dml_dir,
        "ddl_dir": ddl_dir
    }

def create_query_cache() -> Dict[str, Callable]:
    """
    クエリキャッシュ機能を提供する辞書を作成
    
    Returns:
        キャッシュ操作関数を含む辞書
    """
    cache: Dict[str, str] = {}
    
    def get(key: str) -> Optional[str]:
        """キャッシュからアイテムを取得"""
        return cache.get(key)
    
    def set(key: str, value: str) -> None:
        """キャッシュにアイテムを設定"""
        cache[key] = value
    
    def has(key: str) -> bool:
        """キャッシュにアイテムが存在するかチェック"""
        return key in cache
    
    return {
        "get": get,
        "set": set,
        "has": has
    }

def create_success_result(data: Any) -> QueryResult:
    """
    成功結果を生成
    
    Args:
        data: 結果データ
    
    Returns:
        成功結果の辞書
    """
    return {
        "success": True,
        "data": data
    }

def list_dml_queries(dirs: Dict[str, str]) -> List[str]:
    """
    DMLクエリの一覧を取得
    
    Args:
        dirs: ディレクトリパスを含む辞書
    
    Returns:
        DMLクエリ名のリスト
    """
    query_files = []
    try:
        for filename in os.listdir(dirs["dml_dir"]):
            if filename.endswith('.cypher'):
                query_name = os.path.splitext(filename)[0]
                query_files.append(f"dml/{query_name}")
    except FileNotFoundError:
        pass  # ディレクトリが存在しない場合は無視
    
    return query_files

def list_ddl_queries(dirs: Dict[str, str]) -> List[str]:
    """
    DDLクエリの一覧を取得
    
    Args:
        dirs: ディレクトリパスを含む辞書
    
    Returns:
        DDLクエリ名のリスト
    """
    query_files = []
    try:
        for filename in os.listdir(dirs["ddl_dir"]):
            if filename.endswith('.cypher') and os.path.isfile(os.path.join(dirs["ddl_dir"], filename)):
                query_name = os.path.splitext(filename)[0]
                if dirs["dml_dir"] != dirs["ddl_dir"]:
                    query_files.append(f"ddl/{query_name}")
                else:
                    query_files.append(query_name)
    except FileNotFoundError:
        pass  # ディレクトリが存在しない場合は無視
    
    return query_files

def get_available_queries(dirs: Dict[str, str], query_type: QueryType = "dml") -> List[str]:
    """
    利用可能なクエリの一覧を取得
    
    Args:
        dirs: ディレクトリパスを含む辞書
        query_type: 取得するクエリのタイプ ("dml", "ddl", または "all")
    
    Returns:
        クエリ名のリスト（拡張子なし）
    
    Raises:
        ValueError: 無効なクエリタイプが指定された場合
    """
    if query_type not in ["dml", "ddl", "all"]:
        # 無効なクエリタイプの場合は空リストを返す
        # 実際のエラーハンドリングはcreate_query_loaderの内部で行う
        return []
    
    query_files = []
    
    # DMLクエリの取得
    if query_type in ["dml", "all"]:
        query_files.extend(list_dml_queries(dirs))
    
    # DDLクエリの取得
    if query_type in ["ddl", "all"]:
        query_files.extend(list_ddl_queries(dirs))
            
    return sorted(query_files)

def build_query_path(dirs: Dict[str, str], query_name: str, query_type: QueryType = "dml") -> str:
    """
    クエリのファイルパスを構築
    
    Args:
        dirs: ディレクトリパスを含む辞書
        query_name: クエリ名（拡張子なし）
        query_type: クエリのタイプ ("dml" または "ddl")
    
    Returns:
        クエリファイルの絶対パス
    """
    if query_type == "dml":
        # DMLクエリの場合は、dml/サブディレクトリ内を検索
        if query_name.startswith("dml/"):
            query_name = query_name[4:]  # "dml/"プレフィックスを削除
        return os.path.join(dirs["dml_dir"], f"{query_name}.cypher")
    else:
        # DDLクエリの場合は、query_dirのルート内を検索
        if query_name.startswith("ddl/"):
            query_name = query_name[4:]  # "ddl/"プレフィックスを削除
        return os.path.join(dirs["ddl_dir"], f"{query_name}.cypher")

def read_query_file(file_path: str) -> str:
    """
    クエリファイルを読み込む
    
    Args:
        file_path: ファイルパス
    
    Returns:
        ファイル内容
    
    Raises:
        IOError: ファイル読み込みエラー
    """
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except IOError as e:
        raise IOError(f"クエリファイルの読み込みに失敗しました: {file_path} - {str(e)}")

def create_error_result(message: str, available_queries: List[str]) -> QueryError:
    """
    エラー結果を生成
    
    Args:
        message: エラーメッセージ
        available_queries: 利用可能なクエリのリスト
    
    Returns:
        エラー結果の辞書
    """
    return {
        "success": False,
        "error": message,
        "available_queries": available_queries
    }

def validate_query_type(query_type: str) -> None:
    """
    クエリタイプのバリデーション
    
    Args:
        query_type: 検証するクエリタイプ
    
    Raises:
        ValueError: クエリタイプが無効な場合
    """
    if query_type not in ["dml", "ddl"]:
        raise ValueError(f"無効なクエリタイプです: {query_type}。'dml'または'ddl'を指定してください")

def create_query_loader(query_dir: Optional[str] = None, dml_subdir: str = "dml", ddl_subdir: Optional[str] = None) -> QueryDict:
    """
    クエリローダーを作成
    
    Args:
        query_dir: クエリが保存されているルートディレクトリのパス (デフォルト: 現在のモジュールと同じディレクトリ)
        dml_subdir: DMLクエリが保存されているサブディレクトリ名 (デフォルト: "dml")
        ddl_subdir: DDLクエリが保存されているサブディレクトリ名 (デフォルト: query_dirのルート)
    
    Returns:
        クエリ関連の操作関数を含む辞書
    """
    dirs = setup_directories(query_dir, dml_subdir, ddl_subdir)
    cache = create_query_cache()
    
    def get_query(query_name: str, query_type: QueryType = "dml") -> str:
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
        if cache["has"](cache_key):
            return cache["get"](cache_key)
        
        # クエリタイプの検証
        validate_query_type(query_type)
        
        # ファイルパスの構築
        query_path = build_query_path(dirs, query_name, query_type)
        
        # ファイルの存在チェックと読み込み
        if not os.path.exists(query_path):
            available_queries = get_available_queries(dirs, query_type)
            error_msg = f"クエリファイルが見つかりません: {query_path}\n使用可能なクエリ: {available_queries}"
            raise FileNotFoundError(error_msg)
        
        # ファイル読み込み
        query_content = read_query_file(query_path)
        cache["set"](cache_key, query_content)
        return query_content
    
    def get_queries_wrapper(query_type: QueryType = "dml") -> List[str]:
        """
        利用可能なクエリの一覧を取得するラッパー関数
        
        Args:
            query_type: 取得するクエリのタイプ ("dml", "ddl", または "all")
        
        Returns:
            クエリ名のリスト
        
        Raises:
            ValueError: 無効なクエリタイプが指定された場合
        """
        if query_type not in ["dml", "ddl", "all"]:
            error_msg = f"無効なクエリタイプです: {query_type}。'dml', 'ddl', または 'all' を指定してください"
            return create_error_result(error_msg, get_available_queries(dirs, "all"))["available_queries"]
        
        return get_available_queries(dirs, query_type)
    
    def error_result_wrapper(message: str) -> QueryError:
        """
        エラー結果を生成するラッパー関数
        
        Args:
            message: エラーメッセージ
        
        Returns:
            エラー結果の辞書
        """
        return create_error_result(message, get_available_queries(dirs, "all"))
    
    def execute_query(query_name: str, params: Optional[List[Any]] = None, query_type: QueryType = "dml", connection=None) -> Result:
        """
        クエリを実行する
        
        Args:
            query_name: クエリ名（拡張子なし）
            params: クエリパラメータのリスト (オプション)
            query_type: クエリのタイプ ("dml" または "ddl")
            connection: クエリ実行に使用するデータベース接続 (オプション)
        
        Returns:
            クエリ実行結果
        """
        try:
            # クエリを取得
            query_content = get_query(query_name, query_type)
            
            # 接続オブジェクトがない場合はエラー
            if connection is None:
                return error_result_wrapper("データベース接続が指定されていません")
            
            # クエリの実行
            try:
                if params:
                    result = connection.execute(query_content, params)
                else:
                    result = connection.execute(query_content)
                
                return create_success_result(result)
            except Exception as e:
                return error_result_wrapper(f"クエリの実行に失敗しました: {str(e)}")
        
        except FileNotFoundError as e:
            return error_result_wrapper(str(e))
        except ValueError as e:
            return error_result_wrapper(str(e))
        except IOError as e:
            return error_result_wrapper(str(e))
    
    # 公開インターフェイスを返す
    return {
        "get_available_queries": get_queries_wrapper,
        "get_query": get_query,
        "execute_query": execute_query,
        "success_result": create_success_result,
        "error_result": error_result_wrapper
    }

# 後方互換性のためのエイリアス
create_dml_query_executor = create_query_loader

# テスト関数
def test_valid_query_loading():
    """クエリが正しくロードできることをテスト"""
    loader = create_query_loader()
    available_queries = loader["get_available_queries"]()
    
    # 利用可能なクエリが少なくとも1つ存在する
    assert len(available_queries) > 0, "利用可能なDMLクエリが見つかりません"
    
    # 先頭のクエリをテスト
    first_query = available_queries[0]
    query_content = loader["get_query"](first_query)
    
    # クエリ内容が取得できる
    assert query_content, f"クエリ内容を取得できませんでした: {first_query}"
    assert isinstance(query_content, str), "クエリ内容は文字列である必要があります"
    assert len(query_content) > 0, "クエリ内容が空です"

def test_invalid_query_error_handling():
    """無効なクエリ名のエラー処理をテスト"""
    loader = create_query_loader()
    
    # 存在しないクエリ名
    non_existent_query = "non_existent_query_name"
    
    # FileNotFoundError が発生することを確認
    try:
        loader["get_query"](non_existent_query)
        assert False, "存在しないクエリに対して例外が発生しませんでした"
    except FileNotFoundError as e:
        # エラーメッセージに利用可能なクエリ一覧が含まれている
        error_message = str(e)
        assert "使用可能なクエリ" in error_message, "エラーメッセージに使用可能なクエリ一覧が含まれていません"

def test_query_list_retrieval():
    """クエリリストが正しく取得できることをテスト"""
    loader = create_query_loader()
    
    # DMLクエリの取得
    dml_queries = loader["get_available_queries"]("dml")
    assert isinstance(dml_queries, list), "DMLクエリリストはリスト型である必要があります"
    
    # DDLクエリの取得
    ddl_queries = loader["get_available_queries"]("ddl")
    assert isinstance(ddl_queries, list), "DDLクエリリストはリスト型である必要があります"
    
    # すべてのクエリの取得
    all_queries = loader["get_available_queries"]("all")
    assert isinstance(all_queries, list), "クエリリストはリスト型である必要があります"
    assert len(all_queries) >= len(dml_queries), "すべてのクエリは少なくともDMLクエリを含む必要があります"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
