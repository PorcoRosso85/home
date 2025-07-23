#!/usr/bin/env python3
"""
E2E tests for vss_kuzu package import capability

These tests verify that vss_kuzu can be imported and used from external projects
when included as a flake input.
"""

import pytest
import subprocess
import sys
from pathlib import Path


class TestE2EImportCapability:
    """Test vss_kuzu can be imported from external contexts"""
    
    def test_package_import(self):
        """Test that vss_kuzu package can be imported"""
        # This test runs in the Nix environment where vss_kuzu is installed
        import vss_kuzu
        
        # Verify package has expected attributes
        assert hasattr(vss_kuzu, 'VSSService')
        assert hasattr(vss_kuzu, '__version__')
        assert vss_kuzu.__version__ == "0.1.0"
    
    def test_vss_service_creation(self):
        """Test that VSSService can be instantiated"""
        from vss_kuzu import VSSService
        
        # Create service instance
        service = VSSService(in_memory=True)
        assert service is not None
        assert hasattr(service, 'index_documents')
        assert hasattr(service, 'search')
    
    def test_type_definitions_available(self):
        """Test that type definitions are accessible"""
        from vss_kuzu import (
            VectorSearchError,
            VectorSearchResult,
            VectorIndexResult,
        )
        
        # These should be TypedDict classes
        assert VectorSearchError is not None
        assert VectorSearchResult is not None
        assert VectorIndexResult is not None
    
    def test_function_api_available(self):
        """Test that function-first API is available"""
        from vss_kuzu import (
            create_vss_service,
            create_embedding_service,
            calculate_cosine_similarity,
            DatabaseConfig,
        )
        
        # Verify functions exist
        assert callable(create_vss_service)
        assert callable(create_embedding_service)
        assert callable(calculate_cosine_similarity)
        assert DatabaseConfig is not None
    
    def test_basic_functionality(self):
        """Test basic VSS functionality works after import"""
        from vss_kuzu import VSSService, create_vss_service, create_embedding_service
        from vss_kuzu.infrastructure import (
            create_kuzu_database,
            create_kuzu_connection,
            check_vector_extension,
            initialize_vector_schema,
            insert_documents_with_embeddings,
            search_similar_vectors,
            count_documents,
            close_connection,
        )
        from vss_kuzu.domain import find_semantically_similar_documents
        from vss_kuzu.application import ApplicationConfig
        
        # Test 1: Using VSSService class (backwards compatibility)
        service = VSSService(in_memory=True)
        result = service.search({"query": "test"})
        assert isinstance(result, dict)
        assert "ok" in result
        if result.get("ok"):
            assert "results" in result
            assert isinstance(result["results"], list)
        
        # Test 2: Using function-based API
        embedding_func = create_embedding_service()
        vss_funcs = create_vss_service(
            create_db_func=create_kuzu_database,
            create_conn_func=create_kuzu_connection,
            check_vector_func=check_vector_extension,
            init_schema_func=initialize_vector_schema,
            insert_docs_func=insert_documents_with_embeddings,
            search_func=search_similar_vectors,
            count_func=count_documents,
            close_func=close_connection,
            generate_embedding_func=embedding_func,
            calculate_similarity_func=find_semantically_similar_documents
        )
        
        config = ApplicationConfig(in_memory=True)
        search_func = vss_funcs["search"]
        result = search_func({"query": "test"}, config)
        assert isinstance(result, dict)
        assert "ok" in result
    
    def test_module_structure(self):
        """Test that module has expected structure"""
        import vss_kuzu
        
        # Check __all__ exports
        assert hasattr(vss_kuzu, '__all__')
        assert isinstance(vss_kuzu.__all__, list)
        assert 'VSSService' in vss_kuzu.__all__
        
        # Check module docstring
        assert vss_kuzu.__doc__ is not None
        assert "Vector Similarity Search" in vss_kuzu.__doc__
    
    def test_no_pythonpath_needed(self):
        """Test that import works without PYTHONPATH manipulation"""
        # Run a subprocess that imports vss_kuzu
        # This ensures no PYTHONPATH is set
        code = """
import sys
print("PYTHONPATH:", sys.path)
import vss_kuzu
print("Import successful")
print("Version:", vss_kuzu.__version__)
"""
        
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env={k: v for k, v in sys.__dict__.get('environ', {}).items() if k != 'PYTHONPATH'}
        )
        
        # Should succeed without PYTHONPATH
        assert result.returncode == 0
        assert "Import successful" in result.stdout
        assert "Version: 0.1.0" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])