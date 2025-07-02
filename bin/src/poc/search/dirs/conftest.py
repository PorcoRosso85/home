"""pytest configuration for directory scanner tests
Run tests with: nix develop -c uv run pytest
"""

import os
import pytest
import tempfile
from typing import Generator, Any

# テスト環境変数設定
os.environ.update({
    'DIRSCAN_ROOT_PATH': '/tmp/test_scan',
    'DIRSCAN_DB_PATH': ':memory:',
    'DIRSCAN_INMEMORY': 'true'
})


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """一時ディレクトリを作成・削除するフィクスチャ
    
    Yields:
        一時ディレクトリのパス
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_directory_structure(temp_dir: str) -> str:
    """テスト用ディレクトリ構造を作成するフィクスチャ
    
    Args:
        temp_dir: 一時ディレクトリ
        
    Returns:
        作成したディレクトリのルートパス
    """
    # ディレクトリ構造作成
    os.makedirs(f"{temp_dir}/poc/auth")
    os.makedirs(f"{temp_dir}/poc/search/vss")
    os.makedirs(f"{temp_dir}/poc/.git")  # 隠しディレクトリ
    
    # READMEファイル作成
    with open(f"{temp_dir}/poc/auth/README.md", 'w') as f:
        f.write("# Authentication Module\n\nHandles user authentication")
    
    with open(f"{temp_dir}/poc/search/README.md", 'w') as f:
        f.write("# Search Module\n\nSearch functionality")
    
    # flake.nix作成
    with open(f"{temp_dir}/poc/search/flake.nix", 'w') as f:
        f.write('{\n  description = "Search POC";\n}')
    
    # package.json作成
    with open(f"{temp_dir}/poc/auth/package.json", 'w') as f:
        f.write('{"name": "auth", "description": "Authentication package"}')
    
    # Pythonファイル作成
    with open(f"{temp_dir}/poc/search/main.py", 'w') as f:
        f.write('"""Search implementation module"""\n\n')
    
    # 空ディレクトリ作成
    os.makedirs(f"{temp_dir}/poc/empty")
    
    return temp_dir


@pytest.fixture
def mock_scanner() -> Any:
    """モックスキャナーを作成するフィクスチャ
    
    Returns:
        create_directory_scanner関数
    """
    from main import create_directory_scanner
    return create_directory_scanner