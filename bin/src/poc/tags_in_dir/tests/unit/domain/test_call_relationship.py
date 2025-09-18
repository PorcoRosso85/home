"""
Unit tests for CallRelationship entity and create_call_relationship factory.

This module tests the CallRelationship entity creation with various scenarios
including success cases, error cases, and edge cases.
"""

import pytest
from src.domain.call_relationship import CallRelationship, create_call_relationship


class TestCreateCallRelationship:
    """Test suite for create_call_relationship factory function."""
    
    @pytest.mark.parametrize("test_case", [
        # Test case format: (name, from_uri, to_uri, line_number, expected_error)
        # Success cases
        ("valid_different_uris", "file://a.py#L10", "file://b.py#L20", None, None),
        ("valid_self_recursive", "file://a.py#L10", "file://a.py#L10", None, None),
        ("valid_with_line_number", "file://a.py#L10", "file://b.py#L20", 15, None),
        ("valid_line_zero", "file://a.py#L10", "file://b.py#L20", 0, None),
        ("valid_large_line", "file://a.py#L10", "file://b.py#L20", 999999, None),
        ("valid_self_recursive_with_line", "file://func.py#L5", "file://func.py#L5", 7, None),
        
        # Error cases - empty URIs
        ("error_empty_from_uri", "", "file://b.py#L20", None, "from_location_uri cannot be empty"),
        ("error_empty_to_uri", "file://a.py#L10", "", None, "to_location_uri cannot be empty"),
        ("error_both_empty", "", "", None, "from_location_uri cannot be empty"),
        
        # Error cases - invalid line numbers
        ("error_negative_line", "file://a.py#L10", "file://b.py#L20", -1, "line_number must be non-negative, got -1"),
        ("error_negative_line_large", "file://a.py#L10", "file://b.py#L20", -999, "line_number must be non-negative, got -999"),
    ], ids=lambda x: x[0])
    def test_create_call_relationship_scenarios(self, test_case):
        """Test various scenarios for creating CallRelationship instances."""
        name, from_uri, to_uri, line_number, expected_error = test_case
        
        if expected_error:
            # Test error cases
            with pytest.raises(ValueError) as exc_info:
                create_call_relationship(from_uri, to_uri, line_number)
            assert expected_error in str(exc_info.value)
        else:
            # Test success cases
            relationship = create_call_relationship(from_uri, to_uri, line_number)
            assert relationship.from_location_uri == from_uri
            assert relationship.to_location_uri == to_uri
            assert relationship.line_number == line_number
            assert isinstance(relationship, CallRelationship)
    
    def test_call_relationship_immutability(self):
        """Test that CallRelationship instances are immutable."""
        relationship = create_call_relationship(
            "file://a.py#L10",
            "file://b.py#L20",
            15
        )
        
        # Attempt to modify attributes should raise error
        with pytest.raises(AttributeError):
            relationship.from_location_uri = "file://c.py#L30"
        
        with pytest.raises(AttributeError):
            relationship.to_location_uri = "file://d.py#L40"
        
        with pytest.raises(AttributeError):
            relationship.line_number = 25
    
    def test_line_number_type_validation(self):
        """Test that line_number must be an integer."""
        # Test with float
        with pytest.raises(ValueError) as exc_info:
            create_call_relationship(
                "file://a.py#L10",
                "file://b.py#L20",
                15.5  # type: ignore
            )
        assert "line_number must be an integer, got float" in str(exc_info.value)
        
        # Test with string
        with pytest.raises(ValueError) as exc_info:
            create_call_relationship(
                "file://a.py#L10",
                "file://b.py#L20",
                "15"  # type: ignore
            )
        assert "line_number must be an integer, got str" in str(exc_info.value)
    
    def test_various_uri_formats(self):
        """Test that various URI formats are accepted."""
        test_uris = [
            ("file://simple.py#L1", "file://other.py#L2"),
            ("file:///absolute/path/file.py#L10", "file:///another/path.py#L20"),
            ("file://path/with/many/dirs/file.py#L100", "file://short.py#L1"),
            ("file://path with spaces/file.py#L1", "file://normal.py#L2"),
            ("file://特殊文字.py#L1", "file://unicode.py#L2"),
        ]
        
        for from_uri, to_uri in test_uris:
            relationship = create_call_relationship(from_uri, to_uri)
            assert relationship.from_location_uri == from_uri
            assert relationship.to_location_uri == to_uri
    
    def test_none_line_number_handling(self):
        """Test explicit None vs omitted line_number parameter."""
        # Explicit None
        rel1 = create_call_relationship(
            "file://a.py#L10",
            "file://b.py#L20",
            None
        )
        assert rel1.line_number is None
        
        # Omitted parameter (default)
        rel2 = create_call_relationship(
            "file://a.py#L10",
            "file://b.py#L20"
        )
        assert rel2.line_number is None
        
        # Both should be equal
        assert rel1 == rel2
    
    def test_equality_and_hashing(self):
        """Test that CallRelationship instances can be compared and hashed."""
        rel1 = create_call_relationship("file://a.py#L10", "file://b.py#L20", 15)
        rel2 = create_call_relationship("file://a.py#L10", "file://b.py#L20", 15)
        rel3 = create_call_relationship("file://a.py#L10", "file://b.py#L20", 16)
        
        # Test equality
        assert rel1 == rel2
        assert rel1 != rel3
        
        # Test hashing (should be able to use in sets/dicts)
        relationship_set = {rel1, rel2, rel3}
        assert len(relationship_set) == 2  # rel1 and rel2 are equal, so only 2 unique