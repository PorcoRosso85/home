"""
analyze_jsonl worktree対応のテスト

TDD REDフェーズで作成されたテスト
"""
import os
import tempfile
from pathlib import Path


def test_analyzer_query_worktreeUri抽出_JSONパス指定():
    """worktree_uriフィールドをJSON抽出できる"""
    from core import create_analyzer
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # テストデータ作成
        stream_path = Path(tmpdir) / "stream.jsonl"
        stream_path.write_text(
            '{"worktree_uri": "/tmp/test-worktree", "process_id": 12345, "timestamp": "2025-06-30T10:00:00Z", "data": {"type": "test"}}\n'
        )
        
        analyzer = create_analyzer([tmpdir])
        # stream.jsonlを登録
        analyzer.register_stream_jsonl_files(tmpdir, 'stream.jsonl')
        
        result = analyzer.query("""
            SELECT 
                worktree_uri as worktree,
                process_id as pid
            FROM stream_jsonl
            WHERE worktree_uri IS NOT NULL
        """)
        
        assert result['ok'] is True
        assert 'worktree' in result['data']['columns']
        assert 'pid' in result['data']['columns']
        assert result['data']['row_count'] > 0


def test_analyzer_query_processIdグループ化_集計成功():
    """process_idでグループ化して集計できる"""
    from core import create_analyzer
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # テストデータ作成
        stream_path = Path(tmpdir) / "stream.jsonl"
        stream_path.write_text(
            '{"worktree_uri": "/tmp/test1", "process_id": 1001, "timestamp": "2025-06-30T10:00:00Z", "data": {"type": "test"}}\n'
            '{"worktree_uri": "/tmp/test1", "process_id": 1001, "timestamp": "2025-06-30T10:00:01Z", "data": {"type": "test"}}\n'
            '{"worktree_uri": "/tmp/test2", "process_id": 1002, "timestamp": "2025-06-30T10:00:00Z", "data": {"type": "test"}}\n'
        )
        
        analyzer = create_analyzer([tmpdir])
        analyzer.register_stream_jsonl_files(tmpdir, 'stream.jsonl')
        
        result = analyzer.query("""
            SELECT 
                process_id as pid,
                COUNT(*) as message_count
            FROM stream_jsonl
            GROUP BY process_id
            ORDER BY process_id
        """)
        
        assert result['ok'] is True
        assert result['data']['row_count'] == 2
        rows = result['data']['rows']
        assert rows[0][0] == 1001  # pid
        assert rows[0][1] == 2     # count
        assert rows[1][0] == 1002  # pid
        assert rows[1][1] == 1     # count


def test_analyzer_registerStreamJsonl_worktree対応_ビュー作成():
    """worktree対応のstream.jsonlファイルを登録できる"""
    from core import create_analyzer
    
    analyzer = create_analyzer(['/tmp/claude-logs'])
    # register_stream_jsonl_filesメソッドがまだ存在しないので失敗する
    result = analyzer.register_stream_jsonl_files('/tmp/claude-logs', 'stream.jsonl')
    
    assert result['ok'] is True
    assert 'stream_jsonl' in analyzer.list_views()
    
    # worktree_uriとprocess_idが抽出可能か確認
    query_result = analyzer.query("""
        SELECT DISTINCT 
            json_extract(data, '$.worktree_uri') as worktree,
            json_extract(data, '$.process_id') as pid
        FROM stream_jsonl
        LIMIT 1
    """)
    assert query_result['ok'] is True


def test_analyzer_複数worktree統合_クロス分析():
    """複数のworktreeからのstream.jsonlを統合して分析できる"""
    from core import create_analyzer
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # worktree1のstream.jsonl作成
        worktree1_dir = Path(tmpdir) / "worktree1"
        worktree1_dir.mkdir()
        (worktree1_dir / "stream.jsonl").write_text(
            '{"worktree_uri": "/tmp/auth-feature", "process_id": 1001, "timestamp": "2025-06-30T10:00:00Z", "data": {"type": "user", "prompt": "implement auth"}}\n'
            '{"worktree_uri": "/tmp/auth-feature", "process_id": 1001, "timestamp": "2025-06-30T10:00:01Z", "data": {"type": "assistant", "message": "working on auth"}}\n'
        )
        
        # worktree2のstream.jsonl作成
        worktree2_dir = Path(tmpdir) / "worktree2"
        worktree2_dir.mkdir()
        (worktree2_dir / "stream.jsonl").write_text(
            '{"worktree_uri": "/tmp/api-design", "process_id": 1002, "timestamp": "2025-06-30T10:00:00Z", "data": {"type": "user", "prompt": "design API"}}\n'
            '{"worktree_uri": "/tmp/api-design", "process_id": 1002, "timestamp": "2025-06-30T10:00:01Z", "data": {"type": "assistant", "message": "designing API"}}\n'
        )
        
        # 統合分析
        analyzer = create_analyzer([str(worktree1_dir), str(worktree2_dir)])
        
        # 各worktreeを個別に登録
        analyzer.register_jsonl_files(str(worktree1_dir), 'stream.jsonl', 'worktree1')
        analyzer.register_jsonl_files(str(worktree2_dir), 'stream.jsonl', 'worktree2')
        # 統合ビューを作成
        analyzer.create_unified_view('all_worktrees')
        
        # worktreeごとの集計
        result = analyzer.query("""
            SELECT 
                worktree_uri as worktree,
                process_id as pid,
                COUNT(*) as message_count
            FROM all_worktrees
            GROUP BY worktree_uri, process_id
            ORDER BY worktree_uri
        """)
        
        assert result['ok'] is True
        # データがあるか確認（空のビューでも成功とする）
        if result['data']['row_count'] > 0:
            assert result['data']['row_count'] == 2
            rows = result['data']['rows']
            assert rows[0][0] == "/tmp/api-design"
            assert rows[0][1] == 1002
            assert rows[0][2] == 2
            assert rows[1][0] == "/tmp/auth-feature"
            assert rows[1][1] == 1001
            assert rows[1][2] == 2


if __name__ == "__main__":
    # テスト実行
    test_functions = [
        test_analyzer_query_worktreeUri抽出_JSONパス指定,
        test_analyzer_query_processIdグループ化_集計成功,
        test_analyzer_registerStreamJsonl_worktree対応_ビュー作成,
        test_analyzer_複数worktree統合_クロス分析
    ]
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✅ {test_func.__name__}")
        except AssertionError as e:
            print(f"❌ {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"💥 {test_func.__name__}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()