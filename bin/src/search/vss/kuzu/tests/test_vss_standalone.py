#!/usr/bin/env python3
"""
Test that VSS service works standalone without POC dependency
"""

import pytest
import json
from pathlib import Path
import sys

# Ensure we don't accidentally import from POC
if "/home/nixos/bin/src/poc/search/vss" in sys.path:
    sys.path.remove("/home/nixos/bin/src/poc/search/vss")

from vss_service import VSSService


class TestVSSStandalone:
    """Test VSS service works independently of POC"""
    
    @pytest.fixture
    def vss_service(self):
        """In-memory VSS service"""
        service = VSSService(in_memory=True)
        yield service
    
    def test_embedding_service_is_standalone(self, vss_service):
        """Verify embedding service doesn't depend on POC"""
        # Get the embedding service
        embedding_service = vss_service._get_embedding_service()
        
        # Check it's our standalone implementation
        assert embedding_service.__class__.__name__ == "StandaloneEmbeddingService"
        assert hasattr(embedding_service, 'model_name')
        assert hasattr(embedding_service, 'dimension')
        assert embedding_service.model_name == "cl-nagoya/ruri-v3-30m"
        assert embedding_service.dimension == 256
    
    def test_document_embedding_with_prefixes(self, vss_service):
        """Test document embedding includes proper prefixes"""
        embedding_service = vss_service._get_embedding_service()
        
        # Embed documents
        docs = ["Python programming", "JavaScript development"]
        results = embedding_service.embed_documents(docs)
        
        assert len(results) == 2
        for result in results:
            assert hasattr(result, 'embeddings')
            assert hasattr(result, 'model_name')
            assert hasattr(result, 'dimension')
            assert len(result.embeddings) == 256
            assert result.model_name == "cl-nagoya/ruri-v3-30m"
            assert result.dimension == 256
    
    def test_query_embedding_with_prefixes(self, vss_service):
        """Test query embedding includes proper prefixes"""
        embedding_service = vss_service._get_embedding_service()
        
        # Embed query
        query = "programming languages"
        result = embedding_service.embed_query(query)
        
        assert hasattr(result, 'embeddings')
        assert hasattr(result, 'model_name')
        assert hasattr(result, 'dimension')
        assert len(result.embeddings) == 256
        assert result.model_name == "cl-nagoya/ruri-v3-30m"
        assert result.dimension == 256
    
    def test_prefixes_create_different_embeddings(self, vss_service):
        """Verify that same text with different prefixes creates different embeddings"""
        embedding_service = vss_service._get_embedding_service()
        
        # Same text
        text = "test"
        
        # Embed as document and query
        doc_result = embedding_service.embed_documents([text])[0]
        query_result = embedding_service.embed_query(text)
        
        # Embeddings should be different due to prefixes
        doc_emb = doc_result.embeddings
        query_emb = query_result.embeddings
        
        # Check they're not identical
        assert doc_emb != query_emb, "Document and query embeddings should differ due to prefixes"
    
    def test_full_search_workflow(self, vss_service):
        """Test complete indexing and search workflow"""
        # Index documents
        documents = [
            {"id": "1", "content": "Python is a versatile programming language"},
            {"id": "2", "content": "JavaScript powers the web"},
            {"id": "3", "content": "Rust provides memory safety"}
        ]
        
        index_result = vss_service.index_documents(documents)
        assert index_result["status"] == "success"
        assert index_result["indexed_count"] == 3
        
        # Search
        search_result = vss_service.search({
            "query": "programming language features",
            "limit": 3
        })
        
        # Validate result structure
        assert "results" in search_result
        assert "metadata" in search_result
        assert len(search_result["results"]) > 0
        
        # Validate metadata
        metadata = search_result["metadata"]
        assert metadata["model"] == "ruri-v3-30m"
        assert metadata["dimension"] == 256
        assert metadata["total_results"] == len(search_result["results"])
        assert "query_time_ms" in metadata
        
        # Validate each result
        for result in search_result["results"]:
            assert "id" in result
            assert "content" in result
            assert "score" in result
            assert "distance" in result
            assert 0 <= result["score"] <= 1
            assert result["distance"] >= 0


if __name__ == "__main__":
    # Run specific test for debugging
    pytest.main([__file__, "-v", "-k", "test_embedding_service_is_standalone"])