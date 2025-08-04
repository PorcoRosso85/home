"""Specification tests for duplicate flake detection business requirements.

This module tests the BEHAVIOR and BUSINESS VALUE, not implementation details.
It verifies that the system meets the business requirement:
"Detects flakes with 80%+ similarity as duplicates"
"""

from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock


def test_detects_semantically_similar_flakes_as_duplicates():
    """意味的に類似したflakeを重複グループとして検出する
    
    ビジネス価値: 15-30%のコード削減を実現
    """
    # Given: List of flakes with semantically similar descriptions
    flakes = [
        # KuzuDB関連のFlake群 - 意味的に同一のグループ
        {
            "path": Path("/src/kuzu/adapter"),
            "description": "KuzuDB database adapter for Python applications"
        },
        {
            "path": Path("/src/kuzu/client"),
            "description": "Python client library for KuzuDB graph database"
        },
        {
            "path": Path("/src/persistence/kuzu"),
            "description": "KuzuDB persistence layer implementation"
        },
        
        # 認証関連のFlake群 - 別の意味的グループ
        {
            "path": Path("/src/auth/basic"),
            "description": "Basic authentication service with user management"
        },
        {
            "path": Path("/src/auth/oauth"),
            "description": "OAuth2 authentication provider service"
        },
        
        # 独立したFlake
        {
            "path": Path("/src/payment/stripe"),
            "description": "Stripe payment processing integration"
        }
    ]
    
    # When: システムが重複検出を実行
    duplicate_groups = detect_duplicate_flakes_spec(flakes, similarity_threshold=0.85)
    
    # Then: 意味的に類似したグループが検出される
    assert len(duplicate_groups) >= 2, "At least 2 duplicate groups should be detected"
    
    # KuzuDB関連グループの検証
    kuzu_group = find_group_containing_path(duplicate_groups, "/src/kuzu/adapter")
    assert kuzu_group is not None, "KuzuDB-related flakes should form a group"
    assert len(kuzu_group["flakes"]) == 3, "All 3 KuzuDB flakes should be in one group"
    assert kuzu_group["similarity_score"] >= 0.85, "Similarity should be >= 85%"
    
    # 認証関連グループの検証
    auth_group = find_group_containing_path(duplicate_groups, "/src/auth/basic")
    assert auth_group is not None, "Auth-related flakes should form a group"
    assert len(auth_group["flakes"]) == 2, "Both auth flakes should be in one group"
    assert auth_group["similarity_score"] >= 0.85, "Similarity should be >= 85%"
    
    # 独立したFlakeは重複グループに含まれない
    payment_in_any_group = any(
        any(str(f["path"]).endswith("payment/stripe") for f in group["flakes"])
        for group in duplicate_groups
    )
    assert not payment_in_any_group, "Payment flake should not be in any duplicate group"


def test_business_impact_of_duplicate_detection():
    """重複検出によるビジネス価値の実現を検証
    
    期待される効果:
    - 15-30%のコード削減
    - メンテナンスコストの削減
    - 一貫性の向上
    """
    # Given: 実際のプロジェクトに近い重複パターン
    flakes = [
        # データベース接続の重複実装
        {"path": Path("/services/user-service/db"), "description": "PostgreSQL connection handling for user data"},
        {"path": Path("/services/order-service/db"), "description": "Database connection manager for PostgreSQL"},
        {"path": Path("/services/inventory/database"), "description": "PostgreSQL database connectivity layer"},
        
        # ロギングの重複実装
        {"path": Path("/lib/logger"), "description": "Structured logging with JSON output"},
        {"path": Path("/utils/logging"), "description": "JSON-based structured logger"},
        
        # 独自実装（重複なし）
        {"path": Path("/core/ml-engine"), "description": "Machine learning model inference engine"},
        {"path": Path("/external/weather-api"), "description": "Weather data API client"}
    ]
    
    # When: 重複検出を実行
    duplicate_groups = detect_duplicate_flakes_spec(flakes, similarity_threshold=0.85)
    
    # Then: ビジネス価値の検証
    total_flakes = len(flakes)
    duplicated_flakes = sum(len(group["flakes"]) for group in duplicate_groups)
    
    # 最低15%の重複が検出されることを確認
    duplication_ratio = (duplicated_flakes - len(duplicate_groups)) / total_flakes
    assert duplication_ratio >= 0.15, f"Expected at least 15% duplication, got {duplication_ratio*100:.1f}%"
    
    # 各グループが実際に統合可能な候補であることを確認
    for group in duplicate_groups:
        assert group["similarity_score"] >= 0.85, "All groups should have high similarity"
        assert len(group["flakes"]) >= 2, "Each group should have at least 2 flakes"


