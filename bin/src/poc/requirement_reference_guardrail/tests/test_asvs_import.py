"""
Tests for ASVS import with embeddings functionality.
Simplified to focus on essential import verification only.
"""
import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch
import numpy as np
import kuzu


def temp_db_dir():
    """Create a temporary directory for the database"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def create_column_mock(col_name):
    """Create a mock column with appropriate values for each ASVS field"""
    column = Mock()
    # Return appropriate values for each column
    if col_name == 'uri':
        column.__getitem__ = Mock(side_effect=lambda i: Mock(as_py=Mock(return_value=f"ASVS-TEST-{i}")))
    elif col_name == 'number':
        column.__getitem__ = Mock(side_effect=lambda i: Mock(as_py=Mock(return_value=f"1.{i}.1")))
    elif col_name == 'description':
        column.__getitem__ = Mock(side_effect=lambda i: Mock(as_py=Mock(return_value=f"Test requirement {i}")))
    elif col_name in ['level1', 'level2', 'level3']:
        column.__getitem__ = Mock(side_effect=lambda i: Mock(as_py=Mock(return_value=True if col_name == 'level1' else False)))
    elif col_name in ['section', 'chapter']:
        column.__getitem__ = Mock(side_effect=lambda i: Mock(as_py=Mock(return_value=f"Test {col_name} {i}")))
    elif col_name in ['cwe', 'nist']:
        column.__getitem__ = Mock(side_effect=lambda i: Mock(as_py=Mock(return_value="123")))
    else:
        column.__getitem__ = Mock(side_effect=lambda i: Mock(as_py=Mock(return_value=f"test_{col_name}_{i}")))
    return column


def test_basic_import_functionality():
    """Test that ASVS data can be imported with embeddings"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        mock_table = Mock()
        mock_table.num_rows = 3
        mock_table.__getitem__ = Mock(side_effect=create_column_mock)
        
        # Mock embedder as a callable that returns embedding results
        mock_embedder = Mock(return_value={
            'ok': True,
            'embeddings': [np.zeros(384)]
        })
        
        with patch('scripts.import_asvs_with_embeddings.ASVSArrowConverter') as mock_converter:
            mock_converter.return_value.get_requirements_table.return_value = mock_table
            mock_converter.return_value.get_metadata.return_value = Mock(version='5.0')
            
            with patch('scripts.import_asvs_with_embeddings.create_embedder', return_value=mock_embedder):
                with patch('scripts.import_asvs_with_embeddings.create_database') as mock_create_db:
                    with patch('scripts.import_asvs_with_embeddings.create_connection') as mock_create_conn:
                        # Mock database and connection creation
                        mock_db = Mock(spec=['__class__'])
                        mock_db.__class__.__name__ = 'Database'
                        mock_create_db.return_value = mock_db
                        
                        mock_conn = Mock(spec=['execute', '__class__'])
                        mock_conn.__class__.__name__ = 'Connection'
                        mock_conn.execute = Mock()
                        mock_create_conn.return_value = mock_conn
                        
                        # Import the functional API
                        from scripts.import_asvs_with_embeddings import (
                            create_database_connection,
                            create_embedder_function,
                            import_asvs_requirements
                        )
                        
                        # Use functional API
                        # Since we're mocking, we need to patch create_database_connection too
                        with patch('scripts.import_asvs_with_embeddings.create_database_connection') as mock_db_conn:
                            mock_db_conn.return_value = (mock_db, mock_conn)
                            
                            # Create embedder
                            embedder_result = create_embedder_function("test-model")
                            
                            # Import requirements
                            result = import_asvs_requirements(mock_conn, mock_embedder, "/mock/path")
                            assert result['success']
                            assert result['imported_count'] == 3
                            assert mock_embedder.call_count == 3
    
    finally:
        shutil.rmtree(temp_dir)


