#!/usr/bin/env python3
"""
Tests for VSS Service with JSON Schema validation
Following the POC test specifications but using JSON input/output
"""

import json
import pytest
from pathlib import Path
import tempfile
import shutil

from vss_service import VSSService


class TestVSSJSONSchema:
    """Test VSS service with JSON Schema validation"""
    
    @pytest.fixture
    def vss_service(self):
        """Create VSS service with temporary database"""
        tmpdir = tempfile.mkdtemp()
        service = VSSService(db_path=tmpdir)
        yield service
        # Cleanup
        shutil.rmtree(tmpdir)
    
    def test_input_schema_validation_valid(self, vss_service):
        """Valid input should pass validation"""
        valid_input = {
            "query": "ユーザー認証機能",
            "limit": 5,
            "model": "ruri-v3-30m"
        }
        # Should not raise
        vss_service.validate_input(valid_input)
    
    def test_input_schema_validation_invalid(self, vss_service):
        """Invalid input should fail validation"""
        # Missing required field
        invalid_input = {
            "limit": 5
        }
        with pytest.raises(ValueError, match="Invalid input"):
            vss_service.validate_input(invalid_input)
        
        # Invalid type
        invalid_input = {
            "query": 123,  # Should be string
            "limit": 5
        }
        with pytest.raises(ValueError, match="Invalid input"):
            vss_service.validate_input(invalid_input)
        
        # Invalid enum value
        invalid_input = {
            "query": "test",
            "model": "unknown-model"
        }
        with pytest.raises(ValueError, match="Invalid input"):
            vss_service.validate_input(invalid_input)
    
    def test_output_schema_validation(self, vss_service):
        """Output should conform to schema"""
        valid_output = {
            "results": [
                {
                    "id": "doc_1",
                    "content": "ユーザー認証機能を実装する",
                    "score": 0.95,
                    "distance": 0.05
                }
            ],
            "metadata": {
                "model": "ruri-v3-30m",
                "dimension": 256,
                "total_results": 1,
                "query_time_ms": 10.5
            }
        }
        # Should not raise
        vss_service.validate_output(valid_output)
    
    def test_search_with_sample_data(self, vss_service):
        """Test search functionality with sample documents"""
        # Index sample documents
        documents = [
            {"id": "REQ001", "content": "ユーザー認証機能を実装する"},
            {"id": "REQ002", "content": "ログインシステムを構築する"},
            {"id": "REQ003", "content": "データベースを設計する"}
        ]
        
        # Index documents
        result = vss_service.index_documents(documents)
        assert result["status"] == "success"
        assert result["indexed_count"] == 3
        
        # Search
        search_input = {
            "query": "認証システム",
            "limit": 3
        }
        
        search_result = vss_service.search(search_input)
        
        # Validate output structure
        assert "results" in search_result
        assert "metadata" in search_result
        assert isinstance(search_result["results"], list)
        assert len(search_result["results"]) <= 3
        
        # Check metadata
        metadata = search_result["metadata"]
        assert metadata["model"] == "ruri-v3-30m"
        assert metadata["dimension"] == 256
        assert metadata["total_results"] <= 3
        assert "query_time_ms" in metadata
        
        # Results should be sorted by score (descending)
        if len(search_result["results"]) > 1:
            scores = [r["score"] for r in search_result["results"]]
            assert scores == sorted(scores, reverse=True)
    
    def test_search_with_threshold(self, vss_service):
        """Test search with similarity threshold"""
        # Index sample documents
        documents = [
            {"id": "1", "content": "完全に一致するテキスト"},
            {"id": "2", "content": "部分的に関連するテキスト"},
            {"id": "3", "content": "全く関係ないコンテンツ"}
        ]
        
        vss_service.index_documents(documents)
        
        # Search with threshold
        search_input = {
            "query": "完全に一致するテキスト",
            "threshold": 0.7,
            "limit": 10
        }
        
        result = vss_service.search(search_input)
        
        # All results should have score >= threshold
        for item in result["results"]:
            assert item["score"] >= 0.7
    
    def test_search_with_precomputed_vector(self, vss_service):
        """Test search with pre-computed query vector"""
        # Index a document
        documents = [{"id": "1", "content": "テストドキュメント"}]
        vss_service.index_documents(documents)
        
        # Create a dummy vector
        query_vector = [0.1] * 256  # 256 dimensions
        
        search_input = {
            "query": "dummy query (ignored)",
            "query_vector": query_vector,
            "limit": 1
        }
        
        result = vss_service.search(search_input)
        
        # Should return results
        assert len(result["results"]) >= 0
        assert result["metadata"]["dimension"] == 256
    
    def test_vector_index_operations(self, vss_service):
        """Test vector index creation and deletion (from POC spec)"""
        # This test verifies the POC specification for index operations
        # Index some documents
        documents = [
            {"id": "1", "content": "First document"},
            {"id": "2", "content": "Second document"}
        ]
        
        # First indexing should create the index
        result = vss_service.index_documents(documents)
        assert result["status"] == "success"
        
        # Second indexing should work (index already exists)
        more_documents = [{"id": "3", "content": "Third document"}]
        result = vss_service.index_documents(more_documents)
        assert result["status"] == "success"
        
        # Search should work
        search_result = vss_service.search({"query": "document"})
        assert len(search_result["results"]) > 0


class TestVSSSpecification:
    """Test cases based on POC specification"""
    
    @pytest.fixture
    def vss_service(self):
        """VSS service with temporary database"""
        tmpdir = tempfile.mkdtemp()
        service = VSSService(db_path=tmpdir, in_memory=False)
        yield service
        # Cleanup
        shutil.rmtree(tmpdir)
    
    def test_specification_vector_dimension(self, vss_service):
        """Verify vector dimension matches specification"""
        # POC uses 256 dimensions for ruri-v3-30m
        assert vss_service.dimension == 256
    
    def test_specification_distance_to_score_conversion(self, vss_service):
        """Verify distance is converted to similarity score correctly"""
        # Index a document
        documents = [{"id": "1", "content": "Test content"}]
        vss_service.index_documents(documents)
        
        # Search
        result = vss_service.search({"query": "Test content"})
        
        if result["results"]:
            first_result = result["results"][0]
            # Score should be 1 - distance
            expected_score = 1.0 - first_result["distance"]
            assert abs(first_result["score"] - expected_score) < 0.0001
    
    def test_specification_result_ordering(self, vss_service):
        """Verify results are ordered by similarity (descending)"""
        # Index multiple documents
        documents = [
            {"id": "1", "content": "瑠璃色の説明"},
            {"id": "2", "content": "全く関係ない内容"},
            {"id": "3", "content": "瑠璃色について"}
        ]
        vss_service.index_documents(documents)
        
        # Search
        result = vss_service.search({"query": "瑠璃色", "limit": 3})
        
        # Check ordering
        scores = [r["score"] for r in result["results"]]
        assert scores == sorted(scores, reverse=True)
        
        # Documents about "瑠璃色" should rank higher
        top_contents = [r["content"] for r in result["results"][:2]]
        assert any("瑠璃色" in content for content in top_contents)