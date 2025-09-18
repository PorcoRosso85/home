"""
Unit tests for the Symbol entity and create_symbol factory function.

This module tests the behavior of Symbol creation, focusing on:
- Valid URI patterns with file:// scheme and line numbers
- Error cases for invalid URIs
- Edge cases for line numbers
- Property-based testing for valid inputs
"""

import pytest
from hypothesis import given, strategies as st
from typing import List, Tuple
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.domain.symbol import create_symbol


class TestSymbolCreation:
    """Test suite for Symbol entity creation."""
    
    def test_create_valid_symbol(self):
        """Test creating a symbol with valid basic parameters."""
        symbol = create_symbol(
            name="test_function",
            kind="function",
            location_uri="file:///home/user/test.py#L42"
        )
        
        assert symbol.name == "test_function"
        assert symbol.kind == "function"
        assert symbol.location_uri == "file:///home/user/test.py#L42"
        assert symbol.scope is None
        assert symbol.signature is None
    
    def test_create_symbol_with_all_fields(self):
        """Test creating a symbol with all optional fields populated."""
        symbol = create_symbol(
            name="TestClass.test_method",
            kind="method",
            location_uri="file:///path/to/file.py#L100",
            scope="TestClass:class",
            signature="(self, arg1, arg2)"
        )
        
        assert symbol.name == "TestClass.test_method"
        assert symbol.kind == "method"
        assert symbol.location_uri == "file:///path/to/file.py#L100"
        assert symbol.scope == "TestClass:class"
        assert symbol.signature == "(self, arg1, arg2)"
    
    @given(
        name=st.text(min_size=1, max_size=100),
        kind=st.sampled_from(["function", "class", "method", "variable", "module"]),
        path=st.text(min_size=1, max_size=200).filter(lambda x: "/" not in x and "\\" not in x),
        line_num=st.integers(min_value=1, max_value=999999)
    )
    def test_create_symbol_property_based(self, name, kind, path, line_num):
        """Property-based test for valid symbol creation."""
        location_uri = f"file:///home/test/{path}#L{line_num}"
        
        symbol = create_symbol(
            name=name,
            kind=kind,
            location_uri=location_uri
        )
        
        assert symbol.name == name
        assert symbol.kind == kind
        assert symbol.location_uri == location_uri
        assert str(line_num) in symbol.location_uri


class TestSymbolValidation:
    """Test suite for Symbol validation errors."""
    
    # Table-driven tests for invalid URI patterns
    @pytest.mark.parametrize("invalid_uri,expected_error", [
        ("", "location_uri cannot be empty"),
        ("http://example.com/file.py#L10", "location_uri must start with 'file://'"),
        ("https://example.com/file.py#L10", "location_uri must start with 'file://'"),
        ("ftp://server/file.py#L10", "location_uri must start with 'file://'"),
        ("file.py#L10", "location_uri must start with 'file://'"),
        ("/absolute/path/file.py#L10", "location_uri must start with 'file://'"),
        ("./relative/path/file.py#L10", "location_uri must start with 'file://'"),
        ("file:///path/to/file.py", "location_uri must contain line number"),
        ("file:///path/to/file.py#", "location_uri must contain line number"),
        ("file:///path/to/file.py#L", "Invalid line number format"),
        ("file:///path/to/file.py#Labc", "Invalid line number format"),
        ("file:///path/to/file.py#L-5", "Line number must be non-negative"),
        ("file:///path/to/file.py#Line10", "Invalid line number format"),
        ("file:///path/to/file.py:10", "location_uri must contain line number"),
    ])
    def test_invalid_location_uri(self, invalid_uri: str, expected_error: str):
        """Test various invalid location_uri patterns."""
        with pytest.raises(ValueError) as exc_info:
            create_symbol(
                name="test",
                kind="function",
                location_uri=invalid_uri
            )
        
        assert expected_error in str(exc_info.value)
    
    def test_missing_location_uri(self):
        """Test that None location_uri raises appropriate error."""
        with pytest.raises(ValueError) as exc_info:
            create_symbol(
                name="test",
                kind="function",
                location_uri=None  # type: ignore
            )
        
        assert "location_uri cannot be empty" in str(exc_info.value)
    
    def test_edge_case_line_zero(self):
        """Test that line number 0 is accepted (some editors use 0-based indexing)."""
        symbol = create_symbol(
            name="test",
            kind="function",
            location_uri="file:///path/to/file.py#L0"
        )
        
        assert symbol.location_uri == "file:///path/to/file.py#L0"
    
    def test_edge_case_large_line_number(self):
        """Test very large line numbers are accepted."""
        symbol = create_symbol(
            name="test",
            kind="function",
            location_uri="file:///path/to/file.py#L999999"
        )
        
        assert symbol.location_uri == "file:///path/to/file.py#L999999"
    
    def test_windows_style_paths(self):
        """Test that Windows-style paths with backslashes work correctly."""
        # Windows paths in file:// URIs use forward slashes
        symbol = create_symbol(
            name="test",
            kind="function",
            location_uri="file:///C:/Users/test/file.py#L10"
        )
        
        assert symbol.location_uri == "file:///C:/Users/test/file.py#L10"
    
    def test_uri_with_special_characters(self):
        """Test URIs with special characters in the path."""
        uris_to_test = [
            "file:///path/with%20spaces/file.py#L10",
            "file:///path/with-dashes/file.py#L10",
            "file:///path/with_underscores/file.py#L10",
            "file:///path/with.dots/file.py#L10",
        ]
        
        for uri in uris_to_test:
            symbol = create_symbol(
                name="test",
                kind="function",
                location_uri=uri
            )
            assert symbol.location_uri == uri


class TestSymbolBehavior:
    """Test the behavior of Symbol instances after creation."""
    
    def test_symbol_immutability_enforcement(self):
        """Test that Symbol acts as an immutable value object."""
        symbol = create_symbol(
            name="original",
            kind="function",
            location_uri="file:///test.py#L1"
        )
        
        # Symbol is frozen, so attempting to modify attributes should raise an error
        with pytest.raises(AttributeError):
            symbol.name = "modified"
        
        with pytest.raises(AttributeError):
            symbol.location_uri = "file:///other.py#L2"
        
        # Verify the original values remain unchanged
        assert symbol.name == "original"
        assert symbol.location_uri == "file:///test.py#L1"
    
    def test_symbol_equality(self):
        """Test that symbols with same data are equal."""
        symbol1 = create_symbol(
            name="test_func",
            kind="function",
            location_uri="file:///test.py#L10",
            scope="module",
            signature="(arg1, arg2)"
        )
        
        symbol2 = create_symbol(
            name="test_func",
            kind="function",
            location_uri="file:///test.py#L10",
            scope="module",
            signature="(arg1, arg2)"
        )
        
        assert symbol1 == symbol2
        assert hash(symbol1) == hash(symbol2)
    
    def test_symbol_inequality(self):
        """Test that symbols with different data are not equal."""
        base_args = {
            "name": "test_func",
            "kind": "function",
            "location_uri": "file:///test.py#L10"
        }
        
        symbol1 = create_symbol(**base_args)
        
        # Test inequality with different name
        symbol2 = create_symbol(**{**base_args, "name": "other_func"})
        assert symbol1 != symbol2
        
        # Test inequality with different location
        symbol3 = create_symbol(**{**base_args, "location_uri": "file:///test.py#L20"})
        assert symbol1 != symbol3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])