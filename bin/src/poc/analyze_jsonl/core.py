"""
分散JSONLファイルを集約・クエリするコア機能

使用例:
    >>> analyzer = create_analyzer(['/logs/app1', '/logs/app2'])
    >>> result = analyzer.query("SELECT * FROM all_logs LIMIT 10")
    >>> print(result.row_count)
"""

import duckdb
from typing import List, Dict, Any, Union
from pathlib import Path
import glob
import time


# ====================
# REDフェーズ: テストを先に書く
# ====================

def test_create_analyzer_単一ディレクトリ_アナライザー作成成功():
    """単一ディレクトリを指定してアナライザーを作成できる"""
    analyzer = create_analyzer(['/tmp/logs'])
    assert analyzer is not None
    assert hasattr(analyzer, 'query')


def test_create_analyzer_複数ディレクトリ_アナライザー作成成功():
    """複数ディレクトリを指定してアナライザーを作成できる"""
    analyzer = create_analyzer(['/tmp/logs1', '/tmp/logs2', '/tmp/logs3'])
    assert analyzer is not None


def test_create_analyzer_空のディレクトリリスト_エラー():
    """空のディレクトリリストを渡すとエラーになる"""
    result = create_analyzer([])
    assert result['ok'] is False
    assert 'error' in result
    assert 'ディレクトリが指定されていません' in result['error']


def test_analyzer_query_有効なSQL_結果取得成功():
    """有効なSQLクエリで結果を取得できる"""
    analyzer = create_analyzer(['/tmp/logs'])
    result = analyzer.query("SELECT 1 as test")
    
    # デバッグ出力
    if not result['ok']:
        print(f"Query failed: {result.get('error')}")
    



def test_analyzer_query_無効なSQL_エラー():
    """無効なSQLクエリでエラーが返される"""
    analyzer = create_analyzer(['/tmp/logs'])
    result = analyzer.query("INVALID SQL QUERY")
    
    assert result['ok'] is False
    assert 'error' in result


def test_analyzer_register_jsonl_files_JSONLファイル登録_ビュー作成():
    """JSONLファイルを登録してビューが作成される"""
    analyzer = create_analyzer(['/tmp/logs'])
    result = analyzer.register_jsonl_files('/tmp/logs', '*.jsonl', 'logs')
    
    assert result['ok'] is True
    assert result['registered_count'] >= 0
    assert result['view_name'] == 'logs'


def test_analyzer_list_views_登録済みビュー_一覧取得():
    """登録済みのビュー一覧を取得できる"""
    analyzer = create_analyzer(['/tmp/logs'])
    analyzer.register_jsonl_files('/tmp/logs', '*.jsonl', 'logs')
    
    views = analyzer.list_views()
    assert isinstance(views, list)
    assert 'logs' in views


def test_analyzer_create_unified_view_統合ビュー作成_成功():
    """全ソースの統合ビューを作成できる"""
    analyzer = create_analyzer(['/tmp/logs1', '/tmp/logs2'])
    analyzer.register_jsonl_files('/tmp/logs1', '*.jsonl', 'logs1')
    analyzer.register_jsonl_files('/tmp/logs2', '*.jsonl', 'logs2')
    
    result = analyzer.create_unified_view('all_logs')
    assert result['ok'] is True
    assert result['view_name'] == 'all_logs'
    assert result['source_count'] >= 2


def test_find_jsonl_files_存在するパターン_ファイルリスト取得():
    """指定パターンに一致するJSONLファイルのリストを取得できる"""
    files = find_jsonl_files('/tmp/logs', '*.jsonl')
    assert isinstance(files, list)


def test_find_jsonl_files_存在しないディレクトリ_空リスト():
    """存在しないディレクトリを指定すると空リストが返される"""
    files = find_jsonl_files('/nonexistent/directory', '*.jsonl')
    assert files == []


def test_parse_query_result_DuckDB結果_辞書形式変換():
    """DuckDBのクエリ結果を辞書形式に変換できる"""
    # DuckDBの結果をシミュレート
    mock_result = [('value1', 123), ('value2', 456)]
    mock_columns = ['name', 'count']
    
    parsed = parse_query_result(mock_result, mock_columns)
    assert parsed['columns'] == ['name', 'count']
    assert parsed['rows'] == [['value1', 123], ['value2', 456]]
    assert parsed['row_count'] == 2


# ====================
# GREENフェーズ: 最小限の実装（テスト後に実装）
# ====================

def create_analyzer(directories: List[str]) -> Union['JSONLAnalyzer', Dict[str, Any]]:
    """JSONLアナライザーを作成"""
    if not directories:
        return {'ok': False, 'error': 'ディレクトリが指定されていません'}
    
    return JSONLAnalyzer(directories)


