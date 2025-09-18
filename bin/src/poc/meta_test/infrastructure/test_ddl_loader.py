"""Tests for DDL Loader v2 that wraps query_loader."""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from .ddl_loader import DDLLoader, load_ddl_file
from errors import FileOperationError, ValidationError


class TestDDLLoader:
    """Test DDL loader v2 functionality."""
    
    def test_load_ddl_success(self):
        """Test successful DDL loading through query_loader."""
        # Mock graph adapter
        mock_graph = Mock()
        mock_graph.execute_cypher = Mock(return_value={"success": True})
        
        # Mock load_typed_query to return DDL content
        ddl_content = """
        CREATE NODE TABLE TestTable (id STRING PRIMARY KEY);
        CREATE NODE TABLE AnotherTable (id STRING PRIMARY KEY);
        """
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=ddl_content)):
                loader = DDLLoader(mock_graph)
                success, results = loader.load_ddl("test_migration")
            
            
            # Verify both statements were executed
            assert success is True
            assert len(results) == 2
            assert mock_graph.execute_cypher.call_count == 2
            
    def test_load_ddl_file_not_found(self):
        """Test handling when DDL file is not found."""
        mock_graph = Mock()
        
        with patch('pathlib.Path.exists', return_value=False):
            loader = DDLLoader(mock_graph)
            success, results = loader.load_ddl("missing_file")
            
            assert success is False
            assert len(results) == 1
            assert results[0]["type"] == "NotFoundError"
            
    def test_parse_statements_with_comments(self):
        """Test parsing statements with various comment styles."""
        mock_graph = Mock()
        loader = DDLLoader(mock_graph)
        
        content = """
        // This is a comment
        CREATE NODE TABLE Table1 (id STRING PRIMARY KEY);
        
        -- Another comment style
        CREATE NODE TABLE Table2 (
            id STRING PRIMARY KEY,
            name STRING // inline comment
        );
        
        // Multi-line comment handling
        CREATE NODE TABLE Table3 (
            id STRING PRIMARY KEY
        );
        """
        
        statements = loader._parse_statements(content)
        
        assert len(statements) == 3
        assert "Table1" in statements[0]
        assert "Table2" in statements[1]
        assert "Table3" in statements[2]
        assert "//" not in statements[0]
        assert "--" not in statements[1]
        
    def test_parse_statements_with_quoted_semicolons(self):
        """Test parsing handles semicolons in quoted strings."""
        mock_graph = Mock()
        loader = DDLLoader(mock_graph)
        
        content = """
        CREATE NODE TABLE TestTable (
            id STRING PRIMARY KEY,
            description STRING DEFAULT 'Contains; semicolon'
        );
        CREATE NODE TABLE Another (id STRING PRIMARY KEY);
        """
        
        statements = loader._parse_statements(content)
        
        assert len(statements) == 2
        assert "Contains; semicolon" in statements[0]
        assert "Another" in statements[1]
        
    def test_execute_ddl_with_errors(self):
        """Test handling of execution errors."""
        mock_graph = Mock()
        
        # First statement succeeds, second fails
        mock_graph.execute_cypher = Mock(
            side_effect=[
                {"success": True},
                Exception("Invalid syntax")
            ]
        )
        
        ddl_content = """
        CREATE NODE TABLE Table1 (id STRING PRIMARY KEY);
        CREATE INVALID SYNTAX;
        """
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=ddl_content)):
                loader = DDLLoader(mock_graph)
                success, results = loader.load_ddl("test_with_errors")
            
            assert success is False
            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert "Invalid syntax" in results[1]["error"]["message"]
            
    def test_load_directory(self):
        """Test loading multiple DDL files from directory."""
        mock_graph = Mock()
        mock_graph.execute_cypher = Mock(return_value={"success": True})
        
        ddl_content = "CREATE NODE TABLE Test (id STRING PRIMARY KEY);"
        
        with patch('pathlib.Path.glob') as mock_glob:
            # Simulate finding two DDL files
            mock_glob.return_value = [
                Path("migration1.cypher"),
                Path("migration2.cypher")
            ]
            
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=ddl_content)):
                    loader = DDLLoader(mock_graph)
                    success, results = loader.load_directory("/ddl")
                    
                    assert success is True
                    assert len(results) == 2
                    assert "migration1.cypher" in results
                    assert "migration2.cypher" in results
                    
    def test_convenience_function(self):
        """Test the convenience function load_ddl_file."""
        mock_graph = Mock()
        mock_graph.execute_cypher = Mock(return_value={"success": True})
        
        ddl_content = "CREATE NODE TABLE Test (id STRING PRIMARY KEY);"
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=ddl_content)):
                success, results = load_ddl_file(mock_graph, "/path/to/migration.cypher")
                
                assert success is True
                assert len(results) == 1