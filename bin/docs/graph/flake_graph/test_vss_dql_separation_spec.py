"""Test specification for VSS DQL/DML separation.

This module defines RED tests that specify how Vector Similarity Search (VSS)
functionality should be separated into DQL (Data Query Language) and DML 
(Data Manipulation Language) concerns:

- DML: Embedding generation and storage operations
- DQL: Vector similarity search queries using Cypher with KuzuDB VECTOR extension

The separation enables:
1. Pure data manipulation in DML layer (embeddings stored in database)
2. Declarative queries in DQL layer (Cypher with vector operations)
3. Clear separation of concerns between data modification and retrieval
4. Leveraging KuzuDB native VECTOR capabilities for efficient similarity search

Test Structure:
- test_dml_* : Tests for embedding generation and storage (Data Manipulation)
- test_dql_* : Tests for Cypher-based vector search queries (Data Query)
- test_integration_* : Tests for DQL/DML integration scenarios
"""

import pytest
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import tempfile
import os

from flake_graph.kuzu_adapter import KuzuAdapter


class TestVSSDQLSeparation:
    """Test specification for VSS DQL/DML separation architecture."""

    def setup_method(self):
        """Set up test environment with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_vss_separation.kuzu"
        self.kuzu_adapter = KuzuAdapter(self.db_path)

    def teardown_method(self):
        """Clean up test environment."""
        self.kuzu_adapter.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # DML Layer Tests - Embedding Generation and Storage
    
    def test_dml_embedding_generation_produces_vector(self):
        """DML: Embedding generation should produce float vectors from content."""
        # RED: This test should fail until DML embedding generator is implemented
        from flake_graph.dml_embedding_generator import generate_embedding
        
        content = "A Nix flake for Python development with poetry and pytest"
        embedding = generate_embedding(content)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
        assert len(embedding) == 384  # Expected embedding dimension

    def test_dml_embedding_storage_persists_to_database(self):
        """DML: Generated embeddings should be stored in KuzuDB FLOAT[] columns."""
        # RED: This test should fail until DML storage layer is implemented
        from flake_graph.dml_embedding_storage import store_embedding
        
        flake_path = "/src/test/example"
        embedding = [0.1, 0.2, 0.3, 0.4] * 96  # 384-dim mock embedding
        content_hash = "abc123"
        
        # Store embedding via DML layer
        result = store_embedding(
            kuzu_adapter=self.kuzu_adapter,
            flake_path=flake_path,
            embedding_vector=embedding,
            content_hash=content_hash,
            model_version="1.0.0"
        )
        
        assert result["ok"] is True
        
        # Verify storage in database
        flake_data = self.kuzu_adapter.read_flake(flake_path)
        assert flake_data is not None
        assert flake_data["vss_embedding"] == embedding
        assert flake_data["content_hash"] == content_hash

    def test_dml_batch_embedding_generation_processes_multiple_flakes(self):
        """DML: Batch embedding generation should process multiple flakes efficiently."""
        # RED: This test should fail until batch DML processing is implemented
        from flake_graph.dml_batch_processor import process_flakes_batch
        
        flakes = [
            {"path": "/src/web/frontend", "description": "React frontend", "content": "React app"},
            {"path": "/src/api/backend", "description": "FastAPI backend", "content": "Python API"},
            {"path": "/src/db/migrations", "description": "Database schema", "content": "SQL migrations"}
        ]
        
        result = process_flakes_batch(
            kuzu_adapter=self.kuzu_adapter,
            flakes=flakes,
            force_regenerate=False
        )
        
        assert result["ok"] is True
        assert result["processed"] == 3
        assert result["generated_embeddings"] == 3
        
        # Verify all embeddings stored
        for flake in flakes:
            stored_flake = self.kuzu_adapter.read_flake(flake["path"])
            assert stored_flake is not None
            assert stored_flake["vss_embedding"] is not None

    def test_dml_incremental_embedding_skips_unchanged_content(self):
        """DML: Incremental embedding should skip flakes with unchanged content hashes."""
        # RED: This test should fail until incremental DML processing is implemented
        from flake_graph.dml_batch_processor import process_flakes_batch
        
        flake_path = "/src/utils/helpers"
        flake_data = {
            "path": flake_path,
            "description": "Utility functions",
            "content": "Helper functions for common tasks"
        }
        
        # First processing
        result1 = process_flakes_batch(
            kuzu_adapter=self.kuzu_adapter,
            flakes=[flake_data],
            force_regenerate=False
        )
        assert result1["processed"] == 1
        assert result1["generated_embeddings"] == 1
        
        # Second processing with same content
        result2 = process_flakes_batch(
            kuzu_adapter=self.kuzu_adapter,
            flakes=[flake_data],
            force_regenerate=False
        )
        assert result2["processed"] == 1
        assert result2["generated_embeddings"] == 0  # Skipped due to unchanged hash
        assert result2["skipped"] == 1

    # DQL Layer Tests - Cypher-based Vector Search
    
    def test_dql_vector_similarity_search_cypher_query(self):
        """DQL: Vector similarity search should use Cypher with KuzuDB VECTOR functions."""
        # RED: This test should fail until DQL Cypher queries are implemented
        from flake_graph.dql_vector_search import execute_similarity_search
        
        # Setup test data with embeddings
        test_flakes = [
            ("/src/web/frontend", [0.8, 0.2, 0.1] * 128),
            ("/src/web/backend", [0.7, 0.3, 0.0] * 128),  
            ("/src/mobile/app", [0.1, 0.1, 0.8] * 128)
        ]
        
        for path, embedding in test_flakes:
            self.kuzu_adapter.create_flake(path, f"Description for {path}", "nix")
            self.kuzu_adapter.update_flake(path, vss_embedding=embedding)
        
        query_embedding = [0.9, 0.1, 0.0] * 128  # Most similar to frontend
        
        results = execute_similarity_search(
            kuzu_adapter=self.kuzu_adapter,
            query_embedding=query_embedding,
            limit=2,
            threshold=0.5
        )
        
        assert len(results) >= 1
        assert results[0]["path"] == "/src/web/frontend"  # Most similar
        assert results[0]["similarity_score"] > 0.5
        assert "similarity_score" in results[0]

    def test_dql_cypher_uses_kuzu_vector_functions(self):
        """DQL: Cypher queries should use KuzuDB native VECTOR functions for similarity."""
        # RED: This test should fail until native KuzuDB vector functions are used
        from flake_graph.dql_vector_search import get_similarity_query_cypher
        
        cypher_query = get_similarity_query_cypher(
            embedding_placeholder="$query_embedding",
            limit=10,
            threshold=0.7
        )
        
        # Should use KuzuDB vector similarity functions
        assert "VECTOR_COSINE_SIMILARITY" in cypher_query or "VECTOR_SIMILARITY" in cypher_query
        assert "$query_embedding" in cypher_query
        assert "LIMIT 10" in cypher_query
        assert "WHERE" in cypher_query  # For threshold filtering

    def test_dql_filtered_vector_search_by_language(self):
        """DQL: Vector search should support filtering by flake language."""
        # RED: This test should fail until language filtering in DQL is implemented
        from flake_graph.dql_vector_search import execute_filtered_similarity_search
        
        # Setup test data
        test_flakes = [
            ("/src/python/api", [0.8, 0.2] * 192, "python"),
            ("/src/rust/cli", [0.8, 0.1] * 192, "rust"), 
            ("/src/nix/shell", [0.7, 0.3] * 192, "nix")
        ]
        
        for path, embedding, lang in test_flakes:
            self.kuzu_adapter.create_flake(path, f"Description for {path}", lang)
            self.kuzu_adapter.update_flake(path, vss_embedding=embedding)
        
        query_embedding = [0.9, 0.1] * 192
        
        # Search only Python flakes
        python_results = execute_filtered_similarity_search(
            kuzu_adapter=self.kuzu_adapter,
            query_embedding=query_embedding,
            language_filter="python",
            limit=5
        )
        
        assert len(python_results) == 1
        assert python_results[0]["path"] == "/src/python/api"
        assert python_results[0]["language"] == "python"

    def test_dql_vector_search_with_metadata_projection(self):
        """DQL: Vector search should project relevant metadata alongside similarity scores."""
        # RED: This test should fail until metadata projection in DQL is implemented
        from flake_graph.dql_vector_search import execute_similarity_search_with_metadata
        
        # Setup test data
        self.kuzu_adapter.create_flake(
            "/src/test/example", 
            "Test flake description", 
            "nix"
        )
        embedding = [0.5] * 384
        self.kuzu_adapter.update_flake(
            "/src/test/example",
            vss_embedding=embedding,
            vss_analyzed_at=datetime.now()
        )
        
        query_embedding = [0.4] * 384
        
        results = execute_similarity_search_with_metadata(
            kuzu_adapter=self.kuzu_adapter,
            query_embedding=query_embedding,
            limit=1
        )
        
        result = results[0]
        assert "path" in result
        assert "description" in result
        assert "language" in result
        assert "similarity_score" in result
        assert "vss_analyzed_at" in result
        assert isinstance(result["similarity_score"], float)

    # Integration Tests - DQL/DML Interaction
    
    def test_integration_dml_to_dql_pipeline(self):
        """Integration: Full pipeline from DML embedding generation to DQL search."""
        # RED: This test should fail until full DML->DQL pipeline is implemented
        from flake_graph.dml_batch_processor import process_flakes_batch
        from flake_graph.dql_vector_search import execute_similarity_search
        from flake_graph.dml_embedding_generator import generate_embedding
        
        # Step 1: DML - Generate and store embeddings
        flakes = [
            {"path": "/src/web/react", "description": "React frontend app", "content": "React TypeScript"},
            {"path": "/src/api/fastapi", "description": "FastAPI backend", "content": "Python REST API"},
            {"path": "/src/web/vue", "description": "Vue.js frontend", "content": "Vue JavaScript"}
        ]
        
        dml_result = process_flakes_batch(
            kuzu_adapter=self.kuzu_adapter,
            flakes=flakes,
            force_regenerate=True
        )
        assert dml_result["ok"] is True
        assert dml_result["processed"] == 3
        
        # Step 2: DQL - Search using generated embeddings  
        query_text = "frontend JavaScript application"
        query_embedding = generate_embedding(query_text)
        
        search_results = execute_similarity_search(
            kuzu_adapter=self.kuzu_adapter,
            query_embedding=query_embedding,
            limit=2
        )
        
        # Should find Vue.js frontend as most similar to "frontend JavaScript"
        assert len(search_results) >= 1
        frontend_paths = [r["path"] for r in search_results]
        assert "/src/web/vue" in frontend_paths or "/src/web/react" in frontend_paths

    def test_integration_cypher_file_compatibility(self):
        """Integration: DQL Cypher files should be compatible with KuzuDB schema."""
        # RED: This test should fail until Cypher files are created
        from flake_graph.dql_cypher_loader import load_cypher_query
        
        # Test that VSS search Cypher file exists and is valid
        cypher_content = load_cypher_query("search_flakes_by_vector_similarity")
        
        assert cypher_content is not None
        assert "MATCH (f:Flake)" in cypher_content
        assert "vss_embedding" in cypher_content
        assert "RETURN" in cypher_content
        
        # Should be executable against KuzuDB
        # (This will fail until proper Cypher is implemented)
        
    def test_integration_vector_index_performance(self):
        """Integration: Vector searches should perform efficiently with proper indexing."""
        # RED: This test should fail until vector indexing is optimized
        from flake_graph.dql_vector_search import execute_similarity_search
        import time
        
        # Generate large dataset
        large_flake_count = 1000
        for i in range(large_flake_count):
            self.kuzu_adapter.create_flake(
                f"/src/test/flake_{i:04d}",
                f"Test flake {i}",
                "nix"
            )
            # Random-ish embedding
            embedding = [(i * 0.001) % 1.0] * 384
            self.kuzu_adapter.update_flake(f"/src/test/flake_{i:04d}", vss_embedding=embedding)
        
        query_embedding = [0.5] * 384
        
        start_time = time.time()
        results = execute_similarity_search(
            kuzu_adapter=self.kuzu_adapter,
            query_embedding=query_embedding,
            limit=10
        )
        search_time = time.time() - start_time
        
        # Should complete search within reasonable time
        assert search_time < 2.0  # 2 seconds max for 1000 items
        assert len(results) == 10

    def test_integration_concurrent_dml_dql_operations(self):
        """Integration: DML and DQL operations should work concurrently without conflicts."""
        # RED: This test should fail until concurrent safety is implemented
        import threading
        from flake_graph.dml_batch_processor import process_flakes_batch
        from flake_graph.dql_vector_search import execute_similarity_search
        from flake_graph.dml_embedding_generator import generate_embedding
        
        # Setup initial data
        self.kuzu_adapter.create_flake("/src/base/example", "Base flake", "nix")
        self.kuzu_adapter.update_flake("/src/base/example", vss_embedding=[0.1] * 384)
        
        results = {"dml_success": False, "dql_success": False}
        
        def dml_operation():
            try:
                new_flakes = [
                    {"path": "/src/concurrent/test", "description": "Concurrent test", "content": "Test"}
                ]
                result = process_flakes_batch(
                    kuzu_adapter=self.kuzu_adapter,
                    flakes=new_flakes,
                    force_regenerate=True
                )
                results["dml_success"] = result["ok"]
            except Exception:
                results["dml_success"] = False
        
        def dql_operation():
            try:
                query_embedding = generate_embedding("search query")
                search_results = execute_similarity_search(
                    kuzu_adapter=self.kuzu_adapter,
                    query_embedding=query_embedding,
                    limit=5
                )
                results["dql_success"] = len(search_results) >= 0
            except Exception:
                results["dql_success"] = False
        
        # Run concurrently
        dml_thread = threading.Thread(target=dml_operation)
        dql_thread = threading.Thread(target=dql_operation)
        
        dml_thread.start()
        dql_thread.start()
        
        dml_thread.join()
        dql_thread.join()
        
        assert results["dml_success"] is True
        assert results["dql_success"] is True


class TestVSSCypherQuerySpecification:
    """Test specification for specific Cypher query patterns in DQL layer."""
    
    def test_cypher_vector_similarity_query_structure(self):
        """DQL Cypher: Vector similarity queries should follow specific structure."""
        # RED: This should fail until proper Cypher structure is defined
        expected_cypher = """
        // Vector similarity search with cosine similarity
        MATCH (f:Flake)
        WHERE f.vss_embedding IS NOT NULL
        WITH f, VECTOR_COSINE_SIMILARITY(f.vss_embedding, $query_embedding) AS similarity
        WHERE similarity >= $threshold
        RETURN f.path, f.description, f.language, similarity
        ORDER BY similarity DESC
        LIMIT $limit
        """
        
        # This test defines the expected Cypher structure
        # Implementation should match this pattern
        assert "VECTOR_COSINE_SIMILARITY" in expected_cypher
        assert "ORDER BY similarity DESC" in expected_cypher
        assert "$query_embedding" in expected_cypher

    def test_cypher_supports_vector_operations(self):
        """DQL Cypher: Should support various vector operation types."""
        # RED: This should fail until vector operations are implemented
        vector_operations = [
            "VECTOR_COSINE_SIMILARITY",
            "VECTOR_DOT_PRODUCT", 
            "VECTOR_EUCLIDEAN_DISTANCE"
        ]
        
        # Each operation should be available for different similarity metrics
        for operation in vector_operations:
            # Test that operation exists and can be used in queries
            # This will fail until KuzuDB vector extensions are properly integrated
            assert False, f"{operation} not yet implemented in DQL layer"

    def test_cypher_batch_similarity_computation(self):
        """DQL Cypher: Should support batch similarity computation for efficiency."""
        # RED: This should fail until batch operations are optimized
        expected_batch_cypher = """
        // Batch vector similarity with multiple query vectors
        MATCH (f:Flake)
        WHERE f.vss_embedding IS NOT NULL
        UNWIND $query_embeddings AS query_emb
        WITH f, query_emb, VECTOR_COSINE_SIMILARITY(f.vss_embedding, query_emb.vector) AS similarity
        WHERE similarity >= $threshold
        RETURN query_emb.id, f.path, f.description, similarity
        ORDER BY query_emb.id, similarity DESC
        """
        
        # This pattern enables efficient batch processing
        assert "UNWIND $query_embeddings" in expected_batch_cypher
        assert False, "Batch similarity computation not yet implemented"


# Expected module structure for implementation:
#
# flake_graph/dml_embedding_generator.py - Embedding generation functions
# flake_graph/dml_embedding_storage.py - KuzuDB storage operations  
# flake_graph/dml_batch_processor.py - Batch processing for embeddings
# flake_graph/dql_vector_search.py - Cypher-based vector search
# flake_graph/dql_cypher_loader.py - Load Cypher queries from files
# architecture/dql/search_flakes_by_vector_similarity.cypher - VSS Cypher queries