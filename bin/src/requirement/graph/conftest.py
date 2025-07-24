"""
pytest設定ファイル - in-sourceテストの自動探索と環境設定
"""
import os
import sys
import pytest

# 環境変数の設定（テスト実行前）
# NOTE: テスト環境では必要な環境変数を事前に設定する
if 'LD_LIBRARY_PATH' not in os.environ:
    os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib'
if 'RGL_DB_PATH' not in os.environ:
    os.environ['RGL_DB_PATH'] = os.path.join(os.path.dirname(__file__), 'rgl_db')
if 'RGL_DATABASE_PATH' not in os.environ:
    os.environ['RGL_DATABASE_PATH'] = ':memory:'

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Check if kuzu is available
try:
    import kuzu
    KUZU_AVAILABLE = hasattr(kuzu, 'Database')
except ImportError:
    KUZU_AVAILABLE = False

# Skip kuzu tests if not available
requires_kuzu = pytest.mark.skipif(
    not KUZU_AVAILABLE,
    reason="KuzuDB not available or improperly installed"
)


# 収集時に除外するファイル
collect_ignore = [
    "run.py",
    "run_all_tests.py",
    "run_all_tests_with_env.py",
    "test_single_module.py",
    "test_migrated_features.py",  # pytestに依存
    "mod.py",  # モジュールエクスポート用
    "infrastructure/apply_ddl_schema.py",  # kuzu import error
]


def pytest_configure(config):
    """pytest設定のカスタマイズ"""
    # カスタムマーカーの登録（将来の拡張用）
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


# テスト実行時のオプション設定
def pytest_addoption(parser):
    """カスタムオプションの追加"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    """テスト収集後の処理"""
    # --run-slowが指定されていない場合、slowマークのテストをスキップ
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


@pytest.fixture(scope="session", autouse=True)
def cleanup_memory_files(request):
    """
    セッションレベルのクリーンアップフィクスチャ
    
    全テスト実行後に:memory:*ファイルを自動的に削除する。
    KuzuDBなどのインメモリデータベースがファイルシステムに
    作成する一時ファイルをクリーンアップする。
    """
    # テスト実行前は何もしない
    yield

    # テスト実行後のクリーンアップ
    import glob
    import shutil

    try:
        # カレントディレクトリから:memory:*パターンのファイルを検索
        memory_files = glob.glob(":memory:*")

        if memory_files:
            print(f"\nCleaning up {len(memory_files)} :memory:* files...")
            for file_path in memory_files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"  Removed: {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        print(f"  Removed directory: {file_path}")
                except Exception as e:
                    print(f"  Warning: Failed to remove {file_path}: {e}")

    except Exception as e:
        # クリーンアップ中のエラーはテスト結果に影響しないよう静かに処理
        print(f"\nWarning: Cleanup failed with error: {e}")