def test_japanese_and_english_similarity_detection():
    """日本語と英語の混在環境での類似性検出を検証"""
    flakes = [
        # 日本語での認証サービス記述
        {"path": Path("/src/auth/jp1"), "description": "ユーザー認証と権限管理のためのサービス"},
        {"path": Path("/src/auth/jp2"), "description": "認証機能とアクセス制御を提供するシステム"},
        
        # 英語での認証サービス記述
        {"path": Path("/src/auth/en1"), "description": "User authentication and authorization service"},
        {"path": Path("/src/auth/en2"), "description": "Authentication system with access control"},
        
        # 無関係なサービス
        {"path": Path("/src/backup"), "description": "定期的なデータバックアップサービス"},
        {"path": Path("/src/monitoring"), "description": "System monitoring and alerting"}
    ]
    
    # When: 言語を跨いだ重複検出
    duplicate_groups = detect_duplicate_flakes_spec(flakes, similarity_threshold=0.85)
    
    # Then: 同一言語内での重複は検出される
    assert len(duplicate_groups) >= 1, "At least Japanese auth group should be detected"
    
    # 日本語グループの検証
    jp_auth_group = find_group_containing_path(duplicate_groups, "/src/auth/jp1")
    if jp_auth_group:
        assert len(jp_auth_group["flakes"]) >= 2, "Japanese auth services should be grouped"


def test_gradual_similarity_levels():
    """異なる類似度レベルでの検出精度を検証"""
    flakes = [
        # 非常に類似した説明（90%+）
        {"path": Path("/src/api/v1"), "description": "RESTful API for user management"},
        {"path": Path("/src/api/v2"), "description": "REST API for managing users"},
        
        # やや類似した説明（85%程度）
        {"path": Path("/src/cache/redis"), "description": "Redis-based caching layer"},
        {"path": Path("/src/cache/memory"), "description": "In-memory caching service"},
        
        # 低い類似度（70%未満）
        {"path": Path("/src/email"), "description": "Email notification service"},
        {"path": Path("/src/sms"), "description": "SMS messaging gateway"}
    ]
    
    # When: 85%閾値での検出
    strict_groups = detect_duplicate_flakes_spec(flakes, similarity_threshold=0.85)
    
    # When: 70%閾値での検出
    loose_groups = detect_duplicate_flakes_spec(flakes, similarity_threshold=0.70)
    
    # Then: 閾値による検出数の違いを検証
    assert len(strict_groups) >= 1, "High similarity APIs should be detected at 85%"
    assert len(loose_groups) > len(strict_groups), "More groups should be detected at lower threshold"


# Helper functions for specification tests
def detect_duplicate_flakes_spec(
    flakes: List[Dict[str, Any]], 
    similarity_threshold: float
) -> List[Dict[str, Any]]:
    """
    Specification interface for duplicate detection.
    Returns list of duplicate groups with similarity scores.
    """
    # This is a specification test - implementation is mocked
    # In real usage, this would call the actual duplicate detector
    # with VSS enabled and the specified threshold
    
    # For test purposes, return expected behavior
    from flake_graph.duplicate_detector import find_duplicate_flakes
    import pytest
    
    # Attempt to detect duplicates with VSS
    result = find_duplicate_flakes(flakes, use_vss=True, similarity_threshold=similarity_threshold)
    
    # If VSS is not available, skip the test
    if not result:
        # Check if VSS initialization failed by attempting a simple test
        from flake_graph.vss_adapter import create_vss
        vss = create_vss(db_path=":memory:")
        if isinstance(vss, dict) and 'type' in vss:
            pytest.skip(f"VSS not available in test environment: {vss.get('message')}")
    
    return result


def find_group_containing_path(groups: List[Dict[str, Any]], path_substring: str) -> Dict[str, Any]:
    """Find the duplicate group containing a flake with the given path substring."""
    for group in groups:
        for flake in group["flakes"]:
            if path_substring in str(flake["path"]):
                return group
    return None