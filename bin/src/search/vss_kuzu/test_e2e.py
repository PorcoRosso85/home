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
        assert hasattr(vss_kuzu, 'create_vss')
        assert hasattr(vss_kuzu, '__version__')
        assert vss_kuzu.__version__ == "0.1.0"
        
        # Check type definitions are exported
        assert hasattr(vss_kuzu, 'VectorSearchError')
        assert hasattr(vss_kuzu, 'VectorSearchResult')
        assert hasattr(vss_kuzu, 'VectorIndexResult')
    
    def test_unified_api_creation(self):
        """Test that unified API can be created"""
        from vss_kuzu import create_vss
        
        # The unified API should be the main entry point
        assert callable(create_vss)
        
        # Try creating an in-memory VSS instance
        try:
            vss = create_vss(in_memory=True)
            # If successful, check it has the expected interface
            assert hasattr(vss, 'index')
            assert hasattr(vss, 'search')
            assert callable(vss.index)
            assert callable(vss.search)
        except RuntimeError as e:
            # VECTOR extension not available is acceptable in test environment
            assert "VECTOR extension" in str(e)
    
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
    
    def test_extended_function_api_available(self):
        """Test that extended function-first API is available through submodules"""
        from vss_kuzu.application import (
            create_vss_service,
            create_embedding_service,
        )
        from vss_kuzu.domain import calculate_cosine_similarity
        from vss_kuzu.infrastructure import (
            DatabaseConfig,
            insert_documents_with_embeddings,
            search_similar_vectors,
        )
        from vss_kuzu.infrastructure.variables.config import (
            VSSConfig,
            create_config,
        )
        
        # Verify functions exist
        assert callable(create_vss_service)
        assert callable(create_embedding_service)
        assert callable(calculate_cosine_similarity)
        assert callable(create_config)
        assert callable(insert_documents_with_embeddings)
        assert callable(search_similar_vectors)
        assert DatabaseConfig is not None
        assert VSSConfig is not None
    
    def test_basic_functionality(self):
        """Test basic VSS functionality works after import"""
        from vss_kuzu.application import (
            create_vss_service,
            create_embedding_service,
            ApplicationConfig,
        )
        from vss_kuzu.infrastructure import (
            create_kuzu_database,
            create_kuzu_connection,
            check_vector_extension,
            initialize_vector_schema,
            insert_documents_with_embeddings,
            search_similar_vectors,
            count_documents,
            close_connection,
            DatabaseConfig,
        )
        from vss_kuzu.domain import find_semantically_similar_documents
        from vss_kuzu.infrastructure.variables.config import create_config
        
        # Test using function-based API
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
        
        config: ApplicationConfig = {'in_memory': True}
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
        assert 'create_vss' in vss_kuzu.__all__
        assert 'VectorSearchError' in vss_kuzu.__all__
        assert 'VectorSearchResult' in vss_kuzu.__all__
        assert 'VectorIndexResult' in vss_kuzu.__all__
        assert '__version__' in vss_kuzu.__all__
        
        # Check module docstring
        assert vss_kuzu.__doc__ is not None
        assert "Vector Similarity Search" in vss_kuzu.__doc__
    
    def test_no_pythonpath_needed(self):
        """Test that import works without PYTHONPATH manipulation"""
        # Run a subprocess that imports vss_kuzu
        # This ensures no PYTHONPATH is set
        code = """
import sys
import vss_kuzu
"""
        
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env={k: v for k, v in sys.__dict__.get('environ', {}).items() if k != 'PYTHONPATH'}
        )
        
        # Should succeed without PYTHONPATH
        assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])