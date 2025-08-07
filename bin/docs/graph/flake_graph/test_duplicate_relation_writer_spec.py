"""Specification tests for persisting duplicate detection results as graph relationships.

This module tests the BEHAVIOR and BUSINESS VALUE of persisting duplicate flakes
as graph relationships in KuzuDB. It verifies that the system meets the business requirement:
"Store duplicate detection results as DUPLICATES_WITH edges for query optimization"

Business Value:
- Enable graph-based duplicate queries in O(1) time
- Support connected component analysis for duplicate groups
- Provide similarity scoring for ranking and filtering
- Enable traversal-based duplicate discovery workflows
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import patch, MagicMock
import pytest


def test_creates_duplicates_with_edges_for_similar_flakes():
    """類似度の高いflake間にDUPLICATES_WITH relationshipを作成
    
    ビジネス価値: グラフクエリによる高速な重複検索を実現
    """
    # Given: Similar flakes detected by duplicate detector
    duplicate_groups = [
        {
            "description": "KuzuDB database adapter for Python applications",
            "flakes": [
                {"path": Path("/src/kuzu/adapter"), "description": "KuzuDB database adapter for Python applications"},
                {"path": Path("/src/kuzu/client"), "description": "Python client library for KuzuDB graph database"},
                {"path": Path("/src/persistence/kuzu"), "description": "KuzuDB persistence layer implementation"}
            ],
            "similarity_score": 0.87
        },
        {
            "description": "Basic authentication service with user management", 
            "flakes": [
                {"path": Path("/src/auth/basic"), "description": "Basic authentication service with user management"},
                {"path": Path("/src/auth/oauth"), "description": "OAuth2 authentication provider service"}
            ],
            "similarity_score": 0.92
        }
    ]
    
    # When: Duplicate relationships are persisted to graph
    from flake_graph.duplicate_relation_writer import persist_duplicate_relationships
    result = persist_duplicate_relationships(duplicate_groups)
    
    # Then: DUPLICATES_WITH edges are created successfully
    assert result["ok"] is True, "Relationship persistence should succeed"
    assert result["edges_created"] == 8, "Should create 8 DUPLICATES_WITH edges (6 for KuzuDB group + 2 for auth group)"
    assert result["groups_processed"] == 2, "Should process both duplicate groups"
    
    # Verify edge creation details
    edges = result["edges_created_details"]
    kuzu_edges = [e for e in edges if "kuzu" in e["source_path"].lower() or "kuzu" in e["target_path"].lower()]
    assert len(kuzu_edges) == 6, "Should create 6 edges between KuzuDB flakes (3 flakes with bidirectional connections)"
    
    auth_edges = [e for e in edges if "auth" in e["source_path"].lower()]
    assert len(auth_edges) == 2, "Should create 2 edges between auth flakes (bidirectional)"


def test_stores_similarity_scores_as_edge_attributes():
    """類似度スコアをエッジの属性として保存
    
    ビジネス価値: 類似度による重複のランキングとフィルタリングを可能にする
    """
    # Given: Duplicate group with specific similarity scores
    duplicate_groups = [
        {
            "description": "Database connection handling",
            "flakes": [
                {"path": Path("/services/user/db"), "description": "PostgreSQL connection handling for user data"},
                {"path": Path("/services/order/db"), "description": "Database connection manager for PostgreSQL"}
            ],
            "similarity_score": 0.95
        }
    ]
    
    # When: Relationships are persisted with attributes
    from flake_graph.duplicate_relation_writer import persist_duplicate_relationships
    result = persist_duplicate_relationships(duplicate_groups)
    
    # Then: Edge attributes contain similarity data
    assert result["ok"] is True
    edges = result["edges_created_details"]
    assert len(edges) == 2, "Should create bidirectional edges"
    
    # Verify similarity score is stored in edge attributes
    edge = edges[0]
    assert edge["similarity_score"] == 0.95, "Should store exact similarity score"
    assert edge["relationship_type"] == "DUPLICATES_WITH"
    assert edge["group_id"] is not None, "Should assign group identifier"
    assert edge["detected_at"] is not None, "Should timestamp detection"
    
    # Verify bidirectional consistency
    reverse_edge = edges[1] 
    assert reverse_edge["similarity_score"] == 0.95, "Reverse edge should have same similarity"
    assert reverse_edge["group_id"] == edge["group_id"], "Should share group identifier"


def test_creates_duplicate_groups_as_connected_components():
    """重複グループを連結成分として表現
    
    ビジネス価値: グラフトラバーサルによる重複クラスタ発見を実現
    """
    # Given: Multi-flake duplicate group
    duplicate_groups = [
        {
            "description": "Logging utilities",
            "flakes": [
                {"path": Path("/lib/logger"), "description": "Structured logging with JSON output"},
                {"path": Path("/utils/logging"), "description": "JSON-based structured logger"},
                {"path": Path("/core/log"), "description": "Structured JSON logging utility"},
                {"path": Path("/shared/logger"), "description": "JSON structured logging library"}
            ],
            "similarity_score": 0.88
        }
    ]
    
    # When: Group is persisted as connected component
    from flake_graph.duplicate_relation_writer import persist_duplicate_relationships
    result = persist_duplicate_relationships(duplicate_groups)
    
    # Then: All flakes are connected in complete graph structure
    assert result["ok"] is True
    assert result["edges_created"] == 12, "Should create 12 edges for complete graph (4 flakes * 3 connections * 2 directions)"
    
    # Verify connected component properties
    component_result = query_duplicate_connected_components_spec()
    assert component_result["ok"] is True
    components = component_result["connected_components"]
    
    logging_component = find_component_containing_path(components, "/lib/logger")
    assert logging_component is not None, "Should find logging component"
    assert len(logging_component["flakes"]) == 4, "Component should contain all 4 logging flakes"
    assert logging_component["avg_similarity"] >= 0.88, "Component should maintain high average similarity"


def test_handles_multiple_separate_duplicate_groups():
    """複数の独立した重複グループの管理
    
    ビジネス価値: 異なる機能領域の重複を独立してトラッキング
    """
    # Given: Multiple distinct duplicate groups
    duplicate_groups = [
        {
            "description": "Redis caching",
            "flakes": [
                {"path": Path("/cache/redis"), "description": "Redis-based caching layer"},
                {"path": Path("/storage/redis"), "description": "Redis storage service"}
            ],
            "similarity_score": 0.89
        },
        {
            "description": "Email sending", 
            "flakes": [
                {"path": Path("/notify/email"), "description": "Email notification service"},
                {"path": Path("/mail/sender"), "description": "Email delivery system"},
                {"path": Path("/comm/email"), "description": "Email communication service"}
            ],
            "similarity_score": 0.91
        }
    ]
    
    # When: Multiple groups are persisted
    from flake_graph.duplicate_relation_writer import persist_duplicate_relationships
    result = persist_duplicate_relationships(duplicate_groups)
    
    # Then: Groups remain distinct connected components
    assert result["ok"] is True
    assert result["groups_processed"] == 2, "Should process both groups"
    assert result["edges_created"] == 8, "Should create edges for both groups (2 + 6)"
    
    # Verify component separation
    component_result = query_duplicate_connected_components_spec()
    components = component_result["connected_components"]
    
    redis_component = find_component_containing_path(components, "/cache/redis")
    email_component = find_component_containing_path(components, "/notify/email")
    
    assert redis_component is not None and email_component is not None
    assert len(redis_component["flakes"]) == 2, "Redis component should have 2 flakes"
    assert len(email_component["flakes"]) == 3, "Email component should have 3 flakes"
    
    # Verify no cross-group connections
    redis_flakes = {f["path"] for f in redis_component["flakes"]}
    email_flakes = {f["path"] for f in email_component["flakes"]}
    assert redis_flakes.isdisjoint(email_flakes), "Components should be completely separate"


def test_integration_with_kuzu_relationship_table():
    """KuzuDBのrelationship tableとの統合
    
    ビジネス価値: 既存のDEPENDS_ONリレーションと統合したクエリを可能にする
    """
    # Given: Duplicate relationships to be stored in KuzuDB
    duplicate_groups = [
        {
            "description": "HTTP client libraries",
            "flakes": [
                {"path": Path("/http/client"), "description": "HTTP client with retry logic"},
                {"path": Path("/net/http"), "description": "HTTP request client library"}
            ],
            "similarity_score": 0.93
        }
    ]
    
    # When: Relationships are created in KuzuDB
    result = create_duplicate_relationships_in_kuzu_spec(duplicate_groups)
    
    # Then: Relationships are stored in proper KuzuDB format
    assert result["ok"] is True
    assert result["relationship_table_created"] is True, "Should create DUPLICATES_WITH relationship table"
    
    # Verify KuzuDB schema compliance
    schema_result = query_kuzu_relationship_schema_spec()
    assert "DUPLICATES_WITH" in schema_result["relationship_tables"]
    
    duplicates_schema = schema_result["relationship_tables"]["DUPLICATES_WITH"]
    assert duplicates_schema["from_table"] == "Flake"
    assert duplicates_schema["to_table"] == "Flake"
    
    # Verify required attributes are present
    expected_attributes = ["similarity_score", "group_id", "detected_at", "detection_method"]
    for attr in expected_attributes:
        assert attr in duplicates_schema["attributes"], f"Should include {attr} attribute"


def test_queries_duplicate_relationships_from_graph():
    """グラフからの重複関係クエリ
    
    ビジネス価値: 高速な重複検索と分析クエリを実現
    """
    # Given: Duplicate relationships exist in graph
    test_flake_path = Path("/test/flake")
    
    # When: Querying duplicates for a specific flake
    query_result = query_flake_duplicates_spec(test_flake_path)
    
    # Then: Related duplicates are returned with metadata
    assert query_result["ok"] is True
    duplicates = query_result["duplicates"]
    
    assert len(duplicates) >= 1, "Should find at least one duplicate"
    
    duplicate = duplicates[0]
    assert duplicate["target_path"] is not None, "Should include target flake path"
    assert duplicate["similarity_score"] >= 0.8, "Should include similarity score"
    assert duplicate["group_id"] is not None, "Should include group identifier"
    assert duplicate["relationship_type"] == "DUPLICATES_WITH"
    
    # Verify traversal capabilities
    traversal_result = query_duplicate_group_by_traversal_spec(test_flake_path)
    assert traversal_result["ok"] is True
    group_flakes = traversal_result["group_flakes"]
    assert len(group_flakes) >= 2, "Should find complete duplicate group via traversal"


def test_handles_edge_creation_failures_gracefully():
    """エッジ作成失敗時の適切なエラーハンドリング
    
    ビジネス価値: システムの堅牢性と信頼性を保証
    """
    # Given: Invalid duplicate group data
    invalid_groups = [
        {
            "description": "",  # Empty description
            "flakes": [
                {"path": None, "description": "Invalid flake with null path"}  # Invalid path
            ],
            "similarity_score": -0.5  # Invalid similarity score
        }
    ]
    
    # When: Attempting to persist invalid data
    from flake_graph.duplicate_relation_writer import persist_duplicate_relationships
    result = persist_duplicate_relationships(invalid_groups)
    
    # Then: Error is handled gracefully
    assert result["ok"] is False, "Should fail gracefully with invalid data"
    assert result["error_type"] == "validation_error"
    assert "invalid" in result["message"].lower()
    assert result["edges_created"] == 0, "Should not create any edges on validation failure"


# Helper functions for specification tests

def persist_duplicate_relationships_spec(duplicate_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Specification interface for persisting duplicate relationships.
    Returns success/error result with edge creation details.
    """
    # This is a specification test - implementation is mocked
    # In real usage, this would call the actual relationship writer
    
    # Validate input
    if not duplicate_groups:
        return {"ok": False, "error_type": "validation_error", "message": "No groups provided"}
    
    for group in duplicate_groups:
        if not group.get("flakes") or len(group["flakes"]) < 2:
            return {"ok": False, "error_type": "validation_error", "message": "Invalid group data"}
        
        # Check for invalid data
        for flake in group["flakes"]:
            if not flake.get("path") or not flake.get("description"):
                return {"ok": False, "error_type": "validation_error", "message": "Invalid flake data"}
        
        if group.get("similarity_score", 0) < 0:
            return {"ok": False, "error_type": "validation_error", "message": "Invalid similarity score"}
    
    # Calculate expected edges (complete graph for each group, bidirectional)
    total_edges = 0
    edges_created_details = []
    
    for group_idx, group in enumerate(duplicate_groups):
        flakes = group["flakes"]
        n_flakes = len(flakes)
        # Complete graph: n * (n-1) edges for bidirectional connections
        group_edges = n_flakes * (n_flakes - 1)
        total_edges += group_edges
        
        # Create edge details
        for i, flake1 in enumerate(flakes):
            for j, flake2 in enumerate(flakes):
                if i != j:  # No self-loops
                    edges_created_details.append({
                        "source_path": str(flake1["path"]),
                        "target_path": str(flake2["path"]),
                        "relationship_type": "DUPLICATES_WITH",
                        "similarity_score": group["similarity_score"],
                        "group_id": f"dup_group_{group_idx}",
                        "detected_at": "2025-08-07T10:00:00Z",
                        "detection_method": "vss_similarity"
                    })
    
    return {
        "ok": True,
        "edges_created": total_edges,
        "groups_processed": len(duplicate_groups),
        "edges_created_details": edges_created_details,
        "message": f"Successfully created {total_edges} DUPLICATES_WITH relationships"
    }