def test_import_with_embedding_failures():
    """Test that import handles embedding failures gracefully"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Mock embedder as a callable that fails sometimes
        mock_embedder = Mock(side_effect=[
            {'ok': True, 'embeddings': [np.zeros(384)]},
            {'ok': False, 'message': "Embedding failed"},
            {'ok': True, 'embeddings': [np.zeros(384)]}
        ])
        
        mock_table = Mock()
        mock_table.num_rows = 3
        mock_table.__getitem__ = Mock(side_effect=create_column_mock)
        
        with patch('scripts.import_asvs_with_embeddings.ASVSArrowConverter') as mock_converter:
            mock_converter.return_value.get_requirements_table.return_value = mock_table
            mock_converter.return_value.get_metadata.return_value = Mock(version='5.0')
            
            with patch('scripts.import_asvs_with_embeddings.create_embedder', return_value=mock_embedder):
                with patch('scripts.import_asvs_with_embeddings.create_database') as mock_create_db:
                    with patch('scripts.import_asvs_with_embeddings.create_connection') as mock_create_conn:
                        # Mock database and connection creation
                        mock_db = Mock(spec=['__class__'])
                        mock_db.__class__.__name__ = 'Database'
                        mock_create_db.return_value = mock_db
                        
                        mock_conn = Mock(spec=['execute', '__class__'])
                        mock_conn.__class__.__name__ = 'Connection'
                        mock_conn.execute = Mock()
                        mock_create_conn.return_value = mock_conn
                        
                        from scripts.import_asvs_with_embeddings import import_asvs_requirements
                        
                        # Should only import successful embeddings
                        result = import_asvs_requirements(mock_conn, mock_embedder, "/mock/path")
                        assert result['success']
                        assert result['imported_count'] == 2
    
    finally:
        shutil.rmtree(temp_dir)


def test_verify_import_basic():
    """Test basic verification of imported data"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create database with test data
        db = kuzu.Database(temp_dir + "/test.db")
        conn = kuzu.Connection(db)
        
        conn.execute("""
            CREATE NODE TABLE ReferenceEntity (
                id STRING PRIMARY KEY,
                title STRING,
                description STRING,
                source STRING,
                category STRING,
                level STRING,
                embedding DOUBLE[384],
                version STRING,
                url STRING
            )
        """)
        
        # Insert minimal test data
        test_embedding = [0.0] * 384
        conn.execute("""
            CREATE (r:ReferenceEntity {
                id: 'ASVS-TEST',
                title: 'Test Title',
                description: 'Test Description',
                source: 'OWASP ASVS',
                category: 'Test',
                level: 'L1',
                embedding: $embedding,
                version: '5.0',
                url: 'https://example.com'
            })
        """, {'embedding': test_embedding})
        
        # Verify using functional API
        from scripts.import_asvs_with_embeddings import verify_import
        
        result = verify_import(conn)
        assert result['success']
        assert result['total_count'] == 1
        assert result['embedding_dimension'] == 384
        
        conn.close()
    
    finally:
        shutil.rmtree(temp_dir)


def test_database_connection_error():
    """Test handling of invalid database paths"""
    from scripts.import_asvs_with_embeddings import create_database_connection
    
    # Should return error result instead of raising exception
    result = create_database_connection("/invalid/path")
    assert isinstance(result, dict)
    assert not result.get("success", False)
    assert "error" in result
    # The error could be from either database creation or the exception handler
    assert "Failed to" in result["error"]


def test_create_embedder_function():
    """Test embedder function creation"""
    with patch('scripts.import_asvs_with_embeddings.create_embedder') as mock_create_embedder:
        # Mock successful embedder creation
        mock_embedder_func = Mock()
        mock_create_embedder.return_value = mock_embedder_func
        
        from scripts.import_asvs_with_embeddings import create_embedder_function
        
        result = create_embedder_function("test-model")
        assert callable(result)
        assert result == mock_embedder_func
        
        # Test error case
        mock_create_embedder.return_value = {'ok': False, 'message': 'Model not found'}
        result = create_embedder_function("invalid-model")
        assert isinstance(result, dict)
        assert not result.get("success", False)
        assert "error" in result


def test_load_asvs_requirements():
    """Test loading ASVS requirements"""
    with patch('scripts.import_asvs_with_embeddings.ASVSArrowConverter') as mock_converter:
        # Mock successful loading
        mock_table = Mock()
        mock_table.num_rows = 2
        mock_table.__getitem__ = Mock(side_effect=create_column_mock)
        
        mock_converter.return_value.get_requirements_table.return_value = mock_table
        mock_converter.return_value.get_metadata.return_value = Mock(version='5.0')
        
        from scripts.import_asvs_with_embeddings import load_asvs_requirements
        
        result = load_asvs_requirements("/test/path")
        assert isinstance(result, tuple)
        requirements, version = result
        assert len(requirements) == 2
        assert version == '5.0'
        
        # Test error case
        mock_converter.side_effect = Exception("Failed to load")
        result = load_asvs_requirements("/invalid/path")
        assert isinstance(result, dict)
        assert not result.get("success", False)
        assert "error" in result


def test_generate_embedding():
    """Test embedding generation function"""
    from scripts.import_asvs_with_embeddings import generate_embedding
    
    # Test successful embedding
    mock_embedder = Mock(return_value={
        'ok': True,
        'embeddings': [np.array([0.1, 0.2, 0.3])]
    })
    
    result = generate_embedding(mock_embedder, "test content")
    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 3
    
    # Test failed embedding
    mock_embedder = Mock(return_value={
        'ok': False,
        'message': 'Embedding failed'
    })
    
    result = generate_embedding(mock_embedder, "test content")
    assert result is None


def test_determine_requirement_level():
    """Test requirement level determination"""
    from scripts.import_asvs_with_embeddings import determine_requirement_level
    
    # Test L1
    req = {'level1': True, 'level2': False, 'level3': False}
    assert determine_requirement_level(req) == "L1"
    
    # Test L2
    req = {'level1': True, 'level2': True, 'level3': False}
    assert determine_requirement_level(req) == "L2"
    
    # Test L3
    req = {'level1': True, 'level2': True, 'level3': True}
    assert determine_requirement_level(req) == "L3"
    
    # Test N/A
    req = {'level1': False, 'level2': False, 'level3': False}
    assert determine_requirement_level(req) == "N/A"