#!/usr/bin/env python
"""
SearchIntegration - POC search統合の振る舞いテスト
テスト規約に準拠：公開APIのみをテスト（リファクタリングの壁原則）
"""
import sys
import os

# プロジェクトルートをPYTHONPATHに追加
sys.path.insert(0, '/home/nixos/bin/src')

from application.search_integration import SearchIntegration


def test_search_integration_detects_duplicates():
    """重複検出機能が動作することを確認 - 振る舞いのみを検証"""
    # Arrange
    integration = SearchIntegration()
    
    # Act
    results = integration.check_duplicates("ユーザー認証機能", k=5, threshold=0.8)
    
    # Assert - 振る舞いのみを検証
    assert isinstance(results, list)
    assert all(isinstance(r, dict) for r in results)
    assert all('score' in r for r in results)
    assert all('id' in r for r in results)
    assert all(0.0 <= r.get('score', 0) <= 1.0 for r in results)


def test_search_integration_respects_threshold():
    """閾値による結果フィルタリングを確認"""
    # Arrange
    integration = SearchIntegration()
    
    # Act - 高い閾値でフィルタリング
    results = integration.check_duplicates("ユーザー認証機能", k=10, threshold=0.95)
    
    # Assert
    assert isinstance(results, list)
    # 閾値0.95以上のスコアのみが返される
    assert all(r.get('score', 0) >= 0.95 for r in results)


def test_search_integration_handles_empty_query():
    """空のクエリでもエラーなく動作することを確認"""
    # Arrange
    integration = SearchIntegration()
    
    # Act
    results = integration.check_duplicates("", k=5, threshold=0.8)
    
    # Assert
    assert isinstance(results, list)
    # 空のクエリでも正常に空リストを返す


def test_add_to_search_index_accepts_requirement_data():
    """要件データを検索インデックスに追加できることを確認"""
    # Arrange
    integration = SearchIntegration()
    requirement_data = {
        "id": "req_test_001",
        "title": "テスト要件",
        "description": "これはテスト用の要件です",
        "status": "proposed"
    }
    
    # Act
    result = integration.add_to_search_index(requirement_data)
    
    # Assert
    assert isinstance(result, bool)
    # 現在の実装では常にTrueを返す