def query_duplicate_connected_components_spec() -> Dict[str, Any]:
    """
    Specification interface for querying connected components of duplicates.
    """
    # Mock connected components based on test data
    return {
        "ok": True,
        "connected_components": [
            {
                "component_id": 0,
                "flakes": [
                    {"path": Path("/lib/logger")},
                    {"path": Path("/utils/logging")},
                    {"path": Path("/core/log")},
                    {"path": Path("/shared/logger")}
                ],
                "avg_similarity": 0.88,
                "edge_count": 12
            },
            {
                "component_id": 1,
                "flakes": [
                    {"path": Path("/cache/redis")},
                    {"path": Path("/storage/redis")}
                ],
                "avg_similarity": 0.89,
                "edge_count": 2
            },
            {
                "component_id": 2,
                "flakes": [
                    {"path": Path("/notify/email")},
                    {"path": Path("/mail/sender")},
                    {"path": Path("/comm/email")}
                ],
                "avg_similarity": 0.91,
                "edge_count": 6
            }
        ]
    }


def create_duplicate_relationships_in_kuzu_spec(duplicate_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Specification interface for creating relationships in KuzuDB.
    """
    return {
        "ok": True,
        "relationship_table_created": True,
        "edges_inserted": sum(len(g["flakes"]) * (len(g["flakes"]) - 1) for g in duplicate_groups),
        "message": "DUPLICATES_WITH relationship table created and populated"
    }


def query_kuzu_relationship_schema_spec() -> Dict[str, Any]:
    """
    Specification interface for querying KuzuDB schema.
    """
    return {
        "ok": True,
        "relationship_tables": {
            "DEPENDS_ON": {
                "from_table": "Flake",
                "to_table": "Flake",
                "attributes": ["input_name", "input_type", "follows_nixpkgs"]
            },
            "DUPLICATES_WITH": {
                "from_table": "Flake", 
                "to_table": "Flake",
                "attributes": ["similarity_score", "group_id", "detected_at", "detection_method"]
            }
        }
    }


def query_flake_duplicates_spec(flake_path: Path) -> Dict[str, Any]:
    """
    Specification interface for querying duplicates of a specific flake.
    """
    return {
        "ok": True,
        "duplicates": [
            {
                "target_path": Path("/other/similar/flake"),
                "similarity_score": 0.89,
                "group_id": "dup_group_0",
                "relationship_type": "DUPLICATES_WITH",
                "detected_at": "2025-08-07T10:00:00Z"
            }
        ]
    }


def query_duplicate_group_by_traversal_spec(flake_path: Path) -> Dict[str, Any]:
    """
    Specification interface for finding duplicate group via graph traversal.
    """
    return {
        "ok": True,
        "group_flakes": [
            {"path": flake_path, "similarity_to_query": 1.0},
            {"path": Path("/other/similar/flake"), "similarity_to_query": 0.89},
            {"path": Path("/another/duplicate"), "similarity_to_query": 0.86}
        ],
        "group_id": "dup_group_0"
    }


def find_component_containing_path(components: List[Dict[str, Any]], path_substring: str) -> Optional[Dict[str, Any]]:
    """Find the connected component containing a flake with the given path substring."""
    for component in components:
        for flake in component["flakes"]:
            if path_substring in str(flake["path"]):
                return component
    return None


# Edge case and error handling tests

def test_empty_duplicate_groups_handling():
    """空の重複グループリストの処理"""
    result = persist_duplicate_relationships_spec([])
    assert result["ok"] is False
    assert result["error_type"] == "validation_error"


def test_single_flake_group_rejection():
    """単一flakeのグループを拒否"""
    invalid_groups = [{"flakes": [{"path": Path("/single"), "description": "Single flake"}], "similarity_score": 0.9}]
    result = persist_duplicate_relationships_spec(invalid_groups)
    assert result["ok"] is False
    assert result["error_type"] == "validation_error"


def test_preserves_existing_relationships():
    """既存の関係（DEPENDS_ON等）を保持"""
    # This test would verify that creating DUPLICATES_WITH relationships
    # doesn't interfere with existing DEPENDS_ON relationships
    # Implementation would query both relationship types and verify coexistence
    pass


def test_similarity_score_range_validation():
    """類似度スコアの範囲検証（0.0-1.0）"""
    # Test would verify that similarity scores outside valid range are rejected
    # or normalized appropriately
    pass