"""Tests for DDL loader utility."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from .ddl_loader import DDLLoader, load_ddl_file
from .errors import DatabaseError, FileOperationError, ValidationError


class TestDDLLoader:
    """Test DDL loader functionality."""

    def test_init(self):
        """Test DDL loader initialization."""
        mock_adapter = Mock()
        loader = DDLLoader(mock_adapter)
        assert loader.graph_adapter == mock_adapter

    def test_validate_file_not_exists(self):
        """Test validation of non-existent file."""
        mock_adapter = Mock()
        loader = DDLLoader(mock_adapter)
        
        result = loader._validate_file(Path("/non/existent/file.cypher"))
        
        assert isinstance(result, dict)
        assert result["type"] == "FileOperationError"
        assert "does not exist" in result["message"]
        assert result["exists"] is False

    def test_validate_file_not_a_file(self, tmp_path):
        """Test validation of directory instead of file."""
        mock_adapter = Mock()
        loader = DDLLoader(mock_adapter)
        
        # Create a directory
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        result = loader._validate_file(test_dir)
        
        assert isinstance(result, dict)
        assert result["type"] == "ValidationError"
        assert "not a file" in result["message"]

    def test_validate_file_valid(self, tmp_path):
        """Test validation of valid DDL file."""
        mock_adapter = Mock()
        loader = DDLLoader(mock_adapter)
        
        # Create a valid DDL file
        ddl_file = tmp_path / "schema.cypher"
        ddl_file.write_text("CREATE NODE TABLE Test (id STRING PRIMARY KEY);")
        
        result = loader._validate_file(ddl_file)
        
        assert isinstance(result, dict)
        assert result.get("valid") is True

    def test_parse_statements_simple(self):
        """Test parsing simple DDL statements."""
        mock_adapter = Mock()
        loader = DDLLoader(mock_adapter)
        
        content = """
        CREATE NODE TABLE Test1 (id STRING PRIMARY KEY);
        CREATE NODE TABLE Test2 (id STRING PRIMARY KEY);
        """
        
        statements = loader._parse_statements(content)
        
        assert len(statements) == 2
        assert "Test1" in statements[0]
        assert "Test2" in statements[1]

    def test_parse_statements_with_comments(self):
        """Test parsing DDL with comments."""
        mock_adapter = Mock()
        loader = DDLLoader(mock_adapter)
        
        content = """
        // This is a comment
        CREATE NODE TABLE Test1 (id STRING PRIMARY KEY);
        
        /* This is a
           multi-line comment */
        CREATE NODE TABLE Test2 (id STRING PRIMARY KEY);
        
        // Another comment
        """
        
        statements = loader._parse_statements(content)
        
        assert len(statements) == 2
        assert "Test1" in statements[0]
        assert "Test2" in statements[1]
        assert "//" not in statements[0]
        assert "/*" not in statements[1]

    def test_parse_statements_with_quotes(self):
        """Test parsing DDL with quoted strings containing semicolons."""
        mock_adapter = Mock()
        loader = DDLLoader(mock_adapter)
        
        content = """
        CREATE NODE TABLE Test1 (
            id STRING PRIMARY KEY,
            data STRING DEFAULT 'test;data'
        );
        CREATE NODE TABLE Test2 (id STRING PRIMARY KEY);
        """
        
        statements = loader._parse_statements(content)
        
        assert len(statements) == 2
        assert "test;data" in statements[0]  # Semicolon inside quotes preserved

    def test_execute_statements_success(self):
        """Test successful statement execution."""
        mock_adapter = Mock()
        mock_adapter.execute_cypher.return_value = []
        loader = DDLLoader(mock_adapter)
        
        statements = [
            "CREATE NODE TABLE Test1 (id STRING PRIMARY KEY)",
            "CREATE NODE TABLE Test2 (id STRING PRIMARY KEY)"
        ]
        
        results = loader._execute_statements(statements, Path("test.cypher"))
        
        assert results["total_statements"] == 2
        assert len(results["statement_results"]) == 2
        assert all(r["success"] for r in results["statement_results"])
        assert mock_adapter.execute_cypher.call_count == 2

    def test_execute_statements_with_errors(self):
        """Test statement execution with errors."""
        mock_adapter = Mock()
        # First call succeeds, second fails
        mock_adapter.execute_cypher.side_effect = [
            [],  # Success
            Exception("Table already exists")  # Error
        ]
        loader = DDLLoader(mock_adapter)
        
        statements = [
            "CREATE NODE TABLE Test1 (id STRING PRIMARY KEY)",
            "CREATE NODE TABLE Test2 (id STRING PRIMARY KEY)"
        ]
        
        results = loader._execute_statements(statements, Path("test.cypher"))
        
        assert results["total_statements"] == 2
        assert results["statement_results"][0]["success"] is True
        assert results["statement_results"][1]["success"] is False
        assert "already exists" in results["statement_results"][1]["error"]

    def test_load_file_success(self, tmp_path):
        """Test loading a DDL file successfully."""
        mock_adapter = Mock()
        mock_adapter.execute_cypher.return_value = []
        loader = DDLLoader(mock_adapter)
        
        # Create a DDL file
        ddl_file = tmp_path / "schema.cypher"
        ddl_file.write_text("""
        // Test schema
        CREATE NODE TABLE Test1 (id STRING PRIMARY KEY);
        CREATE NODE TABLE Test2 (id STRING PRIMARY KEY);
        """)
        
        result = loader.load_file(ddl_file)
        
        assert isinstance(result, dict)
        assert result["total_statements"] == 2
        assert len(result["statement_results"]) == 2
        assert all(r["success"] for r in result["statement_results"])

    def test_load_directory_success(self, tmp_path):
        """Test loading multiple DDL files from directory."""
        mock_adapter = Mock()
        mock_adapter.execute_cypher.return_value = []
        loader = DDLLoader(mock_adapter)
        
        # Create multiple DDL files
        (tmp_path / "schema1.cypher").write_text("CREATE NODE TABLE Test1 (id STRING PRIMARY KEY);")
        (tmp_path / "schema2.cypher").write_text("CREATE NODE TABLE Test2 (id STRING PRIMARY KEY);")
        (tmp_path / "not_ddl.txt").write_text("This is not a DDL file")
        
        results = loader.load_directory(tmp_path)
        
        assert results["files_processed"] == 2
        assert results["total_statements"] == 2
        assert results["successful_statements"] == 2
        assert results["failed_statements"] == 0

    def test_load_directory_with_pattern(self, tmp_path):
        """Test loading DDL files with specific pattern."""
        mock_adapter = Mock()
        mock_adapter.execute_cypher.return_value = []
        loader = DDLLoader(mock_adapter)
        
        # Create files with different patterns
        (tmp_path / "migration_001.cypher").write_text("CREATE NODE TABLE Test1 (id STRING PRIMARY KEY);")
        (tmp_path / "migration_002.cypher").write_text("CREATE NODE TABLE Test2 (id STRING PRIMARY KEY);")
        (tmp_path / "schema.cypher").write_text("CREATE NODE TABLE Test3 (id STRING PRIMARY KEY);")
        
        results = loader.load_directory(tmp_path, pattern="migration_*.cypher")
        
        assert results["files_processed"] == 2
        assert results["pattern"] == "migration_*.cypher"

    def test_convenience_function(self, tmp_path):
        """Test convenience function load_ddl_file."""
        mock_adapter = Mock()
        mock_adapter.execute_cypher.return_value = []
        
        # Create a DDL file
        ddl_file = tmp_path / "test.cypher"
        ddl_file.write_text("CREATE NODE TABLE Test (id STRING PRIMARY KEY);")
        
        result = load_ddl_file(mock_adapter, ddl_file)
        
        assert isinstance(result, dict)
        assert result["total_statements"] == 1