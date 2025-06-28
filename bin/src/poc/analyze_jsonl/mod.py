"""
analyze_jsonl - 分散JSONLファイルの集約・クエリツール

使用例:
    # 単一ディレクトリの分析
    >>> from analyze_jsonl import analyze_directory
    >>> result = analyze_directory('/var/log/app', "SELECT COUNT(*) as total FROM logs")
    >>> if result['ok']:
    ...     print(f"Total logs: {result['data']['rows'][0][0]}")
    
    # 複数ディレクトリの統合分析
    >>> from analyze_jsonl import analyze_directories
    >>> dirs = ['/var/log/app1', '/var/log/app2', '/var/log/app3']
    >>> result = analyze_directories(dirs, "SELECT * FROM all_logs WHERE level = 'error'")
    >>> if result['ok']:
    ...     print(f"Found {result['data']['row_count']} errors")
    
    # 低レベルAPI（より細かい制御が必要な場合）
    >>> from analyze_jsonl import create_analyzer
    >>> analyzer = create_analyzer(['/logs'])
    >>> analyzer.register_jsonl_files('/logs/app1', '*.jsonl', 'app1_logs')
    >>> result = analyzer.query("SELECT * FROM app1_logs LIMIT 10")

エクスポート:
    - analyze_directory: 単一ディレクトリの簡易分析
    - analyze_directories: 複数ディレクトリの統合分析  
    - create_analyzer: アナライザーインスタンスの作成
    - QueryResult: クエリ結果の型定義
"""

# スタンドアロン実行時は相対インポートを避ける
try:
    from .core import create_analyzer
    from .analyzer_types import QueryResult
except ImportError:
    from core import create_analyzer
    from analyzer_types import QueryResult

# 高レベルAPI（簡易インターフェース）
def analyze_directory(directory: str, sql: str, pattern: str = '*.jsonl') -> QueryResult:
    """
    単一ディレクトリのJSONLファイルを分析
    
    引数:
        directory: 分析対象ディレクトリ
        sql: 実行するSQLクエリ（ビュー名は 'logs' を使用）
        pattern: ファイルパターン（デフォルト: '*.jsonl'）
    
    戻り値:
        QueryResult: クエリ結果（ok=True）またはエラー（ok=False）
    """
    analyzer = create_analyzer([directory])
    # analyzerが辞書（エラー）の場合のみチェック
    if isinstance(analyzer, dict) and not analyzer['ok']:
        return analyzer
    
    analyzer.register_jsonl_files(directory, pattern, 'logs')
    return analyzer.query(sql)


def analyze_directories(directories: list[str], sql: str, pattern: str = '*.jsonl') -> QueryResult:
    """
    複数ディレクトリのJSONLファイルを統合分析
    
    引数:
        directories: 分析対象ディレクトリのリスト
        sql: 実行するSQLクエリ（統合ビュー名は 'all_logs' を使用）
        pattern: ファイルパターン（デフォルト: '*.jsonl'）
    
    戻り値:
        QueryResult: クエリ結果（ok=True）またはエラー（ok=False）
    """
    analyzer = create_analyzer(directories)
    # analyzerが辞書（エラー）の場合のみチェック
    if isinstance(analyzer, dict) and not analyzer['ok']:
        return analyzer
    
    # 各ディレクトリを登録
    for i, directory in enumerate(directories):
        analyzer.register_jsonl_files(directory, pattern, f'dir{i}')
    
    # 統合ビューを作成
    result = analyzer.create_unified_view('all_logs')
    if not result['ok']:
        return result
    
    return analyzer.query(sql)


# エクスポート
__all__ = [
    'analyze_directory',
    'analyze_directories', 
    'create_analyzer',
    'QueryResult',
]


# ====================
# REDフェーズ: 高レベルAPIのテスト
# ====================

def test_analyze_directory_有効なディレクトリ_分析成功():
    """有効なディレクトリを指定して分析できる"""
    result = analyze_directory('/tmp', "SELECT 1 as test")
    assert 'ok' in result
    # 実装前なのでエラーになることを確認


def test_analyze_directories_複数ディレクトリ_統合分析成功():
    """複数ディレクトリを統合して分析できる"""
    result = analyze_directories(['/tmp', '/var'], "SELECT COUNT(*) FROM all_logs")
    assert 'ok' in result
    # 実装前なのでエラーになることを確認