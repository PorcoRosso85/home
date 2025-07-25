"""Tests for in-memory storage adapter."""

import pytest
from s3_client.in_memory_adapter import InMemoryStorageAdapter


class TestInMemoryStorageAdapter:
    """Test the in-memory storage adapter implementation."""
    
    def test_put_and_get_object(self):
        """Test storing and retrieving an object."""
        adapter = InMemoryStorageAdapter()
        
        # Put an object
        key = "test/file.txt"
        body = b"Hello, World!"
        metadata = {"content-type": "text/plain"}
        
        adapter.put_object(key, body, metadata)
        
        # Get the object back
        retrieved = adapter.get_object(key)
        assert retrieved == body
    
    def test_delete_object(self):
        """Test deleting an object."""
        adapter = InMemoryStorageAdapter()
        
        # Put and delete
        key = "test/file.txt"
        adapter.put_object(key, b"data")
        adapter.delete_object(key)
        
        # Should raise KeyError
        with pytest.raises(KeyError):
            adapter.get_object(key)
    
    def test_list_objects(self):
        """Test listing objects with prefix."""
        adapter = InMemoryStorageAdapter()
        
        # Put multiple objects
        adapter.put_object("docs/readme.txt", b"readme")
        adapter.put_object("docs/guide.txt", b"guide")
        adapter.put_object("images/logo.png", b"logo")
        
        # List with prefix
        docs = adapter.list_objects("docs/")
        assert len(docs) == 2
        assert all(obj.key.startswith("docs/") for obj in docs)
        
        # List all
        all_objects = adapter.list_objects()
        assert len(all_objects) == 3
    
    def test_object_exists(self):
        """Test checking object existence."""
        adapter = InMemoryStorageAdapter()
        
        key = "test/file.txt"
        assert not adapter.object_exists(key)
        
        adapter.put_object(key, b"data")
        assert adapter.object_exists(key)
        
        adapter.delete_object(key)
        assert not adapter.object_exists(key)
    
    def test_get_provider_name(self):
        """Test provider name."""
        adapter = InMemoryStorageAdapter()
        assert adapter.get_provider_name() == "in-memory"
    
    def test_overwrite_object(self):
        """Test overwriting an existing object."""
        adapter = InMemoryStorageAdapter()
        
        key = "test/file.txt"
        adapter.put_object(key, b"original")
        adapter.put_object(key, b"updated")
        
        assert adapter.get_object(key) == b"updated"