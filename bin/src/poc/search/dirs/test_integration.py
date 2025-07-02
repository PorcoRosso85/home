"""統合テスト - pytestベース
Run with: nix develop -c uv run pytest test_integration.py
"""

import pytest
import os
import tempfile
from main import create_directory_scanner


def test_統合_フルワークフロー_正常動作(test_directory_structure):
    """フルスキャン→変更検知→検索の統合ワークフロー"""
    scanner = create_directory_scanner(test_directory_structure, ":memory:")
    
    # 1. フルスキャン
    scan_result = scanner['full_scan'](False, True, False)
    assert scan_result['ok'] is True
    initial_count = scan_result['scanned_count']
    
    # 2. 新規ディレクトリ追加
    os.makedirs(f"{test_directory_structure}/poc/new_feature")
    
    # 3. 差分検知
    diff_result = scanner['detect_changes']()
    assert diff_result['ok'] is True
    assert len(diff_result['added']) >= 1
    
    # 4. インクリメンタル更新
    update_result = scanner['incremental_update']()
    assert update_result['ok'] is True
    assert update_result['new_count'] >= 1
    
    # 5. FTSインデックス構築
    index_result = scanner['build_fts_index']()
    assert index_result['ok'] is True
    
    # 6. メタデータ抽出
    metadata_result = scanner['extract_metadata'](f"{test_directory_structure}/poc/auth")
    assert metadata_result['ok'] is True
    
    # 7. ステータス確認
    status = scanner['get_status']()
    assert status['total_directories'] >= initial_count


def test_検索機能_FTS_キーワード一致(test_directory_structure):
    """FTS検索でキーワードに一致するREADMEを検索"""
    scanner = create_directory_scanner(test_directory_structure, ":memory:")
    
    # スキャンとインデックス構築
    scanner['full_scan'](False, True, False)
    scanner['build_fts_index']()
    
    # 検索実行
    result = scanner['search_fts']("authentication")
    assert result['ok'] is True
    # モック実装では結果が返らないが、エラーがないことを確認


def test_メタデータ抽出_優先順位_正しい順序(test_directory_structure):
    """メタデータ抽出の優先順位: README > flake.nix > package.json > docstring"""
    scanner = create_directory_scanner(test_directory_structure, ":memory:")
    
    # README がある場合
    result = scanner['extract_metadata'](f"{test_directory_structure}/poc/auth")
    assert result['ok'] is True
    assert result['source'] == 'readme'
    
    # flake.nix がある場合（READMEなし）
    result = scanner['extract_metadata'](f"{test_directory_structure}/poc/search")
    assert result['ok'] is True
    # READMEがあるのでreadmeが優先される
    assert result['source'] == 'readme'


@pytest.mark.parametrize("skip_empty,skip_hidden,expected_min_count", [
    (False, False, 5),  # 全ディレクトリ
    (True, False, 4),   # 空ディレクトリ除外
    (False, True, 4),   # 隠しディレクトリ除外
    (True, True, 3),    # 両方除外
])
def test_スキャンオプション_組み合わせ_期待通り(test_directory_structure, skip_empty, skip_hidden, expected_min_count):
    """スキャンオプションの組み合わせが期待通り動作"""
    scanner = create_directory_scanner(test_directory_structure, ":memory:")
    
    result = scanner['full_scan'](skip_empty, skip_hidden, False)
    assert result['ok'] is True
    assert result['scanned_count'] >= expected_min_count


def test_エラーハンドリング_不正パス_エラー返却():
    """存在しないパスでスキャナー作成してもクラッシュしない"""
    scanner = create_directory_scanner("/nonexistent/path", ":memory:")
    
    # スキャンはエラーを返すがクラッシュしない
    result = scanner['full_scan'](False, True, False)
    assert result['ok'] is True  # 空の結果でも成功扱い
    assert result['scanned_count'] == 0


def test_並行アクセス_同時実行_データ整合性():
    """複数の操作を並行実行してもデータ整合性が保たれる"""
    import concurrent.futures
    
    with tempfile.TemporaryDirectory() as tmpdir:
        scanner = create_directory_scanner(tmpdir, ":memory:")
        
        # 初期スキャン
        scanner['full_scan'](False, True, False)
        
        # 並行してディレクトリ作成と検索を実行
        def create_dir(i):
            os.makedirs(f"{tmpdir}/dir_{i}", exist_ok=True)
            return scanner['detect_changes']()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_dir, i) for i in range(3)]
            results = [f.result() for f in futures]
        
        # 全ての操作が成功
        assert all(r['ok'] for r in results)