"""Metric 5: Semantic alignment - functional implementation."""

import numpy as np
from typing import Union, Protocol

from infrastructure.errors import ValidationError
from domain.metrics.base import MetricInput, MetricResult


class EmbeddingServiceProtocol(Protocol):
    """Protocol for embedding service dependency."""
    
    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        ...
    
    def calculate_similarity(self, embedding1: list[float], embedding2: list[float]) -> Union[float, ValidationError]:
        """Calculate similarity between embeddings."""
        ...


def get_metric_info() -> dict[str, str]:
    """Get metric metadata."""
    return {
        "name": "semantic_alignment",
        "description": "Semantic alignment - similarity between requirements and test descriptions"
    }


def validate_input(input_data: MetricInput) -> bool:
    """Check if we have descriptions and embeddings."""
    return bool(
        input_data.requirement_id and
        input_data.requirement_data and
        input_data.test_data and
        input_data.requirement_data.get("description") and
        input_data.test_data.get("descriptions") is not None  # Allow empty list
    )


def _calculate_cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    a = np.array(vec1)
    b = np.array(vec2)

    # Compute cosine similarity
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


def _extract_key_concepts(text: str) -> list[str]:
    """Extract key concepts from text for comparison."""
    # Simple keyword extraction (in real implementation, use NLP)
    keywords = []

    # Common testing keywords to look for
    test_keywords = [
        "verify", "validate", "check", "ensure", "test",
        "assert", "confirm", "should", "must", "require"
    ]

    # Domain keywords (would be dynamic in real implementation)
    domain_keywords = [
        "payment", "user", "authentication", "security",
        "threshold", "limit", "timeout", "error", "success"
    ]

    text_lower = text.lower()

    for keyword in test_keywords + domain_keywords:
        if keyword in text_lower:
            keywords.append(keyword)

    return keywords


def _calculate_alignment_scores(
    requirement_desc: str,
    test_descriptions: list[dict],
    req_embedding: list[float] | None,
    embedding_service: EmbeddingServiceProtocol | None
) -> list[dict[str, Union[str, float]]]:
    """Calculate alignment scores for each test description."""
    alignment_scores = []

    for test_desc in test_descriptions:
        if isinstance(test_desc, dict):
            desc_text = test_desc.get("description", "")
            test_embedding = test_desc.get("embedding")

            if req_embedding and test_embedding:
                # Use embedding similarity
                similarity = _calculate_cosine_similarity(req_embedding, test_embedding)
            elif embedding_service and desc_text:
                # Generate embeddings on the fly if service is available
                req_emb = req_embedding or embedding_service.generate_embedding(requirement_desc)
                test_emb = embedding_service.generate_embedding(desc_text)
                similarity_result = embedding_service.calculate_similarity(req_emb, test_emb)
                
                # Check if it's a ValidationError by checking the type field
                if isinstance(similarity_result, dict) and similarity_result.get("type") == "ValidationError":
                    similarity = 0.0
                else:
                    similarity = similarity_result
            else:
                # Fallback to keyword matching
                req_keywords = set(_extract_key_concepts(requirement_desc))
                test_keywords = set(_extract_key_concepts(desc_text))

                if req_keywords:
                    overlap = len(req_keywords & test_keywords)
                    similarity = overlap / len(req_keywords)
                else:
                    similarity = 0.0

            alignment_scores.append({
                "test_description": desc_text,
                "similarity": similarity
            })

    return alignment_scores


def _generate_suggestions(
    score: float,
    requirement_desc: str,
    test_descriptions: list[dict]
) -> list[str]:
    """Generate suggestions based on alignment score."""
    suggestions: list[str] = []
    
    if score < 0.7:
        suggestions.append(
            "Test descriptions have low semantic alignment with requirement. "
            "Update test descriptions to better reflect the requirement's intent."
        )

        # Find concepts in requirement not in tests
        req_concepts = set(_extract_key_concepts(requirement_desc))
        all_test_concepts = set()
        for test_desc in test_descriptions:
            if isinstance(test_desc, dict):
                desc_text = test_desc.get("description", "")
                all_test_concepts.update(_extract_key_concepts(desc_text))

        missing_concepts = req_concepts - all_test_concepts
        if missing_concepts:
            suggestions.append(
                f"Consider adding tests for these concepts: {', '.join(missing_concepts)}"
            )

    return suggestions


def calculate_semantic_alignment_metric(
    input_data: MetricInput,
    embedding_service: EmbeddingServiceProtocol | None = None
) -> Union[MetricResult, ValidationError]:
    """Calculate semantic alignment score."""
    if not validate_input(input_data):
        return ValidationError(
            type="ValidationError",
            message="Invalid input data for semantic alignment metric",
            field="input_data",
            value=str(input_data),
            constraint="Must have requirement_id, requirement_data with description, and test_data with descriptions",
            suggestion="Ensure the input contains valid requirement and test data with descriptions"
        )

    requirement_desc = input_data.requirement_data.get("description", "")
    test_descriptions = input_data.test_data.get("descriptions", [])

    metric_info = get_metric_info()

    if not test_descriptions:
        return MetricResult(
            metric_name=metric_info["name"],
            requirement_id=input_data.requirement_id,
            score=0.0,
            details={
                "requirement_description": requirement_desc,
                "test_count": 0,
                "alignment_scores": [],
            },
            suggestions=["No test descriptions found. Add meaningful descriptions to tests."]
        )

    # Calculate alignment scores
    req_embedding = input_data.requirement_data.get("embedding")
    alignment_scores = _calculate_alignment_scores(
        requirement_desc,
        test_descriptions,
        req_embedding,
        embedding_service
    )

    # Calculate overall score (average of best alignments)
    if alignment_scores:
        best_scores = sorted(
            [s["similarity"] for s in alignment_scores],
            reverse=True
        )[:3]  # Top 3 tests
        score = sum(best_scores) / len(best_scores)
    else:
        score = 0.0

    # Generate suggestions
    suggestions = _generate_suggestions(score, requirement_desc, test_descriptions)

    return MetricResult(
        metric_name=metric_info["name"],
        requirement_id=input_data.requirement_id,
        score=score,
        details={
            "requirement_description": requirement_desc,
            "test_count": len(test_descriptions),
            "alignment_scores": alignment_scores,
            "average_alignment": score,
        },
        suggestions=suggestions
    )