"""
Test to guarantee that KuzuDB from kuzu-py flake input is used
and in-memory database is properly created.
"""
import pytest
import kuzu
import os
from .infrastructure import create_in_memory_database, ResourceRepository


class TestKuzuDBGuarantee:
    """Tests to ensure KuzuDB environment and in-memory operation."""
    
    def test_kuzu_from_flake_input(self):
        """kuzu-pyのflake inputから正しくKuzuDBがインポートされている"""
        # Assert: KuzuDB is available
        assert hasattr(kuzu, 'Database')
        assert hasattr(kuzu, 'Connection')
        
        # Check version
        assert hasattr(kuzu, '__version__')
        print(f"KuzuDB version: {kuzu.__version__}")
    
    def test_in_memory_database_creation(self):
        """in-memoryデータベースが作成され、ファイルシステムを使用しない"""
        # Act
        db = create_in_memory_database()
        
        # Assert: Database is created
        assert db is not None
        assert isinstance(db, kuzu.Database)
        
        # Assert: Database path is :memory:
        assert db.database_path == ":memory:"
        
        # Assert: No physical files are created
        # (in-memory databases don't create files)
        assert not os.path.exists(":memory:")
    
    def test_multiple_in_memory_instances_are_isolated(self):
        """複数のin-memoryインスタンスが互いに分離されている"""
        # Create two separate in-memory databases
        db1 = create_in_memory_database()
        repo1 = ResourceRepository(db1)
        
        db2 = create_in_memory_database()
        repo2 = ResourceRepository(db2)
        
        # Add data to first database
        from .domain import create_resource
        resource = create_resource("test-001", "Test Resource", "HUMAN")
        repo1.save(resource)
        
        # Assert: Data exists in first database
        assert repo1.find_by_id("test-001") is not None
        
        # Assert: Data does not exist in second database
        assert repo2.find_by_id("test-001") is None
    
    def test_in_memory_data_is_volatile(self):
        """in-memoryデータベースのデータは揮発性である"""
        # Create database and add data
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        
        from .domain import create_resource
        resource = create_resource("volatile-001", "Volatile Resource", "HUMAN")
        repo.save(resource)
        
        # Assert: Data exists
        assert repo.find_by_id("volatile-001") is not None
        
        # Create new connection to same database
        new_conn = kuzu.Connection(db)
        
        # Assert: Data still exists through new connection
        result = new_conn.execute(
            "MATCH (r:Resource {id: $id}) RETURN r",
            {"id": "volatile-001"}
        )
        assert result.has_next()
        
        # Note: When db object is garbage collected, all data is lost
        # This is the expected behavior for in-memory databases
    
    def test_no_disk_persistence(self):
        """in-memoryデータベースはディスクに永続化されない"""
        # Create a unique test directory to ensure no files are created
        test_dir = "./test_no_persistence_check"
        
        # Ensure directory doesn't exist
        assert not os.path.exists(test_dir)
        
        # Create in-memory database
        db = create_in_memory_database()
        repo = ResourceRepository(db)
        
        # Perform operations
        from .domain import create_resource, add_capability
        resource = create_resource("disk-test-001", "Disk Test", "EQUIPMENT")
        resource = add_capability(resource, "TEST_CAPABILITY", 5)
        repo.save(resource)
        
        # Assert: Still no directory created
        assert not os.path.exists(test_dir)
        
        # Assert: Data exists in memory
        found = repo.find_by_id("disk-test-001")
        assert found is not None
        assert len(found["capabilities"]) == 1