#!/usr/bin/env python3
"""
Tests for the kuzu_storage module.
"""

import pytest
import tempfile
import os
from pathlib import Path

from tags_in_dir import Symbol
from kuzu_storage import KuzuStorage


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def storage():
    """Create an in-memory KuzuStorage instance."""
    return KuzuStorage(":memory:")


@pytest.fixture
def sample_symbols():
    """Create sample symbols for testing."""
    return [
        Symbol(
            name="hello_world",
            kind="function",
            location_uri="file:///home/user/main.py#L10",
            scope="module",
            signature="()"
        ),
        Symbol(
            name="Greeter",
            kind="class",
            location_uri="file:///home/user/main.py#L20",
            scope="module"
        ),
        Symbol(
            name="greet",
            kind="method",
            location_uri="file:///home/user/main.py#L25",
            scope="Greeter:class",
            signature="(self, name)"
        ),
        Symbol(
            name="format_string",
            kind="function",
            location_uri="file:///home/user/utils.py#L5",
            scope="module",
            signature="(s)"
        ),
        Symbol(
            name="StringFormatter",
            kind="class",
            location_uri="file:///home/user/utils.py#L15"
        )
    ]


class TestKuzuStorage:
    """Test cases for KuzuStorage."""

    def test_initialization(self):
        """Test storage initialization."""
        # Test in-memory database
        storage = KuzuStorage(":memory:")
        assert storage.db_path == ":memory:"
        
        # Test file-based database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        try:
            storage = KuzuStorage(db_path)
            assert storage.db_path == db_path
        finally:
            os.unlink(db_path)

    def test_store_single_symbol(self, storage, sample_symbols):
        """Test storing a single symbol."""
        symbol = sample_symbols[0]
        assert storage.store_symbol(symbol) is True
        
        # Verify it was stored
        results = storage.find_symbols_by_name("hello_world")
        assert len(results) == 1
        assert results[0]["name"] == "hello_world"
        assert results[0]["kind"] == "function"
        assert results[0]["location_uri"] == "file:///home/user/main.py#L10"

    def test_store_multiple_symbols(self, storage, sample_symbols):
        """Test storing multiple symbols."""
        count = storage.store_symbols(sample_symbols)
        assert count == len(sample_symbols)
        
        # Verify all were stored
        stats = storage.get_statistics()
        assert stats["total_symbols"] == len(sample_symbols)

    def test_store_duplicate_symbol(self, storage, sample_symbols):
        """Test that storing duplicate symbols updates existing ones."""
        symbol = sample_symbols[0]
        
        # Store once
        assert storage.store_symbol(symbol) is True
        
        # Modify and store again
        symbol.signature = "(modified)"
        assert storage.store_symbol(symbol) is True
        
        # Should still have only one symbol
        results = storage.find_symbols_by_name("hello_world")
        assert len(results) == 1
        assert results[0]["signature"] == "(modified)"

    def test_create_calls_relationship(self, storage, sample_symbols):
        """Test creating CALLS relationships."""
        # Store symbols first
        storage.store_symbols(sample_symbols[:3])
        
        # Create relationship: hello_world calls greet
        assert storage.create_calls_relationship(
            sample_symbols[0].location_uri,
            sample_symbols[2].location_uri,
            line_number=12
        ) is True
        
        # Verify relationship exists
        stats = storage.get_statistics()
        assert stats["total_relationships"] == 1

    def test_find_symbols_by_file(self, storage, sample_symbols):
        """Test finding symbols by file."""
        storage.store_symbols(sample_symbols)
        
        # Find symbols in main.py
        main_symbols = storage.find_symbols_by_file("/home/user/main.py")
        assert len(main_symbols) == 3
        
        main_names = {s["name"] for s in main_symbols}
        assert main_names == {"hello_world", "Greeter", "greet"}
        
        # Find symbols in utils.py
        utils_symbols = storage.find_symbols_by_file("/home/user/utils.py")
        assert len(utils_symbols) == 2
        
        utils_names = {s["name"] for s in utils_symbols}
        assert utils_names == {"format_string", "StringFormatter"}

    def test_find_symbols_by_name(self, storage, sample_symbols):
        """Test finding symbols by name."""
        storage.store_symbols(sample_symbols)
        
        # Find existing symbol
        results = storage.find_symbols_by_name("Greeter")
        assert len(results) == 1
        assert results[0]["kind"] == "class"
        
        # Find non-existing symbol
        results = storage.find_symbols_by_name("non_existent")
        assert len(results) == 0

    def test_find_symbols_by_kind(self, storage, sample_symbols):
        """Test finding symbols by kind."""
        storage.store_symbols(sample_symbols)
        
        # Find functions
        functions = storage.find_symbols_by_kind("function")
        assert len(functions) == 2
        func_names = {f["name"] for f in functions}
        assert func_names == {"hello_world", "format_string"}
        
        # Find classes
        classes = storage.find_symbols_by_kind("class")
        assert len(classes) == 2
        class_names = {c["name"] for c in classes}
        assert class_names == {"Greeter", "StringFormatter"}
        
        # Find methods
        methods = storage.find_symbols_by_kind("method")
        assert len(methods) == 1
        assert methods[0]["name"] == "greet"

    def test_find_symbol_calls(self, storage, sample_symbols):
        """Test finding call relationships."""
        # Store symbols
        storage.store_symbols(sample_symbols[:4])
        
        # Create relationships
        # hello_world calls greet
        storage.create_calls_relationship(
            sample_symbols[0].location_uri,  # hello_world
            sample_symbols[2].location_uri,  # greet
            line_number=12
        )
        
        # hello_world calls format_string
        storage.create_calls_relationship(
            sample_symbols[0].location_uri,  # hello_world
            sample_symbols[3].location_uri,  # format_string
            line_number=14
        )
        
        # greet calls format_string
        storage.create_calls_relationship(
            sample_symbols[2].location_uri,  # greet
            sample_symbols[3].location_uri,  # format_string
            line_number=27
        )
        
        # Test calls from hello_world
        called_by_hello, calling_hello = storage.find_symbol_calls(sample_symbols[0].location_uri)
        assert len(called_by_hello) == 2
        called_names = {c["name"] for c in called_by_hello}
        assert called_names == {"greet", "format_string"}
        assert len(calling_hello) == 0
        
        # Test calls to format_string
        called_by_format, calling_format = storage.find_symbol_calls(sample_symbols[3].location_uri)
        assert len(called_by_format) == 0
        assert len(calling_format) == 2
        caller_names = {c["name"] for c in calling_format}
        assert caller_names == {"hello_world", "greet"}

    def test_execute_cypher(self, storage, sample_symbols):
        """Test executing raw Cypher queries."""
        storage.store_symbols(sample_symbols)
        
        # Simple query
        results = storage.execute_cypher(
            "MATCH (s:Symbol) WHERE s.location_uri CONTAINS 'main.py' RETURN s.name ORDER BY s.name"
        )
        assert len(results) == 3
        assert results[0][0] == "Greeter"
        assert results[1][0] == "greet"
        assert results[2][0] == "hello_world"
        
        # Query with parameters
        results = storage.execute_cypher(
            "MATCH (s:Symbol) WHERE s.kind = $kind RETURN s.name",
            {"kind": "function"}
        )
        assert len(results) == 2
        names = {r[0] for r in results}
        assert names == {"hello_world", "format_string"}

    def test_get_statistics(self, storage, sample_symbols):
        """Test getting database statistics."""
        # Empty database
        stats = storage.get_statistics()
        assert stats["total_symbols"] == 0
        assert stats["total_relationships"] == 0
        assert stats["symbols_by_kind"] == {}
        
        # With data
        storage.store_symbols(sample_symbols)
        storage.create_calls_relationship(
            sample_symbols[0].location_uri,
            sample_symbols[2].location_uri
        )
        
        stats = storage.get_statistics()
        assert stats["total_symbols"] == len(sample_symbols)
        assert stats["total_relationships"] == 1
        assert stats["symbols_by_kind"]["function"] == 2
        assert stats["symbols_by_kind"]["class"] == 2
        assert stats["symbols_by_kind"]["method"] == 1

    def test_symbols_with_none_values(self, storage):
        """Test storing symbols with None values for optional fields."""
        symbol = Symbol(
            name="minimal_func",
            kind="function",
            location_uri="file:///test/minimal.py#L1",
            scope=None,
            signature=None
        )
        
        assert storage.store_symbol(symbol) is True
        
        results = storage.find_symbols_by_name("minimal_func")
        assert len(results) == 1
        assert results[0]["scope"] == ""
        assert results[0]["signature"] == ""

    def test_complex_cypher_queries(self, storage, sample_symbols):
        """Test complex Cypher queries for real-world use cases."""
        storage.store_symbols(sample_symbols)
        
        # Create some relationships
        storage.create_calls_relationship(
            sample_symbols[0].location_uri,  # hello_world
            sample_symbols[2].location_uri   # greet
        )
        storage.create_calls_relationship(
            sample_symbols[2].location_uri,  # greet
            sample_symbols[3].location_uri   # format_string
        )
        
        # Find all functions that are called by methods
        results = storage.execute_cypher("""
            MATCH (m:Symbol {kind: 'method'})-[:CALLS]->(f:Symbol {kind: 'function'})
            RETURN m.name, f.name
        """)
        assert len(results) == 1
        assert results[0][0] == "greet"
        assert results[0][1] == "format_string"
        
        # Find call chains of length 2
        results = storage.execute_cypher("""
            MATCH (a:Symbol)-[:CALLS]->(b:Symbol)-[:CALLS]->(c:Symbol)
            RETURN a.name, b.name, c.name
        """)
        assert len(results) == 1
        assert results[0][0] == "hello_world"
        assert results[0][1] == "greet"
        assert results[0][2] == "format_string"

    def test_file_based_storage(self, temp_db_path):
        """Test file-based storage persistence."""
        # Create and populate database
        storage1 = KuzuStorage(temp_db_path)
        symbol = Symbol(
            name="persistent_func",
            kind="function",
            location_uri="file:///test/persist.py#L10"
        )
        storage1.store_symbol(symbol)
        storage1.close()
        
        # Open again and verify data persists
        storage2 = KuzuStorage(temp_db_path)
        results = storage2.find_symbols_by_name("persistent_func")
        assert len(results) == 1
        assert results[0]["name"] == "persistent_func"
        storage2.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])