"""データベースファクトリーのテスト
Run with: nix develop -c uv run pytest test_database_factory.py
"""

import pytest
import os
from infrastructure.db.database_factory import (
    create_database, create_connection, create_database_and_connection
)


def test_database作成_inmemory_成功():
    """インメモリデータベースの作成"""
    result = create_database(None, True)
    if not result['ok']:
        print(f"Error: {result['error']}")
    assert result['ok'] is True
    assert result['database'] is not None


def test_database作成_永続化_成功(temp_dir):
    """永続化データベースの作成"""
    db_path = f"{temp_dir}/test.db"
    result = create_database(db_path, False)
    assert result['ok'] is True
    assert result['database'] is not None
    assert os.path.exists(db_path)


def test_database作成_パスなし永続化_エラー():
    """永続化でパス未指定はエラー"""
    result = create_database(None, False)
    assert result['ok'] is False
    assert 'path is required' in result['error']


def test_connection作成_正常_成功():
    """データベース接続の作成"""
    # まずデータベースを作成
    db_result = create_database(None, True)
    assert db_result['ok'] is True
    
    # 接続を作成
    conn_result = create_connection(db_result['database'])
    assert conn_result['ok'] is True
    assert conn_result['connection'] is not None


def test_database_and_connection作成_inmemory_成功():
    """データベースと接続を同時作成（インメモリ）"""
    result = create_database_and_connection(None, True)
    assert result['ok'] is True
    assert result['connection'] is not None


def test_database_and_connection作成_永続化_成功(temp_dir):
    """データベースと接続を同時作成（永続化）"""
    db_path = f"{temp_dir}/test.db"
    result = create_database_and_connection(db_path, False)
    assert result['ok'] is True
    assert result['connection'] is not None
    assert os.path.exists(db_path)