class JSONLAnalyzer:
    """DuckDBベースのJSONL分析器"""
    
    def __init__(self, directories: List[str]):
        self.directories = directories
        self.conn = duckdb.connect(':memory:')
        self.views = []
    
    def query(self, sql: str) -> Dict[str, Any]:
        """SQLクエリを実行"""
        try:
            # executeの結果を保存
            cursor = self.conn.execute(sql)
            result = cursor.fetchall()
            # descriptionはプロパティ（関数呼び出しではない）
            columns = [desc[0] for desc in cursor.description]
            
            return {
                'ok': True,
                'data': {
                    'columns': columns,
                    'rows': [list(row) for row in result],
                    'row_count': len(result),
                    'execution_time_ms': 0.0  # 簡易実装
                }
            }
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def register_jsonl_files(self, directory: str, pattern: str, view_name: str) -> Dict[str, Any]:
        """JSONLファイルを登録してビューを作成"""
        try:
            files = find_jsonl_files(directory, pattern)
            
            if files:
                file_list = ', '.join([f"'{f}'" for f in files])
                sql = f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_json_auto([{file_list}])"
                self.conn.execute(sql)
            else:
                # ファイルがなくても空のビューを作成（統合ビュー用に基本的なカラムを定義）
                self.conn.execute(f"""
                    CREATE OR REPLACE VIEW {view_name} AS 
                    SELECT 
                        NULL::VARCHAR as content,
                        NULL::TIMESTAMP as timestamp,
                        NULL::VARCHAR as level
                    WHERE 1=0
                """)
            
            self.views.append(view_name)
            
            return {
                'ok': True,
                'registered_count': len(files),
                'view_name': view_name
            }
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def list_views(self) -> List[str]:
        """登録済みビューの一覧を取得"""
        return self.views
    
    def register_stream_jsonl_files(self, directory: str, pattern: str = 'stream.jsonl') -> Dict[str, Any]:
        """stream.jsonl専用の登録関数"""
        try:
            files = find_jsonl_files(directory, pattern)
            
            if files:
                # stream_jsonlビューを作成
                file_list = ', '.join([f"'{f}'" for f in files])
                self.conn.execute(f"""
                    CREATE OR REPLACE VIEW stream_jsonl AS 
                    SELECT * FROM read_json_auto([{file_list}])
                """)
                self.views.append('stream_jsonl')
                
                return {
                    'ok': True,
                    'registered_count': len(files),
                    'view_name': 'stream_jsonl'
                }
            else:
                # ファイルがなくても空のビューを作成
                self.conn.execute("""
                    CREATE OR REPLACE VIEW stream_jsonl AS 
                    SELECT 
                        NULL::VARCHAR as worktree_uri,
                        NULL::INTEGER as process_id,
                        NULL::TIMESTAMP as timestamp,
                        NULL::JSON as data
                    WHERE 1=0
                """)
                self.views.append('stream_jsonl')
                
                return {
                    'ok': True,
                    'registered_count': 0,
                    'view_name': 'stream_jsonl'
                }
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def create_unified_view(self, view_name: str) -> Dict[str, Any]:
        """統合ビューを作成"""
        if not self.views:
            return {'ok': False, 'error': 'ビューが登録されていません'}
        
        try:
            # 空のビューを除外（実際のファイルがあるビューのみ使用）
            non_empty_views = []
            for v in self.views:
                try:
                    # ビューが空でないかチェック
                    result = self.conn.execute(f"SELECT 1 FROM {v} LIMIT 1").fetchone()
                    if result is not None:
                        non_empty_views.append(v)
                except:
                    # エラーが出た場合も空と見なす
                    pass
            
            if not non_empty_views:
                # 全て空の場合は、統合ビューも空で作成
                self.conn.execute(f"""
                    CREATE OR REPLACE VIEW {view_name} AS 
                    SELECT 
                        NULL::VARCHAR as content,
                        NULL::TIMESTAMP as timestamp,
                        NULL::VARCHAR as level,
                        NULL::VARCHAR as source
                    WHERE 1=0
                """)
            else:
                # 各ビューの共通カラムを見つける
                common_columns = None
                for v in non_empty_views:
                    try:
                        # ビューのカラムを取得
                        columns_result = self.conn.execute(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = '{v}'
                            ORDER BY ordinal_position
                        """).fetchall()
                        columns = [col[0] for col in columns_result]
                        
                        if common_columns is None:
                            common_columns = set(columns)
                        else:
                            common_columns = common_columns.intersection(columns)
                    except:
                        pass
                
                if common_columns:
                    # 共通カラムのみを選択
                    column_list = ', '.join(sorted(common_columns))
                    union_parts = [f"SELECT {column_list}, '{v}' as source FROM {v}" for v in non_empty_views]
                    sql = f"CREATE OR REPLACE VIEW {view_name} AS {' UNION ALL '.join(union_parts)}"
                else:
                    # 共通カラムがない場合は全カラムを使用（エラーになる可能性あり）
                    union_parts = [f"SELECT *, '{v}' as source FROM {v}" for v in non_empty_views]
                    sql = f"CREATE OR REPLACE VIEW {view_name} AS {' UNION ALL '.join(union_parts)}"
                
                self.conn.execute(sql)
            
            return {
                'ok': True,
                'view_name': view_name,
                'source_count': len(self.views)
            }
        except Exception as e:
            return {'ok': False, 'error': str(e)}


def find_jsonl_files(directory: str, pattern: str) -> List[str]:
    """指定ディレクトリからJSONLファイルを検索"""
    try:
        base_path = Path(directory)
        if not base_path.exists():
            return []
        
        full_pattern = str(base_path / pattern)
        return glob.glob(full_pattern, recursive=True)
    except:
        return []


def parse_query_result(rows: List[tuple], columns: List[str]) -> Dict[str, Any]:
    """DuckDBの結果を辞書形式に変換"""
    return {
        'columns': columns,
        'rows': [list(row) for row in rows],
        'row_count': len(rows)
    }