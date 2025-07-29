"""
Duplicate Detection Specification

Pure business logic for duplicate detection rules.
No external dependencies, only pure functions defining the rules.
"""
from typing import List, Optional, Tuple


class DuplicateDetectionSpec:
    """Specification for duplicate detection business rules."""
    
    # Business rule: Similarity threshold for considering requirements as duplicates
    SIMILARITY_THRESHOLD = 0.95
    
    @staticmethod
    def is_duplicate(similarity: float) -> bool:
        """
        Determine if a similarity score indicates a duplicate.
        
        Business Rule: Requirements with similarity >= 0.95 are considered duplicates.
        
        Args:
            similarity: Cosine similarity score between 0 and 1
            
        Returns:
            True if similarity meets the threshold, False otherwise
        """
        return similarity >= DuplicateDetectionSpec.SIMILARITY_THRESHOLD
    
    @staticmethod
    def should_provide_feedback(duplicates: List[Tuple[str, float]]) -> bool:
        """
        Determine if feedback should be provided for found duplicates.
        
        Business Rule: Always provide feedback when duplicates are found.
        
        Args:
            duplicates: List of (requirement_id, similarity_score) tuples
            
        Returns:
            True if duplicates list is not empty, False otherwise
        """
        return len(duplicates) > 0
    
    @staticmethod
    def format_feedback_message(
        new_requirement: str,
        duplicates: List[Tuple[str, float]]
    ) -> str:
        """
        Format user feedback message for duplicate detection.
        
        Business Rule: Provide clear feedback listing all potential duplicates.
        
        Args:
            new_requirement: The requirement being added
            duplicates: List of (requirement_id, similarity_score) tuples
            
        Returns:
            Formatted feedback message
        """
        if not duplicates:
            return ""
        
        message = f"Potential duplicates found for '{new_requirement}':\n"
        for req_id, similarity in duplicates:
            percentage = similarity * 100
            message += f"  - {req_id} (similarity: {percentage:.1f}%)\n"
        
        return message.strip()
    
    @staticmethod
    def get_similarity_category(similarity: float) -> str:
        """
        Categorize similarity score for reporting.
        
        Business Rules:
        - >= 0.99: Exact match
        - >= 0.95: High similarity (duplicate)
        - >= 0.80: Medium similarity
        - < 0.80: Low similarity
        
        Args:
            similarity: Cosine similarity score between 0 and 1
            
        Returns:
            Category name
        """
        if similarity >= 0.99:
            return "exact_match"
        elif similarity >= 0.95:
            return "high_similarity"
        elif similarity >= 0.80:
            return "medium_similarity"
        else:
            return "low_similarity"