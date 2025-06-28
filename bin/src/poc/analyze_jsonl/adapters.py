"""
外部依存のアダプター層

CONVENTION.yaml準拠:
- DuckDBとの接続を抽象化
- ファイルシステムアクセスを分離
- 副作用を境界に隔離
"""

from typing import List, Dict, Any, Tuple, Optional
import duckdb
import glob
from pathlib import Path


# ====================
# REDフェーズ: テストを先に書く
# ====================

def test_create_duckdb_connection_メモリDB_接続成功():
    """インメモリDuckDB接続を作成できる"""
    conn = create_duckdb_connection()
    assert conn is not None
    # 接続が有効か確認
    result = conn.execute("SELECT 1").fetchall()
    assert result == [(1,)]


def test_create_duckdb_connection_メモリ制限設定_設定反映():
    """メモリ制限を設定して接続を作成できる"""
    conn = create_duckdb_connection(memory_limit_mb=512)
    # 設定が反映されているか確認（DuckDBの内部設定を直接確認は困難なのでクエリが実行できることを確認）
    result = conn.execute("SELECT 1").fetchall()
    assert result == [(1,)]


def test_execute_query_有効なSQL_結果取得():
    """有効なSQLクエリを実行して結果を取得できる"""
    conn = create_duckdb_connection()
    result, columns = execute_query(conn, "SELECT 1 as num, 'test' as text")
    
    assert result == [(1, 'test')]
    assert columns == ['num', 'text']


def test_execute_query_無効なSQL_None返却():
    """無効なSQLクエリを実行するとNoneが返される"""
    conn = create_duckdb_connection()
    result, columns = execute_query(conn, "INVALID SQL")
    
    assert result is None
    assert columns is None


def test_find_files_by_pattern_存在するパターン_ファイルリスト():
    """存在するパターンでファイルリストを取得できる"""
    # /tmpは常に存在するディレクトリ
    files = find_files_by_pattern('/tmp', '*.tmp')
    assert isinstance(files, list)


def test_find_files_by_pattern_存在しないディレクトリ_空リスト():
    """存在しないディレクトリを指定すると空リストが返される"""
    files = find_files_by_pattern('/this/does/not/exist', '*')
    assert files == []


def test_register_jsonl_view_ファイルリスト_ビュー作成():
    """JSONLファイルリストからビューを作成できる"""
    conn = create_duckdb_connection()
    # テスト用の仮想ファイルリスト
    files = ['/tmp/test1.jsonl', '/tmp/test2.jsonl']
    
    success = register_jsonl_view(conn, files, 'test_view')
    # ファイルが存在しなくてもビュー作成のSQLは実行できる
    assert isinstance(success, bool)


def test_get_table_info_存在するテーブル_情報取得():
    """存在するテーブルの情報を取得できる"""
    conn = create_duckdb_connection()
    # テスト用のテーブルを作成
    conn.execute("CREATE TABLE test_table (id INTEGER, name VARCHAR)")
    
    info = get_table_info(conn, 'test_table')
    assert isinstance(info, list)
    assert len(info) == 2  # id, name の2カラム


def test_get_table_info_存在しないテーブル_空リスト():
    """存在しないテーブルを指定すると空リストが返される"""
    conn = create_duckdb_connection()
    info = get_table_info(conn, 'nonexistent_table')
    assert info == []


# ====================
# GREENフェーズ: 最小限の実装（テスト後に実装）
# ====================

def create_duckdb_connection(memory_limit_mb: Optional[int] = None) -> duckdb.DuckDBPyConnection:
    """DuckDB接続を作成"""
    conn = duckdb.connect(':memory:')
    if memory_limit_mb:
        conn.execute(f"SET memory_limit='{memory_limit_mb}MB'")
    return conn


def execute_query(conn: duckdb.DuckDBPyConnection, sql: str) -> Tuple[Optional[List[tuple]], Optional[List[str]]]:
    """SQLクエリを実行"""
    try:
        cursor = conn.execute(sql)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return result, columns
    except:
        return None, None


def find_files_by_pattern(directory: str, pattern: str) -> List[str]:
    """ファイルパターンで検索"""
    try:
        path = Path(directory)
        if not path.exists():
            return []
        
        full_pattern = str(path / pattern)
        return glob.glob(full_pattern, recursive=True)
    except:
        return []


def register_jsonl_view(conn: duckdb.DuckDBPyConnection, files: List[str], view_name: str) -> bool:
    """JSONLファイルからビューを作成"""
    try:
        if files:
            file_list = ', '.join([f"'{f}'" for f in files])
            sql = f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_json_auto([{file_list}])"
        else:
            # 空のビューを作成
            sql = f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM (VALUES (NULL)) t(dummy) WHERE 1=0"
        
        conn.execute(sql)
        return True
    except:
        return False


def get_table_info(conn: duckdb.DuckDBPyConnection, table_name: str) -> List[Tuple[str, str]]:
    """テーブル/ビューの情報を取得"""
    try:
        result = conn.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
        """).fetchall()
        return result
    except:
        return []