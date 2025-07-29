"""
Fast tests for duplicate detection business rules.

These tests verify pure business logic without any external dependencies.
Execution time should be <1ms per test.
"""
import pytest
from typing import List, Tuple

from specs.duplicate_detection_spec import DuplicateDetectionSpec


class TestDuplicateDetectionRules:
    """Test duplicate detection business rules."""
    
    @pytest.mark.parametrize("similarity,expected", [
        # Exact match
        (1.00, True),
        # Above threshold
        (0.98, True),
        (0.96, True),
        # At threshold
        (0.95, True),
        # Below threshold
        (0.94, False),
        (0.90, False),
        (0.80, False),
        (0.50, False),
        (0.00, False),
    ])
    def test_is_duplicate_threshold_rules(self, similarity: float, expected: bool):
        """Test similarity threshold rules for duplicate detection."""
        result = DuplicateDetectionSpec.is_duplicate(similarity)
        assert result == expected
    
    @pytest.mark.parametrize("duplicates,expected", [
        # Has duplicates - should provide feedback
        ([("req_001", 0.98)], True),
        ([("req_001", 0.95), ("req_002", 0.96)], True),
        ([("req_001", 0.99), ("req_002", 0.98), ("req_003", 0.95)], True),
        # No duplicates - no feedback
        ([], False),
    ])
    def test_should_provide_feedback_rules(
        self, 
        duplicates: List[Tuple[str, float]], 
        expected: bool
    ):
        """Test feedback generation rules."""
        result = DuplicateDetectionSpec.should_provide_feedback(duplicates)
        assert result == expected
    
    def test_format_feedback_message_with_duplicates(self):
        """Test feedback message formatting with duplicates."""
        new_req = "User authentication must be secure"
        duplicates = [
            ("req_001", 0.98),
            ("req_002", 0.95),
        ]
        
        message = DuplicateDetectionSpec.format_feedback_message(new_req, duplicates)
        
        assert "Potential duplicates found" in message
        assert "User authentication must be secure" in message
        assert "req_001 (similarity: 98.0%)" in message
        assert "req_002 (similarity: 95.0%)" in message
    
    def test_format_feedback_message_no_duplicates(self):
        """Test feedback message formatting with no duplicates."""
        message = DuplicateDetectionSpec.format_feedback_message("New requirement", [])
        assert message == ""
    
    @pytest.mark.parametrize("similarity,expected_category", [
        # Exact match
        (1.00, "exact_match"),
        (0.99, "exact_match"),
        # High similarity (duplicate)
        (0.98, "high_similarity"),
        (0.95, "high_similarity"),
        # Medium similarity
        (0.94, "medium_similarity"),
        (0.80, "medium_similarity"),
        # Low similarity
        (0.79, "low_similarity"),
        (0.50, "low_similarity"),
        (0.00, "low_similarity"),
    ])
    def test_similarity_category_rules(self, similarity: float, expected_category: str):
        """Test similarity categorization rules."""
        category = DuplicateDetectionSpec.get_similarity_category(similarity)
        assert category == expected_category
    
    def test_similarity_threshold_constant(self):
        """Test that similarity threshold is set correctly."""
        assert DuplicateDetectionSpec.SIMILARITY_THRESHOLD == 0.95
    
    def test_edge_cases(self):
        """Test edge cases for duplicate detection."""
        # Test boundary values
        assert DuplicateDetectionSpec.is_duplicate(0.9500001) == True
        assert DuplicateDetectionSpec.is_duplicate(0.9499999) == False
        
        # Test with exactly threshold value
        assert DuplicateDetectionSpec.is_duplicate(0.95) == True