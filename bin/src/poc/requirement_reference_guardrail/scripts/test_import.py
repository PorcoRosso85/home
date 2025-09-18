#!/usr/bin/env python3
"""
Test script for ASVS import with embeddings

This script tests the import_asvs_with_embeddings.py functionality
"""
import sys
import tempfile
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from scripts.import_asvs_with_embeddings import ASVSImporter

# Add kuzu_py to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "persistence/kuzu_py"))
from kuzu_py import create_connection, create_database


def test_schema_creation():
    """Test that the schema is created correctly"""
    logger.info("Testing schema creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        with ASVSImporter(str(db_path)) as importer:
            importer.ensure_schema()
            
            # Verify table exists
            result = importer._conn.execute("CALL TABLE_INFO('ReferenceEntity') RETURN *")
            columns = []
            while result.has_next():
                row = result.get_next()
                columns.append(row[1])  # Column name is at index 1
                
            expected_columns = {
                'id', 'title', 'description', 'source', 
                'category', 'level', 'embedding', 'version', 'url'
            }
            
            actual_columns = set(columns)
            missing = expected_columns - actual_columns
            extra = actual_columns - expected_columns
            
            if missing:
                logger.error(f"Missing columns: {missing}")
            if extra:
                logger.warning(f"Extra columns: {extra}")
                
            assert expected_columns.issubset(actual_columns), f"Schema mismatch"
            logger.info("✓ Schema creation test passed")


def test_sample_import():
    """Test importing a small sample of ASVS data"""
    logger.info("Testing sample ASVS import...")
    
    # Create sample ASVS data
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create ASVS directory structure
        asvs_dir = Path(tmpdir) / "5.0" / "en"
        asvs_dir.mkdir(parents=True)
        
        # Create a sample ASVS markdown file
        sample_md = asvs_dir / "0x10-V1-Architecture.md"
        sample_md.write_text("""# V1 Architecture, Design and Threat Modeling

## V1.1 Secure Software Development Lifecycle

| # | Description | L1 | L2 | L3 | CWE |
| --- | --- | --- | --- | --- | --- |
| **1.1.1** | Verify the use of a secure software development lifecycle that addresses security in all stages of development. | | ✓ | ✓ | |
| **1.1.2** | Verify the use of threat modeling for every design change or sprint planning to identify threats, plan for countermeasures, facilitate appropriate risk responses, and guide security testing. | | ✓ | ✓ | 1053 |
""")
        
        # Create database
        db_path = Path(tmpdir) / "test_import.db"
        
        with ASVSImporter(str(db_path)) as importer:
            count = importer.import_asvs(str(asvs_dir.parent))
            
            assert count > 0, "No requirements imported"
            logger.info(f"✓ Imported {count} requirements")
            
            # Verify the import
            verification = importer.verify_import()
            assert verification['success'], f"Verification failed: {verification.get('error')}"
            assert verification['total_count'] == count, "Count mismatch"
            assert verification['embedding_dimension'] == 384, "Wrong embedding dimension"
            
            logger.info("✓ Sample import test passed")


def test_embedding_generation():
    """Test that embeddings are generated correctly"""
    logger.info("Testing embedding generation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_embeddings.db"
        
        # Create a simple ASVS file
        asvs_dir = Path(tmpdir) / "5.0" / "en"
        asvs_dir.mkdir(parents=True)
        
        sample_md = asvs_dir / "0x10-V1-Architecture.md"
        sample_md.write_text("""# V1 Architecture, Design and Threat Modeling

## V1.1 Secure Software Development Lifecycle

| # | Description | L1 | L2 | L3 | CWE |
| --- | --- | --- | --- | --- | --- |
| **1.1.1** | Verify the use of a secure software development lifecycle that addresses security in all stages of development. | | ✓ | ✓ | |
""")
        
        with ASVSImporter(str(db_path), model_name="sentence-transformers/all-MiniLM-L6-v2") as importer:
            count = importer.import_asvs(str(asvs_dir.parent))
            
            # Check that embeddings were created
            result = importer._conn.execute("""
                MATCH (r:ReferenceEntity) 
                WHERE r.embedding IS NOT NULL 
                RETURN r.id, SIZE(r.embedding) as dim
            """)
            
            has_embeddings = False
            while result.has_next():
                has_embeddings = True
                id, dim = result.get_next()
                assert dim == 384, f"Wrong embedding dimension for {id}: {dim}"
                logger.info(f"✓ Embedding created for {id} with dimension {dim}")
                
            assert has_embeddings, "No embeddings were created"
            logger.info("✓ Embedding generation test passed")


def test_error_handling():
    """Test error handling scenarios"""
    logger.info("Testing error handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_errors.db"
        
        # Test with non-existent ASVS path
        with ASVSImporter(str(db_path)) as importer:
            try:
                importer.import_asvs("/non/existent/path")
                assert False, "Should have raised an error"
            except Exception as e:
                logger.info(f"✓ Correctly handled missing path: {e}")
                
        # Test with empty ASVS directory
        empty_dir = Path(tmpdir) / "empty"
        empty_dir.mkdir()
        
        with ASVSImporter(str(db_path)) as importer:
            count = importer.import_asvs(str(empty_dir))
            assert count == 0, "Should import 0 requirements from empty directory"
            logger.info("✓ Correctly handled empty directory")
            
    logger.info("✓ Error handling test passed")


def run_all_tests():
    """Run all tests"""
    logger.info("Starting ASVS import tests...")
    
    try:
        test_schema_creation()
        test_sample_import()
        test_embedding_generation()
        test_error_handling()
        
        logger.info("\n✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()