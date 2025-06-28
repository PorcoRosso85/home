"""
pytest設定ファイル - in-sourceテストの自動探索と環境設定
"""
import os
import sys
import pytest

# 環境変数の設定（テスト実行前）
os.environ.setdefault('LD_LIBRARY_PATH', '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib')
os.environ.setdefault('RGL_DB_PATH', os.path.join(os.path.dirname(__file__), 'rgl_db'))

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


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """テスト用の一時DBパスを提供"""
    return str(tmp_path_factory.mktemp("test_db"))


@pytest.fixture
def clean_env():
    """環境変数をクリーンアップするフィクスチャ"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


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