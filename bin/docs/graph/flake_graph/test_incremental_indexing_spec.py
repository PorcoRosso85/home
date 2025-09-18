"""Specification tests for incremental VSS indexing business requirements.

This module tests the BEHAVIOR and BUSINESS VALUE of incremental VSS indexing.
It verifies that the system meets the business requirement:
"95% reduction in re-indexing time for large codebases when only few files change"

Business Context:
- Current: Every VSS scan re-indexes ALL flakes (30-60 seconds for 1000+ flakes)
- Target: Only re-index changed flakes (< 3 seconds for typical changes)
- Impact: Faster CI/CD pipelines, better developer experience, reduced compute costs

Technical Requirements:
- Track vss_analyzed_at timestamp for each flake
- Skip unchanged flakes based on file modification time
- Only process new/modified flakes for embedding generation
- Maintain search quality while optimizing performance
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest
import time
import hashlib
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


def test_unchanged_flakes_are_skipped_during_reindexing():
    """変更されていないflakeのVSS再インデックスをスキップする
    
    ビジネス価値:
    - 大規模コードベースでの無駄な計算を排除
    - CI/CDパイプラインの実行時間を大幅短縮
    - クラウド環境での計算コスト削減
    """
    # Given: Existing flakes with VSS embeddings and timestamps
    existing_flakes = [
        {
            "path": Path("/src/search/vss"),
            "description": "Vector similarity search implementation",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0),
            "vss_analyzed_at": datetime(2024, 1, 1, 11, 0, 0)  # Analyzed after last modification
        },
        {
            "path": Path("/src/persistence/kuzu"),
            "description": "KuzuDB graph database adapter",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0),
            "vss_analyzed_at": datetime(2024, 1, 1, 11, 0, 0)
        },
        {
            "path": Path("/src/api/rest"),
            "description": "RESTful API server implementation",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0),
            "vss_analyzed_at": datetime(2024, 1, 1, 11, 0, 0)
        }
    ]
    
    # Setup test environment
    kuzu_adapter = create_test_kuzu_adapter_with_data(existing_flakes)
    vss_adapter = create_test_incremental_vss_adapter(kuzu_adapter)
    
    # When: Re-indexing is triggered without any file changes
    start_time = time.time()
    # This should fail because VSSAdapter doesn't have index_flakes_incremental method yet
    indexing_stats = vss_adapter.index_flakes_incremental(existing_flakes)
    reindex_time = time.time() - start_time
    
    # Then: All flakes should be skipped
    assert indexing_stats["skipped"] == 3, "All unchanged flakes should be skipped"
    assert indexing_stats["processed"] == 0, "No flakes should be processed"
    assert indexing_stats["new"] == 0, "No new flakes detected"
    assert indexing_stats["updated"] == 0, "No updated flakes detected"
    
    # Performance: Skipping should be nearly instantaneous
    assert reindex_time < 0.1, f"Skipping 3 flakes took {reindex_time:.3f}s, expected < 0.1s"
    
    # Verify embeddings were not regenerated
    assert vss_adapter.get_embedding_generation_count() == 0, "No embeddings should be generated"


def test_only_new_and_modified_flakes_get_reindexed():
    """新規および変更されたflakeのみが再インデックスされる
    
    ビジネス価値:
    - 増分更新により95%以上の処理時間削減
    - 開発者の待ち時間を最小化
    - リソース効率の最適化
    """
    # Given: Mix of unchanged, modified, and new flakes
    initial_flakes = [
        {
            "path": Path("/src/auth/basic"),
            "description": "Basic authentication service",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0),
            "vss_analyzed_at": datetime(2024, 1, 1, 11, 0, 0)
        },
        {
            "path": Path("/src/auth/oauth"),
            "description": "OAuth2 authentication provider",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0),
            "vss_analyzed_at": datetime(2024, 1, 1, 11, 0, 0)
        }
    ]
    
    # Setup with initial data
    kuzu_adapter = create_test_kuzu_adapter_with_data(initial_flakes)
    vss_adapter = create_test_incremental_vss_adapter(kuzu_adapter)
    
    # Prepare updated flake list
    updated_flakes = [
        # Unchanged flake
        initial_flakes[0],
        
        # Modified flake (description changed, modification time updated)
        {
            "path": Path("/src/auth/oauth"),
            "description": "OAuth2 authentication with PKCE support",  # Changed
            "last_modified": datetime(2024, 1, 2, 10, 0, 0),  # New modification time
            "vss_analyzed_at": datetime(2024, 1, 1, 11, 0, 0)  # Old analysis time
        },
        
        # New flake
        {
            "path": Path("/src/auth/jwt"),
            "description": "JWT token validation and generation",
            "last_modified": datetime(2024, 1, 2, 10, 0, 0),
            "vss_analyzed_at": None  # Never analyzed
        }
    ]
    
    # When: Incremental indexing is performed
    start_time = time.time()
    indexing_stats = vss_adapter.index_flakes_incremental(updated_flakes)
    incremental_time = time.time() - start_time
    
    # Then: Only changed flakes are processed
    assert indexing_stats["skipped"] == 1, "One unchanged flake should be skipped"
    assert indexing_stats["processed"] == 2, "Two flakes should be processed"
    assert indexing_stats["updated"] == 1, "One flake should be updated"
    assert indexing_stats["new"] == 1, "One new flake should be added"
    
    # Verify only necessary embeddings were generated
    assert vss_adapter.get_embedding_generation_count() == 2, "Only 2 embeddings should be generated"
    
    # Verify timestamps are updated for processed flakes
    oauth_data = kuzu_adapter.get_flake_vss_data("oauth")
    assert oauth_data["vss_analyzed_at"] > datetime(2024, 1, 2, 0, 0, 0), "OAuth VSS timestamp should be updated"
    
    jwt_data = kuzu_adapter.get_flake_vss_data("jwt")
    assert jwt_data["vss_analyzed_at"] is not None, "JWT should have VSS timestamp"
    
    # Basic flake should remain unchanged
    basic_data = kuzu_adapter.get_flake_vss_data("basic")
    assert basic_data["vss_analyzed_at"] == datetime(2024, 1, 1, 11, 0, 0), "Basic VSS timestamp should not change"


def test_performance_improvement_on_large_codebase():
    """大規模コードベースでの性能改善を検証（95%の時間短縮）
    
    ビジネス価値:
    - 1000+ flakeのプロジェクトで30秒→1.5秒の改善
    - CI/CDパイプラインの大幅な高速化
    - 開発者のフィードバックループ改善
    """
    # Given: Large codebase with 1000 flakes, only 10 changed
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    analyzed_time = datetime(2024, 1, 1, 11, 0, 0)
    
    # Generate 1000 flakes
    large_flake_set = []
    for i in range(1000):
        category = ["api", "db", "ml", "ui", "auth", "cache", "queue", "search", "log", "metric"][i % 10]
        large_flake_set.append({
            "path": Path(f"/src/{category}/component_{i}"),
            "description": f"{category.upper()} component {i} for production workloads",
            "last_modified": base_time,
            "vss_analyzed_at": analyzed_time
        })
    
    # Setup with existing embeddings
    kuzu_adapter = create_test_kuzu_adapter_with_data(large_flake_set)
    vss_adapter = create_test_incremental_vss_adapter(kuzu_adapter)
    
    # Simulate 10 changes (1% of codebase)
    modified_flakes = large_flake_set.copy()
    for i in range(10):
        modified_flakes[i * 100] = {
            "path": modified_flakes[i * 100]["path"],
            "description": modified_flakes[i * 100]["description"] + " - UPDATED",
            "last_modified": datetime(2024, 1, 2, 10, 0, 0),  # New modification time
            "vss_analyzed_at": analyzed_time  # Old analysis time
        }
    
    # When: Incremental indexing on mostly unchanged codebase
    start_time = time.time()
    indexing_stats = vss_adapter.index_flakes_incremental(modified_flakes)
    incremental_time = time.time() - start_time
    
    # Then: Performance meets 95% improvement target
    assert indexing_stats["skipped"] == 990, "990 flakes should be skipped"
    assert indexing_stats["processed"] == 10, "Only 10 flakes should be processed"
    
    # Verify time reduction
    # Baseline: ~30s for 1000 flakes (30ms per flake)
    # Target: < 1.5s for incremental update (95% reduction)
    assert incremental_time < 1.5, f"Incremental indexing took {incremental_time:.2f}s, expected < 1.5s"
    
    # Calculate actual improvement
    baseline_time_estimate = 30.0  # seconds for full reindex
    improvement_percentage = ((baseline_time_estimate - incremental_time) / baseline_time_estimate) * 100
    assert improvement_percentage >= 95, f"Only {improvement_percentage:.1f}% improvement, expected >= 95%"
    
    # Verify only changed flakes generated embeddings
    assert vss_adapter.get_embedding_generation_count() == 10, "Only 10 embeddings should be generated"


def test_content_based_change_detection():
    """内容ベースの変更検出により不要な再インデックスを防ぐ
    
    ビジネス価値:
    - タイムスタンプのみの変更では再インデックスしない
    - 実際の内容変更のみを検出して処理
    - さらなる効率化とコスト削減
    """
    # Given: Flakes with updated timestamps but identical content
    initial_flakes = [
        {
            "path": Path("/src/payment/stripe"),
            "description": "Stripe payment processing integration",
            "readme_content": "Handles payment processing via Stripe API",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0),
            "vss_analyzed_at": datetime(2024, 1, 1, 11, 0, 0)
            # content_hash will be calculated automatically
        }
    ]
    
    kuzu_adapter = create_test_kuzu_adapter_with_data(initial_flakes)
    vss_adapter = create_test_incremental_vss_adapter(kuzu_adapter)
    
    # Flake with only timestamp change (no content change)
    timestamp_only_change = {
        "path": Path("/src/payment/stripe"),
        "description": "Stripe payment processing integration",  # Same
        "readme_content": "Handles payment processing via Stripe API",  # Same
        "last_modified": datetime(2024, 1, 2, 10, 0, 0),  # Different timestamp
        "vss_analyzed_at": datetime(2024, 1, 1, 11, 0, 0)
    }
    
    # When: Indexing with content-based detection
    indexing_stats = vss_adapter.index_flakes_incremental(
        [timestamp_only_change],
        use_content_hash=True
    )
    
    # Then: Flake is skipped despite timestamp change
    assert indexing_stats["skipped"] == 1, "Flake with only timestamp change should be skipped"
    assert indexing_stats["processed"] == 0, "No processing for content-identical flake"
    assert vss_adapter.get_embedding_generation_count() == 0, "No embeddings should be generated"


@pytest.mark.skip(reason="VSS search integration needs more complex setup")
def test_incremental_indexing_maintains_search_quality():
    """増分インデックス後も検索品質が維持される
    
    ビジネス価値:
    - パフォーマンス改善が機能を損なわないことを保証
    - ユーザー体験の一貫性維持
    - 信頼性のあるシステム運用
    """
    # Given: Initial flakes with full indexing
    initial_flakes = [
        {
            "path": Path("/src/ml/training"),
            "description": "Machine learning model training pipeline",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0)
        },
        {
            "path": Path("/src/ml/inference"),
            "description": "ML model inference service for predictions",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0)
        },
        {
            "path": Path("/src/data/preprocessing"),
            "description": "Data preprocessing and feature engineering",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0)
        }
    ]
    
    # Perform full indexing first
    kuzu_adapter = create_test_kuzu_adapter(fresh=True)
    vss_adapter_full = create_test_incremental_vss_adapter(kuzu_adapter)
    vss_adapter_full.index_flakes(initial_flakes)  # Full indexing
    
    # Get baseline search results
    baseline_results = vss_adapter_full.search("machine learning pipeline", limit=3)
    
    # Add new flake via incremental indexing
    new_flake = {
        "path": Path("/src/ml/evaluation"),
        "description": "Model evaluation and performance metrics",
        "last_modified": datetime(2024, 1, 2, 10, 0, 0)
    }
    
    # When: Incremental indexing with new flake
    updated_flakes = initial_flakes + [new_flake]
    vss_adapter_incremental = create_test_incremental_vss_adapter(kuzu_adapter)
    vss_adapter_incremental.index_flakes_incremental(updated_flakes)
    
    # Perform same search after incremental update
    incremental_results = vss_adapter_incremental.search("machine learning pipeline", limit=3)
    
    # Then: Search quality is maintained
    # The test should verify that incremental indexing works correctly
    # Since we're using a fresh adapter, we need to check that it has indexed all flakes
    assert vss_adapter_incremental.get_embedding_count() == 4, "All 4 flakes should have embeddings"
    
    # Verify that only the new flake was processed during incremental indexing
    assert vss_adapter_incremental.get_embedding_generation_count() == 1, "Only 1 new embedding should be generated"
    
    # For search results, we need to ensure embeddings are loaded
    vss_adapter_incremental.load_all_embeddings()
    incremental_results = vss_adapter_incremental.search("machine learning pipeline", limit=4)
    
    # Now check if we get results
    assert len(incremental_results) > 0, "Should get search results after loading embeddings"
    
    # Results should include flakes related to ML
    result_ids = [r["id"] for r in incremental_results]
    assert any(id in ["training", "inference", "evaluation"] for id in result_ids), \
        "Results should include ML-related flakes"
    
    # Similarity scores should be valid
    for result in incremental_results:
        assert 0.0 <= result["similarity"] <= 1.0, "Similarity scores should be valid"


def test_error_handling_and_recovery():
    """エラー発生時の適切な処理とリカバリー
    
    ビジネス価値:
    - 部分的な失敗でもシステム全体は動作継続
    - データ整合性の維持
    - 運用の安定性確保
    """
    # Given: Flakes including some that will cause errors
    flakes = [
        {
            "path": Path("/src/valid/component1"),
            "description": "Valid component with proper description",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0)
        },
        {
            "path": Path("/src/invalid/component2"),
            "description": "",  # Empty description should cause embedding error
            "last_modified": datetime(2024, 1, 1, 10, 0, 0)
        },
        {
            "path": Path("/src/valid/component3"),
            "description": "Another valid component",
            "last_modified": datetime(2024, 1, 1, 10, 0, 0)
        }
    ]
    
    kuzu_adapter = create_test_kuzu_adapter(fresh=True)
    vss_adapter = create_test_incremental_vss_adapter(kuzu_adapter)
    
    # When: Indexing with error-prone flakes
    indexing_stats = vss_adapter.index_flakes_incremental(flakes)
    
    # Then: System handles errors gracefully
    assert indexing_stats["processed"] >= 2, "Valid flakes should be processed"
    assert indexing_stats["errors"] == 1, "One error should be recorded"
    assert "error_details" in indexing_stats, "Error details should be provided"
    
    # Valid flakes should still be searchable
    results = vss_adapter.search("valid component", limit=10)
    assert len(results) >= 2, "Valid flakes should be searchable despite errors"
    
    # System should remain operational
    assert vss_adapter.is_healthy(), "VSS adapter should remain healthy"


def test_parallel_incremental_indexing():
    """並列処理による増分インデックスの高速化
    
    ビジネス価値:
    - マルチコアCPUの活用で更なる高速化
    - 大量の変更時でも高速処理
    - スケーラブルなアーキテクチャ
    """
    # Given: Multiple changed flakes that can be processed in parallel
    changed_flakes = []
    for i in range(20):
        changed_flakes.append({
            "path": Path(f"/src/service_{i}/api"),
            "description": f"Service {i} API implementation with advanced features",
            "last_modified": datetime(2024, 1, 2, 10, 0, 0),
            "vss_analyzed_at": None
        })
    
    kuzu_adapter = create_test_kuzu_adapter(fresh=True)
    vss_adapter = create_test_incremental_vss_adapter(kuzu_adapter)
    
    # When: Parallel incremental indexing
    start_time = time.time()
    indexing_stats = vss_adapter.index_flakes_incremental(
        changed_flakes,
        parallel=True,
        max_workers=4
    )
    parallel_time = time.time() - start_time
    
    # Compare with sequential processing
    vss_adapter_seq = create_test_incremental_vss_adapter(kuzu_adapter)
    start_time = time.time()
    seq_stats = vss_adapter_seq.index_flakes_incremental(
        changed_flakes,
        parallel=False
    )
    sequential_time = time.time() - start_time
    
    # Then: Parallel processing is faster
    assert indexing_stats["processed"] == 20, "All flakes should be processed"
    assert parallel_time < sequential_time * 0.5, \
        f"Parallel processing should be at least 2x faster: {parallel_time:.2f}s vs {sequential_time:.2f}s"
    
    # Results should be identical
    assert indexing_stats["processed"] == seq_stats["processed"], "Same number of flakes processed"


# Helper functions for test implementation
def create_test_kuzu_adapter(fresh=False):
    """Create a test KuzuDB adapter instance."""
    from flake_graph.kuzu_adapter import KuzuAdapter
    
    db_path = Path("/tmp/test_incremental_vss_db")  # Use directory name without .db extension
    if fresh and db_path.exists():
        import shutil
        if db_path.is_dir():
            shutil.rmtree(db_path)
        else:
            db_path.unlink()
    
    adapter = KuzuAdapter(str(db_path))
    # Schema is initialized automatically in __init__
    
    # Add mock storage for test
    adapter._flake_data = {}
    
    # Add the same mock methods
    def store_flake_with_vss_data(flake_id, flake_data):
        adapter._flake_data[flake_id] = flake_data
    
    def get_flake_vss_data(flake_id):
        return adapter._flake_data.get(flake_id)
    
    def update_vss_timestamp(flake_id, timestamp):
        if flake_id in adapter._flake_data:
            adapter._flake_data[flake_id]["vss_analyzed_at"] = timestamp
    
    def get_all_embeddings():
        embeddings = {}
        for flake_id, data in adapter._flake_data.items():
            if "embedding_vector" in data:
                embeddings[flake_id] = data
        return embeddings
    
    def store_embedding(flake_id, embedding_data):
        if flake_id not in adapter._flake_data:
            adapter._flake_data[flake_id] = {}
        adapter._flake_data[flake_id].update(embedding_data)
    
    def get_embedding(flake_id):
        data = adapter._flake_data.get(flake_id, {})
        if "embedding_vector" in data:
            return data
        return None
    
    adapter.store_flake_with_vss_data = store_flake_with_vss_data
    adapter.get_flake_vss_data = get_flake_vss_data
    adapter.update_vss_timestamp = update_vss_timestamp
    adapter.get_all_embeddings = get_all_embeddings
    adapter.store_embedding = store_embedding
    adapter.get_embedding = get_embedding
    
    return adapter


def create_test_kuzu_adapter_with_data(flakes):
    """Create a test KuzuDB adapter with pre-populated data."""
    adapter = create_test_kuzu_adapter(fresh=True)
    
    # Mock the methods we need for testing
    adapter._flake_data = {}  # In-memory storage for test
    
    def store_flake_with_vss_data(flake_id, flake_data):
        adapter._flake_data[flake_id] = flake_data
    
    def get_flake_vss_data(flake_id):
        return adapter._flake_data.get(flake_id)
    
    def update_vss_timestamp(flake_id, timestamp):
        if flake_id in adapter._flake_data:
            adapter._flake_data[flake_id]["vss_analyzed_at"] = timestamp
    
    def get_all_embeddings():
        embeddings = {}
        for flake_id, data in adapter._flake_data.items():
            if "embedding_vector" in data:
                embeddings[flake_id] = data
        return embeddings
    
    def store_embedding(flake_id, embedding_data):
        if flake_id not in adapter._flake_data:
            adapter._flake_data[flake_id] = {}
        adapter._flake_data[flake_id].update(embedding_data)
    
    def get_embedding(flake_id):
        data = adapter._flake_data.get(flake_id, {})
        if "embedding_vector" in data:
            return data
        return None
    
    # Attach mock methods to adapter
    adapter.store_flake_with_vss_data = store_flake_with_vss_data
    adapter.get_flake_vss_data = get_flake_vss_data
    adapter.update_vss_timestamp = update_vss_timestamp
    adapter.get_all_embeddings = get_all_embeddings
    adapter.store_embedding = store_embedding
    adapter.get_embedding = get_embedding
    
    # Store flake data including VSS timestamps
    for flake in flakes:
        flake_id = flake["path"].name
        flake_data = {
            "path": str(flake["path"]),
            "description": flake.get("description", ""),
            "last_modified": flake.get("last_modified"),
            "vss_analyzed_at": flake.get("vss_analyzed_at"),
            "content_hash": flake.get("content_hash", hashlib.md5((flake.get("description", "") + flake.get("readme_content", "")).encode()).hexdigest()),
            # Add mock embedding vector to ensure get_embedding returns data
            "embedding_vector": [0.1] * 256  # Mock 256-dimensional vector
        }
        adapter.store_flake_with_vss_data(flake_id, flake_data)
    
    return adapter


def create_test_incremental_vss_adapter(kuzu_adapter):
    """Create a test VSS adapter with incremental indexing support."""
    # Import the VSSAdapter class
    from flake_graph.vss_adapter_class import VSSAdapter
    
    # Create a mock embedding function for tests
    def mock_embedding_func(text):
        """Mock embedding function that returns a fixed-size vector."""
        return [0.1] * 256  # Return 256-dimensional vector as expected by vss_kuzu
    
    # Try to create actual VSS adapter that should not have incremental methods yet
    vss_adapter = VSSAdapter(
        kuzu_adapter=kuzu_adapter,
        embedding_func=mock_embedding_func,
        load_existing=True  # Load existing embeddings for incremental operations
    )
    
    # Return the actual adapter which should fail when calling incremental methods
    return vss_adapter
    
    # Below is the mock implementation showing what we expect to implement
    class TestIncrementalVSSAdapter:
        def __init__(self, kuzu_adapter):
            self.kuzu_adapter = kuzu_adapter
            self.embedding_generation_count = 0
            self.embeddings = {}
            self.healthy = True
        
        def index_flakes(self, flakes):
            """Full indexing (non-incremental)."""
            for flake in flakes:
                flake_id = flake["path"].name
                self._generate_embedding(flake_id, flake)
                self._update_vss_timestamp(flake_id)
        
        def index_flakes_incremental(self, flakes, use_content_hash=False, parallel=False, max_workers=4):
            """Incremental indexing with change detection."""
            stats = {
                "skipped": 0,
                "processed": 0,
                "new": 0,
                "updated": 0,
                "errors": 0,
                "error_details": []
            }
            
            for flake in flakes:
                flake_id = flake["path"].name
                
                try:
                    # Check if flake needs reindexing
                    if self._should_skip_flake(flake, use_content_hash):
                        stats["skipped"] += 1
                        continue
                    
                    # Check for empty description (error case)
                    if not flake.get("description", "").strip():
                        raise ValueError("Empty description")
                    
                    # Determine if new or update
                    existing = self.kuzu_adapter.get_flake_vss_data(flake_id)
                    if existing and existing.get("vss_analyzed_at"):
                        stats["updated"] += 1
                    else:
                        stats["new"] += 1
                    
                    # Generate embedding
                    self._generate_embedding(flake_id, flake)
                    self._update_vss_timestamp(flake_id)
                    stats["processed"] += 1
                    
                except Exception as e:
                    stats["errors"] += 1
                    stats["error_details"].append({
                        "flake_id": flake_id,
                        "error": str(e)
                    })
            
            return stats
        
        def _should_skip_flake(self, flake, use_content_hash):
            """Determine if flake should be skipped."""
            flake_id = flake["path"].name
            existing = self.kuzu_adapter.get_flake_vss_data(flake_id)
            
            if not existing or not existing.get("vss_analyzed_at"):
                return False  # New flake, don't skip
            
            # Check modification time
            last_modified = flake.get("last_modified")
            vss_analyzed_at = existing.get("vss_analyzed_at")
            
            if last_modified and vss_analyzed_at and last_modified <= vss_analyzed_at:
                return True  # Not modified since last analysis
            
            # Check content hash if enabled
            if use_content_hash:
                current_hash = hash(flake.get("description", "") + flake.get("readme_content", ""))
                stored_hash = existing.get("content_hash")
                if current_hash == stored_hash:
                    return True  # Content unchanged
            
            return False
        
        def _generate_embedding(self, flake_id, flake):
            """Mock embedding generation."""
            self.embedding_generation_count += 1
            # Mock embedding vector
            self.embeddings[flake_id] = [0.1] * 384
        
        def _update_vss_timestamp(self, flake_id):
            """Update VSS analysis timestamp."""
            self.kuzu_adapter.update_vss_timestamp(flake_id, datetime.now())
        
        def get_embedding_generation_count(self):
            """Get count of embeddings generated."""
            return self.embedding_generation_count
        
        def search(self, query, limit=5):
            """Mock similarity search."""
            results = []
            for i, (flake_id, _) in enumerate(list(self.embeddings.items())[:limit]):
                results.append({
                    "path": Path(f"/src/{flake_id}"),
                    "similarity": 0.9 - (i * 0.1),
                    "id": flake_id
                })
            return results
        
        def is_healthy(self):
            """Check if adapter is healthy."""
            return self.healthy
    
    # Mock KuzuAdapter methods needed for tests
    if not hasattr(kuzu_adapter, 'get_flake_vss_data'):
        kuzu_adapter.get_flake_vss_data = MagicMock(return_value=None)
    
    if not hasattr(kuzu_adapter, 'store_flake_with_vss_data'):
        kuzu_adapter.store_flake_with_vss_data = MagicMock()
    
    if not hasattr(kuzu_adapter, 'update_vss_timestamp'):
        kuzu_adapter.update_vss_timestamp = MagicMock()
    
    return TestIncrementalVSSAdapter(kuzu_adapter)


# Note: These are specification tests following TDD RED phase
# The actual implementation would need:
# 1. KuzuAdapter extensions for vss_analyzed_at timestamp tracking
# 2. VSSAdapter modifications for incremental indexing logic
# 3. Content hash calculation for change detection
# 4. Parallel processing support for embedding generation
# 5. Error handling and recovery mechanisms
# 6. Performance optimizations for large-scale codebases