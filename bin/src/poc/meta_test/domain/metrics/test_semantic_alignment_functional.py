"""Tests for semantic alignment functional implementation."""

import pytest
from typing import Union

from domain.metrics.base import MetricInput, MetricResult
from domain.metrics.semantic_alignment_functional import (
    get_metric_info,
    validate_input,
    calculate_semantic_alignment_metric,
    EmbeddingServiceProtocol
)
from infrastructure.errors import ValidationError


class MockEmbeddingService:
    """Mock embedding service for testing."""
    
    def generate_embedding(self, text: str) -> list[float]:
        """Generate mock embedding."""
        # Simple deterministic embedding based on text length
        return [float(len(text) % 10) / 10] * 10
    
    def calculate_similarity(self, embedding1: list[float], embedding2: list[float]) -> Union[float, dict]:
        """Calculate mock similarity."""
        if len(embedding1) != len(embedding2):
            return {
                "type": "ValidationError",
                "message": "Embeddings must have same dimension",
                "field": "embeddings",
                "value": f"embedding1 length: {len(embedding1)}, embedding2 length: {len(embedding2)}",
                "constraint": "equal_length",
                "suggestion": "Ensure both embeddings have the same number of dimensions"
            }
        # Simple similarity based on difference (cosine similarity would be better)
        # Return a value between 0 and 1
        diff = abs(embedding1[0] - embedding2[0])
        return 1.0 - min(diff, 1.0)


def test_get_metric_info():
    """Test metric info retrieval."""
    info = get_metric_info()
    assert info["name"] == "semantic_alignment"
    assert "similarity between requirements and test descriptions" in info["description"]


def test_validate_input_valid():
    """Test input validation with valid data."""
    input_data = MetricInput(
        requirement_id="REQ001",
        requirement_data={
            "description": "User should be able to login"
        },
        test_data={
            "descriptions": [{"description": "Test login functionality"}]
        }
    )
    assert validate_input(input_data) is True


def test_validate_input_missing_requirement_id():
    """Test input validation with missing requirement ID."""
    input_data = MetricInput(
        requirement_id="",
        requirement_data={"description": "Some description"},
        test_data={"descriptions": []}
    )
    assert validate_input(input_data) is False


def test_validate_input_missing_description():
    """Test input validation with missing description."""
    input_data = MetricInput(
        requirement_id="REQ001",
        requirement_data={},
        test_data={"descriptions": []}
    )
    assert validate_input(input_data) is False


def test_calculate_with_invalid_input():
    """Test calculation with invalid input."""
    input_data = MetricInput(
        requirement_id="",
        requirement_data={},
        test_data={}
    )
    
    result = calculate_semantic_alignment_metric(input_data)
    
    # ValidationError is a TypedDict, check by type field
    assert isinstance(result, dict)
    assert result.get("type") == "ValidationError"
    assert "Invalid input data" in result.get("message", "")


def test_calculate_with_no_test_descriptions():
    """Test calculation when no test descriptions exist."""
    input_data = MetricInput(
        requirement_id="REQ001",
        requirement_data={"description": "User authentication required"},
        test_data={"descriptions": []}
    )
    
    result = calculate_semantic_alignment_metric(input_data)
    
    assert result.metric_name == "semantic_alignment"
    assert result.score == 0.0
    assert result.details["test_count"] == 0
    assert "No test descriptions found" in result.suggestions[0]


def test_calculate_with_embeddings():
    """Test calculation with pre-computed embeddings."""
    input_data = MetricInput(
        requirement_id="REQ001",
        requirement_data={
            "description": "User authentication required",
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        },
        test_data={
            "descriptions": [
                {
                    "description": "Test user login",
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]  # Identical embedding
                },
                {
                    "description": "Test invalid credentials",
                    "embedding": [0.0, 0.1, 0.2, 0.3, 0.4]  # Different embedding
                }
            ]
        }
    )
    
    result = calculate_semantic_alignment_metric(input_data)
    
    assert result.metric_name == "semantic_alignment"
    assert result.score > 0.0
    assert result.details["test_count"] == 2
    assert len(result.details["alignment_scores"]) == 2


def test_calculate_with_embedding_service():
    """Test calculation with embedding service."""
    input_data = MetricInput(
        requirement_id="REQ001",
        requirement_data={
            "description": "User authentication required"
        },
        test_data={
            "descriptions": [
                {"description": "Test user login"},
                {"description": "Test password validation"}
            ]
        }
    )
    
    embedding_service = MockEmbeddingService()
    result = calculate_semantic_alignment_metric(input_data, embedding_service)
    
    assert result.metric_name == "semantic_alignment"
    assert result.score >= 0.0
    assert result.details["test_count"] == 2


def test_calculate_keyword_fallback():
    """Test calculation with keyword matching fallback."""
    input_data = MetricInput(
        requirement_id="REQ001",
        requirement_data={
            "description": "User must authenticate with valid credentials"
        },
        test_data={
            "descriptions": [
                {"description": "Verify user authentication process"},
                {"description": "Check payment processing"}
            ]
        }
    )
    
    result = calculate_semantic_alignment_metric(input_data)
    
    assert result.metric_name == "semantic_alignment"
    assert result.score > 0.0  # Should have some alignment due to "user" and "authenticate"
    assert len(result.details["alignment_scores"]) == 2


def test_suggestions_for_low_alignment():
    """Test that suggestions are generated for low alignment scores."""
    input_data = MetricInput(
        requirement_id="REQ001",
        requirement_data={
            "description": "Payment processing with security validation"
        },
        test_data={
            "descriptions": [
                {"description": "Test user interface"},
                {"description": "Check button colors"}
            ]
        }
    )
    
    result = calculate_semantic_alignment_metric(input_data)
    
    assert result.score < 0.7
    assert len(result.suggestions) > 0
    assert "low semantic alignment" in result.suggestions[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])