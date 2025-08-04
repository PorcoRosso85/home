"""Specification tests for VSS embedding persistence in KuzuDB.

This module tests the BEHAVIOR and BUSINESS VALUE of persisting VSS embeddings.
It verifies that the system meets the business requirement:
"90% startup time reduction by eliminating embedding regeneration"

Business Context:
- Current: Every startup regenerates all embeddings (30-60 seconds for large codebases)
- Target: Load pre-computed embeddings from KuzuDB (< 3 seconds)
- Impact: Faster developer feedback loop, reduced CI/CD times

Technical Requirements:
- Embeddings must be stored in KuzuDB alongside flake metadata
- System must detect when embeddings are already computed
- Loaded embeddings must produce identical search results
- Incremental updates for new/modified flakes only
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest
import time
from datetime import datetime


def test_embeddings_persist_to_kuzu_on_first_scan():
    """初回スキャン時にVSSエンベディングがKuzuDBに永続化される
    
    ビジネス価値:
    - 次回起動時の高速化を可能にする基盤
    - CI/CDパイプラインでの再利用可能性
    - 分散チーム間でのエンベディング共有
    """
    # Given: Fresh database with no existing embeddings
    kuzu_adapter = create_test_kuzu_adapter(fresh=True)
    vss_adapter = create_test_vss_adapter(kuzu_adapter)
    
    test_flakes = [
        {
            "path": Path("/src/search/vss"),
            "description": "Vector similarity search implementation",
            "readme_content": "VSS using sentence transformers for semantic search"
        },
        {
            "path": Path("/src/persistence/kuzu"),
            "description": "KuzuDB graph database adapter",
            "readme_content": "High-performance embedded graph database integration"
        },
        {
            "path": Path("/src/telemetry/logging"),
            "description": "Structured logging with OpenTelemetry",
            "readme_content": "Distributed tracing and log aggregation"
        }
    ]
    
    # When: System processes flakes and generates embeddings
    start_time = time.time()
    vss_adapter.index_flakes(test_flakes)
    embedding_time = time.time() - start_time
    
    # Then: Embeddings are persisted to KuzuDB
    persisted_embeddings = kuzu_adapter.get_all_embeddings()
    assert len(persisted_embeddings) == 3, "All flake embeddings should be persisted"
    
    for flake in test_flakes:
        flake_id = str(flake["path"].parent.name)
        embedding_data = kuzu_adapter.get_embedding(flake_id)
        
        assert embedding_data is not None, f"Embedding for {flake_id} should exist"
        assert "embedding_vector" in embedding_data, "Should store embedding vector"
        assert "embedding_model" in embedding_data, "Should store model version for compatibility"
        assert "created_at" in embedding_data, "Should store creation timestamp"
        assert len(embedding_data["embedding_vector"]) > 0, "Embedding should not be empty"
    
    # Performance baseline for comparison
    assert embedding_time > 0.1, "Initial embedding generation should take measurable time"
    pytest.skip(f"Initial embedding time: {embedding_time:.2f}s (baseline for persistence tests)")


def test_embeddings_load_from_kuzu_on_restart():
    """再起動時にKuzuDBから既存エンベディングが高速ロードされる
    
    ビジネス価値:
    - 90%以上の起動時間短縮
    - 開発者の待ち時間削減 → 生産性向上
    - CI/CDパイプラインの高速化
    """
    # Given: Existing database with pre-computed embeddings
    kuzu_adapter = create_test_kuzu_adapter(with_test_data=True)
    
    # Simulate embeddings already in database
    test_embeddings = [
        {
            "flake_id": "vss",
            "embedding_vector": [0.1, 0.2, 0.3] * 128,  # Mock 384-dim embedding
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "created_at": datetime.now().isoformat()
        },
        {
            "flake_id": "kuzu", 
            "embedding_vector": [0.2, 0.3, 0.4] * 128,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "created_at": datetime.now().isoformat()
        },
        {
            "flake_id": "logging",
            "embedding_vector": [0.3, 0.4, 0.5] * 128,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "created_at": datetime.now().isoformat()
        }
    ]
    
    for emb in test_embeddings:
        kuzu_adapter.store_embedding(emb["flake_id"], emb)
    
    # When: New VSS adapter instance loads embeddings on startup
    start_time = time.time()
    vss_adapter = create_test_vss_adapter(kuzu_adapter, load_existing=True)
    load_time = time.time() - start_time
    
    # Then: Embeddings are loaded from KuzuDB without regeneration
    assert vss_adapter.has_cached_embeddings(), "Should detect cached embeddings"
    assert vss_adapter.get_embedding_count() == 3, "All embeddings should be loaded"
    
    # Verify 90% performance improvement
    # Assuming baseline embedding generation takes ~1s for 3 flakes
    expected_max_load_time = 0.1  # 100ms target for loading from DB
    assert load_time < expected_max_load_time, \
        f"Loading should be < {expected_max_load_time}s, got {load_time:.3f}s"
    
    # Verify loaded embeddings are functional
    loaded_vectors = vss_adapter.get_all_embedding_vectors()
    assert len(loaded_vectors) == 3, "All vectors should be accessible"
    
    for flake_id, vector in loaded_vectors.items():
        assert len(vector) == 384, "Embedding dimension should be preserved"
        assert all(isinstance(v, float) for v in vector), "Vector values should be floats"


def test_loaded_embeddings_produce_identical_search_results():
    """ロードされたエンベディングが同一の検索結果を生成する
    
    ビジネス価値:
    - 永続化による機能的な劣化がないことを保証
    - ユーザー体験の一貫性維持
    - デバッグ・テストの再現性確保
    """
    # Given: Two VSS instances - one fresh, one with loaded embeddings
    kuzu_adapter1 = create_test_kuzu_adapter(fresh=True)
    kuzu_adapter2 = create_test_kuzu_adapter(fresh=True)
    
    test_flakes = [
        {
            "path": Path("/src/search/vss"),
            "description": "Vector similarity search using ML embeddings"
        },
        {
            "path": Path("/src/search/fts"),
            "description": "Full-text search with inverted index"
        },
        {
            "path": Path("/src/ml/embeddings"),
            "description": "Machine learning embedding generation service"
        },
        {
            "path": Path("/src/db/postgres"),
            "description": "PostgreSQL database adapter and connection pool"
        }
    ]
    
    # Create embeddings with first instance
    vss_fresh = create_test_vss_adapter(kuzu_adapter1)
    vss_fresh.index_flakes(test_flakes)
    
    # Persist embeddings to second database
    embeddings = kuzu_adapter1.get_all_embeddings()
    for emb_id, emb_data in embeddings.items():
        kuzu_adapter2.store_embedding(emb_id, emb_data)
    
    # When: Second instance loads embeddings and performs searches
    vss_loaded = create_test_vss_adapter(kuzu_adapter2, load_existing=True)
    
    test_queries = [
        "vector search implementation",
        "database connection management", 
        "machine learning models",
        "text indexing and retrieval"
    ]
    
    # Then: Both instances produce identical results
    for query in test_queries:
        results_fresh = vss_fresh.search(query, limit=3)
        results_loaded = vss_loaded.search(query, limit=3)
        
        assert len(results_fresh) == len(results_loaded), \
            f"Result count mismatch for '{query}'"
        
        # Verify same flakes in same order
        for i, (fresh_result, loaded_result) in enumerate(zip(results_fresh, results_loaded)):
            assert fresh_result["id"] == loaded_result["id"], \
                f"Result {i} ID mismatch for '{query}'"
            
            # Similarity scores should be identical (or very close due to float precision)
            assert abs(fresh_result["similarity"] - loaded_result["similarity"]) < 0.0001, \
                f"Similarity score mismatch for '{query}' result {i}"


def test_incremental_embedding_updates_for_new_flakes():
    """新規・変更されたflakeのみエンベディングを再計算する
    
    ビジネス価値:
    - 大規模コードベースでの効率的な更新
    - 変更の影響を最小限に抑制
    - CI/CDでの差分ビルド時間短縮
    """
    # Given: Existing embeddings in database
    kuzu_adapter = create_test_kuzu_adapter(with_test_data=True)
    
    # Initial flakes with embeddings
    existing_flakes = [
        {
            "path": Path("/src/api/rest"),
            "description": "RESTful API server implementation",
            "last_modified": datetime(2024, 1, 1).isoformat()
        },
        {
            "path": Path("/src/api/graphql"),
            "description": "GraphQL API with schema federation",
            "last_modified": datetime(2024, 1, 1).isoformat()
        }
    ]
    
    # Store initial embeddings
    for i, flake in enumerate(existing_flakes):
        flake_id = flake["path"].name
        kuzu_adapter.store_embedding(flake_id, {
            "embedding_vector": [0.1 * i] * 384,
            "created_at": flake["last_modified"],
            "content_hash": hash(flake["description"])
        })
    
    # New and modified flakes
    updated_flakes = [
        # Unchanged flake
        existing_flakes[0],
        # Modified flake (description changed)
        {
            "path": Path("/src/api/graphql"),
            "description": "GraphQL API with schema federation and subscriptions",
            "last_modified": datetime(2024, 2, 1).isoformat()
        },
        # New flake
        {
            "path": Path("/src/api/grpc"),
            "description": "gRPC service with protocol buffers",
            "last_modified": datetime(2024, 2, 1).isoformat()
        }
    ]
    
    # When: System processes the updated flake list
    vss_adapter = create_test_vss_adapter(kuzu_adapter, load_existing=True)
    
    start_time = time.time()
    update_stats = vss_adapter.update_embeddings(updated_flakes)
    update_time = time.time() - start_time
    
    # Then: Only new/modified flakes are processed
    assert update_stats["unchanged"] == 1, "One flake should be unchanged"
    assert update_stats["updated"] == 1, "One flake should be updated"
    assert update_stats["new"] == 1, "One flake should be new"
    assert update_stats["total_processed"] == 2, "Only 2 flakes should be processed"
    
    # Performance: Incremental update should be faster than full regeneration
    # Assuming ~0.3s per embedding, 2 embeddings should take < 1s
    assert update_time < 1.0, f"Incremental update took {update_time:.2f}s, expected < 1s"
    
    # Verify embedding states
    rest_embedding = kuzu_adapter.get_embedding("rest")
    assert rest_embedding["created_at"] == existing_flakes[0]["last_modified"], \
        "Unchanged flake should keep original embedding"
    
    graphql_embedding = kuzu_adapter.get_embedding("graphql")
    assert graphql_embedding["created_at"] == updated_flakes[1]["last_modified"], \
        "Modified flake should have new embedding"
    
    grpc_embedding = kuzu_adapter.get_embedding("grpc")
    assert grpc_embedding is not None, "New flake should have embedding"
    assert grpc_embedding["created_at"] == updated_flakes[2]["last_modified"]


def test_embedding_model_version_compatibility():
    """異なるモデルバージョンのエンベディングを適切に処理する
    
    ビジネス価値:
    - モデル更新時の後方互換性確保
    - 段階的なモデル移行を可能に
    - システムの長期的な保守性向上
    """
    # Given: Embeddings from different model versions
    kuzu_adapter = create_test_kuzu_adapter(fresh=True)
    
    embeddings_v1 = [
        {
            "flake_id": "auth",
            "embedding_vector": [0.1] * 384,  # v1 model: 384 dimensions
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "model_version": "1.0.0",
            "created_at": datetime(2024, 1, 1).isoformat()
        }
    ]
    
    embeddings_v2 = [
        {
            "flake_id": "payment",
            "embedding_vector": [0.2] * 768,  # v2 model: 768 dimensions
            "embedding_model": "sentence-transformers/all-mpnet-base-v2",
            "model_version": "2.0.0",
            "created_at": datetime(2024, 6, 1).isoformat()
        }
    ]
    
    for emb in embeddings_v1 + embeddings_v2:
        kuzu_adapter.store_embedding(emb["flake_id"], emb)
    
    # When: System loads mixed-version embeddings
    vss_adapter = create_test_vss_adapter(
        kuzu_adapter, 
        load_existing=True,
        current_model_version="2.0.0"
    )
    
    compatibility_report = vss_adapter.check_embedding_compatibility()
    
    # Then: System handles version differences appropriately
    assert compatibility_report["total_embeddings"] == 2
    assert compatibility_report["current_version_count"] == 1
    assert compatibility_report["outdated_version_count"] == 1
    assert "auth" in compatibility_report["outdated_embeddings"]
    
    # System should flag outdated embeddings for regeneration
    regeneration_needed = vss_adapter.get_embeddings_needing_update()
    assert len(regeneration_needed) == 1
    assert regeneration_needed[0]["flake_id"] == "auth"
    assert regeneration_needed[0]["reason"] == "model_version_mismatch"
    
    # Search should still work with mixed versions (with warning)
    results = vss_adapter.search("authentication", limit=2)
    assert len(results) > 0, "Search should work despite version mismatch"
    
    # But results should include compatibility warning
    assert any(r.get("compatibility_warning") for r in results if r["id"] == "auth"), \
        "Outdated embeddings should have compatibility warning"


def test_embedding_persistence_handles_large_codebases():
    """大規模コードベース（1000+ flakes）での永続化性能を検証
    
    ビジネス価値:
    - エンタープライズ規模のプロジェクトでの実用性
    - スケーラビリティの保証
    - 性能劣化の早期発見
    """
    # Given: Large number of flakes simulating real codebase
    kuzu_adapter = create_test_kuzu_adapter(fresh=True)
    
    # Generate 1000 test flakes across different categories
    large_flake_set = []
    categories = ["api", "db", "ml", "ui", "auth", "payment", "search", "cache", "queue", "monitor"]
    
    for i in range(1000):
        category = categories[i % len(categories)]
        large_flake_set.append({
            "path": Path(f"/src/{category}/component_{i}"),
            "description": f"{category.upper()} component {i} - handles {category}-related operations",
            "readme_content": f"Detailed implementation of {category} functionality with advanced features"
        })
    
    # When: System processes and persists large dataset
    vss_adapter = create_test_vss_adapter(kuzu_adapter)
    
    start_time = time.time()
    vss_adapter.index_flakes(large_flake_set)
    initial_index_time = time.time() - start_time
    
    # Simulate restart and load
    vss_adapter_reloaded = create_test_vss_adapter(kuzu_adapter, load_existing=True)
    
    start_time = time.time()
    vss_adapter_reloaded.load_all_embeddings()
    reload_time = time.time() - start_time
    
    # Then: Performance meets requirements
    # Initial indexing: ~30-60s is acceptable for 1000 flakes
    assert initial_index_time < 60, f"Initial indexing took {initial_index_time:.1f}s, expected < 60s"
    
    # Reload target: < 3s for 90% improvement (from ~30s baseline)
    assert reload_time < 3, f"Reload took {reload_time:.1f}s, expected < 3s"
    
    # Calculate actual improvement
    improvement_percentage = ((initial_index_time - reload_time) / initial_index_time) * 100
    assert improvement_percentage >= 90, \
        f"Only {improvement_percentage:.1f}% improvement, expected >= 90%"
    
    # Verify all embeddings loaded correctly
    assert vss_adapter_reloaded.get_embedding_count() == 1000, "All embeddings should be loaded"
    
    # Test search performance with loaded embeddings
    search_queries = [
        "database connection pooling",
        "machine learning inference", 
        "API rate limiting",
        "user authentication OAuth"
    ]
    
    for query in search_queries:
        start_time = time.time()
        results = vss_adapter_reloaded.search(query, limit=10)
        search_time = time.time() - start_time
        
        assert search_time < 0.1, f"Search '{query}' took {search_time:.3f}s, expected < 0.1s"
        assert len(results) == 10, "Should return requested number of results"


def test_embedding_storage_space_efficiency():
    """エンベディングストレージの空間効率性を検証
    
    ビジネス価値:
    - ストレージコストの最適化
    - ネットワーク転送時間の短縮
    - バックアップ・復元の高速化
    """
    # Skip this test as it requires actual implementation
    pytest.skip("Embedding compression and storage optimization not yet implemented")
    
    # Given: Embeddings with various optimization strategies
    kuzu_adapter = create_test_kuzu_adapter(fresh=True)
    
    # Test embedding data
    test_embedding = {
        "flake_id": "test_flake",
        "embedding_vector": [0.123456789] * 384,  # High precision floats
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "created_at": datetime.now().isoformat()
    }
    
    # When: Store with different compression strategies
    strategies = {
        "raw": kuzu_adapter.store_embedding_raw,
        "quantized": kuzu_adapter.store_embedding_quantized,  # int8 quantization
        "compressed": kuzu_adapter.store_embedding_compressed  # zstd compression
    }
    
    storage_sizes = {}
    for strategy_name, store_func in strategies.items():
        store_func("test_flake", test_embedding)
        storage_sizes[strategy_name] = kuzu_adapter.get_storage_size("test_flake")
    
    # Then: Compression provides significant space savings
    raw_size = storage_sizes["raw"]
    
    # Quantization should reduce size by ~75% (float32 -> int8)
    quantized_savings = (1 - storage_sizes["quantized"] / raw_size) * 100
    assert quantized_savings > 70, f"Quantization saved only {quantized_savings:.1f}%"
    
    # Compression should provide additional savings
    compressed_savings = (1 - storage_sizes["compressed"] / raw_size) * 100
    assert compressed_savings > 50, f"Compression saved only {compressed_savings:.1f}%"
    
    # Verify search quality is maintained
    for strategy_name in strategies:
        results = vss_adapter.search_with_strategy("test query", strategy=strategy_name)
        assert len(results) > 0, f"Search with {strategy_name} strategy should work"


# Helper functions for test implementation
def create_test_kuzu_adapter(fresh=False, with_test_data=False):
    """Create a test KuzuDB adapter instance."""
    from flake_graph.kuzu_adapter import KuzuAdapter
    
    if fresh:
        db_path = Path("/tmp/test_vss_persistence.db")
        if db_path.exists():
            import shutil
            shutil.rmtree(db_path)
    else:
        db_path = Path("/tmp/test_vss_persistence_existing.db")
    
    adapter = KuzuAdapter(str(db_path))
    
    if with_test_data:
        # Add some test data if requested
        adapter.init_schema()
    
    return adapter


def create_test_vss_adapter(kuzu_adapter, load_existing=False, current_model_version="1.0.0"):
    """Create a test VSS adapter instance."""
    from flake_graph.vss_adapter import VSSAdapter
    
    # Use actual VSSAdapter implementation
    return VSSAdapter(
        kuzu_adapter=kuzu_adapter,
        vss_db_path="/tmp/test_vss.kuzu",
        model_version=current_model_version,
        load_existing=load_existing
    )
    
    # Note: The mock TestVSSAdapter below is kept for reference but not used
    class TestVSSAdapter:
        def __init__(self, kuzu_adapter, load_existing=False, model_version="1.0.0"):
            self.kuzu_adapter = kuzu_adapter
            self.embeddings = {}
            self.model_version = model_version
            
            if load_existing:
                self.load_all_embeddings()
        
        def index_flakes(self, flakes):
            """Generate and store embeddings for flakes."""
            for flake in flakes:
                flake_id = flake["path"].name
                # Mock embedding generation
                embedding_vector = self._generate_mock_embedding(flake["description"])
                
                embedding_data = {
                    "embedding_vector": embedding_vector,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "model_version": self.model_version,
                    "created_at": datetime.now().isoformat(),
                    "content_hash": hash(flake.get("description", "") + flake.get("readme_content", ""))
                }
                
                self.embeddings[flake_id] = embedding_vector
                self.kuzu_adapter.store_embedding(flake_id, embedding_data)
        
        def load_all_embeddings(self):
            """Load embeddings from KuzuDB."""
            stored_embeddings = self.kuzu_adapter.get_all_embeddings()
            for flake_id, emb_data in stored_embeddings.items():
                self.embeddings[flake_id] = emb_data["embedding_vector"]
        
        def has_cached_embeddings(self):
            """Check if embeddings are loaded."""
            return len(self.embeddings) > 0
        
        def get_embedding_count(self):
            """Get number of loaded embeddings."""
            return len(self.embeddings)
        
        def get_all_embedding_vectors(self):
            """Get all embedding vectors."""
            return self.embeddings
        
        def search(self, query, limit=5):
            """Mock similarity search."""
            # Simple mock search - return some results
            results = []
            for i, (flake_id, vector) in enumerate(list(self.embeddings.items())[:limit]):
                results.append({
                    "id": flake_id,
                    "similarity": 0.9 - (i * 0.1)  # Decreasing similarity
                })
            return results
        
        def update_embeddings(self, flakes):
            """Update only changed embeddings."""
            stats = {"unchanged": 0, "updated": 0, "new": 0, "total_processed": 0}
            
            for flake in flakes:
                flake_id = flake["path"].name
                existing = self.kuzu_adapter.get_embedding(flake_id)
                
                current_hash = hash(flake.get("description", "") + flake.get("readme_content", ""))
                
                if existing:
                    if existing.get("content_hash") == current_hash:
                        stats["unchanged"] += 1
                    else:
                        # Re-generate embedding
                        self.index_flakes([flake])
                        stats["updated"] += 1
                        stats["total_processed"] += 1
                else:
                    # New flake
                    self.index_flakes([flake])
                    stats["new"] += 1
                    stats["total_processed"] += 1
            
            return stats
        
        def check_embedding_compatibility(self):
            """Check model version compatibility."""
            all_embeddings = self.kuzu_adapter.get_all_embeddings()
            current_version_count = 0
            outdated_version_count = 0
            outdated_embeddings = []
            
            for flake_id, emb_data in all_embeddings.items():
                if emb_data.get("model_version") == self.model_version:
                    current_version_count += 1
                else:
                    outdated_version_count += 1
                    outdated_embeddings.append(flake_id)
            
            return {
                "total_embeddings": len(all_embeddings),
                "current_version_count": current_version_count,
                "outdated_version_count": outdated_version_count,
                "outdated_embeddings": outdated_embeddings
            }
        
        def get_embeddings_needing_update(self):
            """Get list of embeddings that need regeneration."""
            report = self.check_embedding_compatibility()
            needs_update = []
            
            for flake_id in report["outdated_embeddings"]:
                needs_update.append({
                    "flake_id": flake_id,
                    "reason": "model_version_mismatch"
                })
            
            return needs_update
        
        def _generate_mock_embedding(self, text):
            """Generate a mock embedding vector."""
            # Simple mock: use text length to generate different vectors
            base_value = len(text) / 1000.0
            return [base_value + (i * 0.001) for i in range(384)]
    
    return TestVSSAdapter(kuzu_adapter, load_existing, current_model_version)


# Note: These are specification tests following TDD RED phase
# The actual implementation would need:
# 1. KuzuAdapter extensions for embedding storage
# 2. VSSAdapter modifications for persistence
# 3. Schema updates in KuzuDB for embedding tables
# 4. Efficient serialization/deserialization of vectors
# 5. Model version management and migration strategies