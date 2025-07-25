"""Tests for storage adapter interface."""

import pytest
from typing import Protocol
from s3_client.storage_adapter import StorageAdapter


class TestStorageAdapterInterface:
    """Test the StorageAdapter protocol definition."""
    
    def test_storage_adapter_is_protocol(self):
        """Test that StorageAdapter is a Protocol."""
        assert hasattr(StorageAdapter, '__protocol__')
    
    def test_storage_adapter_has_required_methods(self):
        """Test that StorageAdapter defines all required methods."""
        required_methods = [
            'put_object',
            'get_object',
            'delete_object',
            'list_objects',
            'object_exists',
            'get_provider_name'
        ]
        
        for method in required_methods:
            assert hasattr(StorageAdapter, method)
    
    def test_storage_adapter_method_signatures(self):
        """Test that StorageAdapter methods have correct signatures."""
        # Check put_object signature
        put_annotations = StorageAdapter.put_object.__annotations__
        assert 'key' in put_annotations
        assert 'body' in put_annotations
        assert 'metadata' in put_annotations
        
        # Check get_object signature
        get_annotations = StorageAdapter.get_object.__annotations__
        assert 'key' in get_annotations
        assert 'return' in get_annotations
        
        # Check list_objects signature
        list_annotations = StorageAdapter.list_objects.__annotations__
        assert 'prefix' in list_annotations
        assert 'return' in list_annotations