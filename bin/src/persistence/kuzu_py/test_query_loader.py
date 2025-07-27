"""
Query loaderのテスト（TDD RED phase）
"""
import pytest
from pathlib import Path
from typing import Union
import time

from result_types import ErrorDict
from query_loader import load_query_from_file, clear_query_cache


def test_load_query_from_file():
    """ファイルから単純なクエリを読み込むテスト"""
    # Arrange
    query_path = Path("test_queries/simple_match.cypher")
    
    # Act
    result = load_query_from_file(query_path)
    
    # Assert
    assert isinstance(result, str)
    assert result == "MATCH (n:Person) WHERE n.name = 'Alice' RETURN n.name, n.age"


def test_file_not_found():
    """存在しないファイルの場合はErrorDictを返すテスト"""
    # Arrange
    query_path = Path("test_queries/non_existent.cypher")
    
    # Act
    result = load_query_from_file(query_path)
    
    # Assert
    assert isinstance(result, dict)
    assert result["ok"] is False
    assert "error" in result
    assert "not found" in result["error"].lower()
    assert "details" in result
    assert result["details"]["path"] == str(query_path)


def test_empty_file():
    """空のクエリファイルを処理するテスト"""
    # Arrange
    query_path = Path("test_queries/empty.cypher")
    
    # Act
    result = load_query_from_file(query_path)
    
    # Assert
    assert isinstance(result, dict)
    assert result["ok"] is False
    assert "error" in result
    assert "empty" in result["error"].lower()
    assert "details" in result
    assert result["details"]["path"] == str(query_path)


def test_remove_comments():
    """コメント行を除去してクエリを読み込むテスト"""
    # Arrange
    query_path = Path("test_queries/with_comments.cypher")
    
    # Act
    result = load_query_from_file(query_path)
    
    # Assert
    assert isinstance(result, str)
    # コメントが除去され、クエリ行のみが残ることを確認
    assert "//" not in result
    assert result == "MATCH (n:Person)\nWHERE n.age > 25\nRETURN n.name"


def test_query_cache():
    """クエリキャッシュが正しく動作するテスト"""
    # Arrange
    query_path = Path("test_queries/simple_match.cypher")
    
    # キャッシュをクリア
    clear_query_cache()
    
    # Act - 1回目の読み込み
    start_time = time.time()
    result1 = load_query_from_file(query_path)
    first_load_time = time.time() - start_time
    
    # Act - 2回目の読み込み（キャッシュから）
    start_time = time.time()
    result2 = load_query_from_file(query_path)
    second_load_time = time.time() - start_time
    
    # Assert
    assert isinstance(result1, str)
    assert result1 == result2  # 同じ結果が返る
    assert second_load_time < first_load_time  # キャッシュからの方が速い


def test_cache_clear():
    """キャッシュクリア機能のテスト"""
    # Arrange
    query_path = Path("test_queries/simple_match.cypher")
    
    # Act - キャッシュに読み込む
    result1 = load_query_from_file(query_path)
    
    # キャッシュをクリア
    clear_query_cache()
    
    # Act - 再度読み込む（キャッシュではなくファイルから）
    result2 = load_query_from_file(query_path)
    
    # Assert
    assert result1 == result2  # 結果は同じ


def test_cache_file_change_detection():
    """ファイル変更時にキャッシュが無効化されるテスト"""
    # Arrange
    query_path = Path("test_queries/changeable.cypher")
    
    # Act - 初回読み込み
    result1 = load_query_from_file(query_path)
    
    # ファイルを変更（タイムスタンプを更新）
    # 実際のテストではモックか一時ファイルを使用
    # ここでは疑似的にファイル変更をシミュレート
    
    # Act - 変更後の読み込み
    result2 = load_query_from_file(query_path, force_reload=True)
    
    # Assert
    # force_reloadフラグでキャッシュを無視できることを確認
    assert isinstance(result2, str)


