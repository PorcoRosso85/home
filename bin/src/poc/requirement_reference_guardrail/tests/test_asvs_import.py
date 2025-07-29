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


def test_basic_import_functionality():
    """Test that ASVS data can be imported with embeddings"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Mock the minimum required components
        def create_column_mock(col_name):
            column = Mock()
            column.__getitem__ = Mock(side_effect=lambda i: Mock(as_py=Mock(return_value=f"test_{col_name}_{i}")))
            return column
        
        mock_table = Mock()
        mock_table.num_rows = 3
        mock_table.__getitem__ = Mock(side_effect=create_column_mock)
        
        mock_embedder = Mock()
        mock_embedder.embed = Mock(return_value=Mock(
            success=True,
            embedding=np.zeros(384),
            error=None
        ))
        
        with patch('scripts.import_asvs_with_embeddings.ASVSArrowConverter') as mock_converter:
            mock_converter.return_value.get_requirements_table.return_value = mock_table
            mock_converter.return_value.get_metadata.return_value = Mock(version='5.0')
            
            with patch('scripts.import_asvs_with_embeddings.create_embedder', return_value=mock_embedder):
                # Import should work without errors
                from scripts.import_asvs_with_embeddings import ASVSImporter
                importer = ASVSImporter(temp_dir, "test-model")
                
                with importer:
                    count = importer.import_asvs("/mock/path")
                    assert count == 3
                    assert mock_embedder.embed.call_count == 3
    
    finally:
        shutil.rmtree(temp_dir)


def test_import_with_embedding_failures():
    """Test that import handles embedding failures gracefully"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Mock embedder that fails sometimes
        mock_embedder = Mock()
        mock_embedder.embed = Mock(side_effect=[
            Mock(success=True, embedding=np.zeros(384)),
            Mock(success=False, error="Embedding failed"),
            Mock(success=True, embedding=np.zeros(384))
        ])
        
        def create_column_mock(col_name):
            column = Mock()
            column.__getitem__ = Mock(side_effect=lambda i: Mock(as_py=Mock(return_value=f"test_{col_name}_{i}")))
            return column
        
        mock_table = Mock()
        mock_table.num_rows = 3
        mock_table.__getitem__ = Mock(side_effect=create_column_mock)
        
        with patch('scripts.import_asvs_with_embeddings.ASVSArrowConverter') as mock_converter:
            mock_converter.return_value.get_requirements_table.return_value = mock_table
            mock_converter.return_value.get_metadata.return_value = Mock(version='5.0')
            
            with patch('scripts.import_asvs_with_embeddings.create_embedder', return_value=mock_embedder):
                from scripts.import_asvs_with_embeddings import ASVSImporter
                importer = ASVSImporter(temp_dir, "test-model")
                
                with importer:
                    # Should only import successful embeddings
                    count = importer.import_asvs("/mock/path")
                    assert count == 2
    
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
        
        conn.close()
        
        # Verify using importer
        from scripts.import_asvs_with_embeddings import ASVSImporter
        importer = ASVSImporter(temp_dir, "test-model")
        
        with importer:
            result = importer.verify_import()
            assert result['success']
            assert result['total_count'] == 1
            assert result['embedding_dimension'] == 384
    
    finally:
        shutil.rmtree(temp_dir)


def test_database_connection_error():
    """Test handling of invalid database paths"""
    from scripts.import_asvs_with_embeddings import ASVSImporter
    
    importer = ASVSImporter("/invalid/path", "test-model")
    
    with pytest.raises(RuntimeError, match="Failed to create database"):
        importer.connect()