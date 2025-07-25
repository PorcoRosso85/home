"""Tests for stdout storage adapter."""

import pytest
import json
from io import StringIO
from unittest.mock import patch
from s3_client.stdout_adapter import StdoutStorageAdapter


class TestStdoutStorageAdapter:
    """Test the stdout storage adapter implementation."""
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_put_object_outputs_to_stdout(self, mock_stdout):
        """Test that put_object outputs JSON to stdout."""
        adapter = StdoutStorageAdapter()
        
        adapter.put_object("test.txt", b"hello world", {"type": "text"})
        
        output = mock_stdout.getvalue()
        data = json.loads(output.strip())
        assert data["operation"] == "put_object"
        assert data["key"] == "test.txt"
        assert data["size"] == 11
        assert data["metadata"] == {"type": "text"}
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_get_object_outputs_to_stdout(self, mock_stdout):
        """Test that get_object outputs JSON and returns empty bytes."""
        adapter = StdoutStorageAdapter()
        
        result = adapter.get_object("test.txt")
        
        output = mock_stdout.getvalue()
        data = json.loads(output.strip())
        assert data["operation"] == "get_object"
        assert data["key"] == "test.txt"
        assert result == b""
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_delete_object_outputs_to_stdout(self, mock_stdout):
        """Test that delete_object outputs JSON to stdout."""
        adapter = StdoutStorageAdapter()
        
        adapter.delete_object("test.txt")
        
        output = mock_stdout.getvalue()
        data = json.loads(output.strip())
        assert data["operation"] == "delete_object"
        assert data["key"] == "test.txt"
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_list_objects_outputs_to_stdout(self, mock_stdout):
        """Test that list_objects outputs JSON and returns empty list."""
        adapter = StdoutStorageAdapter()
        
        result = adapter.list_objects("prefix/")
        
        output = mock_stdout.getvalue()
        data = json.loads(output.strip())
        assert data["operation"] == "list_objects"
        assert data["prefix"] == "prefix/"
        assert result == []
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_object_exists_outputs_to_stdout(self, mock_stdout):
        """Test that object_exists outputs JSON and returns False."""
        adapter = StdoutStorageAdapter()
        
        result = adapter.object_exists("test.txt")
        
        output = mock_stdout.getvalue()
        data = json.loads(output.strip())
        assert data["operation"] == "object_exists"
        assert data["key"] == "test.txt"
        assert result is False
    
    def test_get_provider_name(self):
        """Test provider name."""
        adapter = StdoutStorageAdapter()
        assert adapter.get_provider_name() == "stdout"