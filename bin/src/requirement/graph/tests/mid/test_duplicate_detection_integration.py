"""
Mid-layer integration tests for duplicate detection.

Tests the integration between duplicate detection business logic and search services.
Uses in-memory mock services to ensure fast execution (<10ms per test).
"""
import pytest
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from specs.duplicate_detection_spec import DuplicateDetectionSpec


@dataclass
class SearchResult:
    """Simple search result representation."""
    requirement_id: str
    text: str
    similarity: float


class InMemorySearchService:
    """Mock search service that simulates VSS behavior with in-memory data."""
    
    def __init__(self):
        # Simulate pre-indexed requirements with their embeddings
        self.similarity_map: Dict[str, Dict[str, float]] = {}
        self.requirements: Dict[str, str] = {}
    
    def add_requirement(self, req_id: str, text: str):
        """Add a requirement to the in-memory database."""
        self.requirements[req_id] = text
    
    def set_similarity(self, query: str, req_id: str, similarity: float):
        """Pre-configure similarity scores for testing."""
        if query not in self.similarity_map:
            self.similarity_map[query] = {}
        self.similarity_map[query][req_id] = similarity
    
    def find_similar(self, query: str, threshold: float = 0.0) -> List[SearchResult]:
        """
        Find similar requirements based on pre-configured similarity scores.
        
        Args:
            query: The requirement text to search for
            threshold: Minimum similarity score to include in results
            
        Returns:
            List of search results with similarity scores
        """
        results = []
        
        # Return pre-configured similarities for the query
        if query in self.similarity_map:
            for req_id, similarity in self.similarity_map[query].items():
                if similarity >= threshold and req_id in self.requirements:
                    results.append(SearchResult(
                        requirement_id=req_id,
                        text=self.requirements[req_id],
                        similarity=similarity
                    ))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results


class DuplicateDetectionService:
    """Service that orchestrates duplicate detection using search service."""
    
    def __init__(self, search_service: InMemorySearchService):
        self.search_service = search_service
    
    def detect_duplicates(self, new_requirement: str) -> List[Tuple[str, float]]:
        """
        Detect potential duplicate requirements.
        
        Args:
            new_requirement: The new requirement text to check
            
        Returns:
            List of (requirement_id, similarity) tuples for potential duplicates
        """
        # Search for similar requirements
        results = self.search_service.find_similar(
            new_requirement, 
            threshold=0.0  # Get all results, filter later
        )
        
        # Filter by duplicate threshold
        duplicates = []
        for result in results:
            if DuplicateDetectionSpec.is_duplicate(result.similarity):
                duplicates.append((result.requirement_id, result.similarity))
        
        return duplicates
    
    def check_and_provide_feedback(self, new_requirement: str) -> Optional[str]:
        """
        Check for duplicates and provide feedback if needed.
        
        Args:
            new_requirement: The new requirement text to check
            
        Returns:
            Feedback message if duplicates found, None otherwise
        """
        duplicates = self.detect_duplicates(new_requirement)
        
        if DuplicateDetectionSpec.should_provide_feedback(duplicates):
            return DuplicateDetectionSpec.format_feedback_message(
                new_requirement, duplicates
            )
        
        return None


class TestDuplicateDetectionIntegration:
    """Integration tests for duplicate detection workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.search_service = InMemorySearchService()
        self.duplicate_service = DuplicateDetectionService(self.search_service)
        
        # Add test requirements
        self.search_service.add_requirement("req_001", "ユーザー認証機能を実装する")
        self.search_service.add_requirement("req_002", "ユーザ認証を実装する")
        self.search_service.add_requirement("req_003", "認証機能を追加する")
        self.search_service.add_requirement("req_004", "ログイン機能を実装する")
    
    def test_duplicate_detection_flow(self):
        """Test the complete flow: search → detect → feedback."""
        start_time = time.time()
        
        # Configure similarity scores for test scenario
        query = "ユーザー認証機能"
        self.search_service.set_similarity(query, "req_001", 1.0)    # Exact match
        self.search_service.set_similarity(query, "req_002", 0.98)   # High similarity
        self.search_service.set_similarity(query, "req_003", 0.85)   # Below threshold
        self.search_service.set_similarity(query, "req_004", 0.70)   # Low similarity
        
        # Execute duplicate detection
        duplicates = self.duplicate_service.detect_duplicates(query)
        
        # Verify results
        assert len(duplicates) == 2  # Only req_001 and req_002 meet threshold
        assert ("req_001", 1.0) in duplicates
        assert ("req_002", 0.98) in duplicates
        
        # Get feedback
        feedback = self.duplicate_service.check_and_provide_feedback(query)
        assert feedback is not None
        assert "Potential duplicates found" in feedback
        assert "req_001 (similarity: 100.0%)" in feedback
        assert "req_002 (similarity: 98.0%)" in feedback
        
        # Ensure test runs fast
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        assert execution_time < 10, f"Test took {execution_time:.2f}ms, expected <10ms"
    
    def test_empty_database_scenario(self):
        """Test duplicate detection with empty database."""
        start_time = time.time()
        
        # Create service with empty database
        empty_search = InMemorySearchService()
        empty_duplicate = DuplicateDetectionService(empty_search)
        
        # Try to detect duplicates
        duplicates = empty_duplicate.detect_duplicates("新しい要件")
        
        # Should return empty list
        assert duplicates == []
        
        # Should not provide feedback
        feedback = empty_duplicate.check_and_provide_feedback("新しい要件")
        assert feedback is None
        
        # Ensure test runs fast
        execution_time = (time.time() - start_time) * 1000
        assert execution_time < 10
    
    def test_no_duplicates_found_scenario(self):
        """Test when no duplicates are found (all similarities below threshold)."""
        start_time = time.time()
        
        # Configure all similarities below threshold
        query = "完全に新しい要件"
        self.search_service.set_similarity(query, "req_001", 0.80)
        self.search_service.set_similarity(query, "req_002", 0.70)
        self.search_service.set_similarity(query, "req_003", 0.60)
        self.search_service.set_similarity(query, "req_004", 0.50)
        
        # Execute duplicate detection
        duplicates = self.duplicate_service.detect_duplicates(query)
        
        # Should find no duplicates
        assert duplicates == []
        
        # Should not provide feedback
        feedback = self.duplicate_service.check_and_provide_feedback(query)
        assert feedback is None
        
        # Ensure test runs fast
        execution_time = (time.time() - start_time) * 1000
        assert execution_time < 10
    
    def test_exact_match_scenario(self):
        """Test exact match (similarity = 1.0) scenario."""
        start_time = time.time()
        
        # Configure exact match
        query = "ユーザー認証機能を実装する"
        self.search_service.set_similarity(query, "req_001", 1.0)
        
        # Execute duplicate detection
        duplicates = self.duplicate_service.detect_duplicates(query)
        
        # Should find one exact match
        assert len(duplicates) == 1
        assert duplicates[0] == ("req_001", 1.0)
        
        # Check feedback
        feedback = self.duplicate_service.check_and_provide_feedback(query)
        assert feedback is not None
        assert "req_001 (similarity: 100.0%)" in feedback
        
        # Ensure test runs fast
        execution_time = (time.time() - start_time) * 1000
        assert execution_time < 10
    
    @pytest.mark.parametrize("similarity_distribution,expected_count", [
        # All above threshold
        ({"req_001": 0.99, "req_002": 0.98, "req_003": 0.97, "req_004": 0.96}, 4),
        # Mix of above and below
        ({"req_001": 0.99, "req_002": 0.94, "req_003": 0.96, "req_004": 0.80}, 2),
        # All at threshold boundary
        ({"req_001": 0.95, "req_002": 0.95, "req_003": 0.95, "req_004": 0.95}, 4),
        # All just below threshold
        ({"req_001": 0.94, "req_002": 0.94, "req_003": 0.94, "req_004": 0.94}, 0),
        # Varying distributions
        ({"req_001": 1.0, "req_002": 0.50, "req_003": 0.30, "req_004": 0.10}, 1),
    ])
    def test_different_similarity_distributions(
        self, 
        similarity_distribution: Dict[str, float], 
        expected_count: int
    ):
        """Test duplicate detection with different similarity score distributions."""
        start_time = time.time()
        
        # Configure similarities
        query = "テスト要件"
        for req_id, similarity in similarity_distribution.items():
            self.search_service.set_similarity(query, req_id, similarity)
        
        # Execute duplicate detection
        duplicates = self.duplicate_service.detect_duplicates(query)
        
        # Verify expected count
        assert len(duplicates) == expected_count
        
        # Verify all returned duplicates meet threshold
        for req_id, similarity in duplicates:
            assert similarity >= DuplicateDetectionSpec.SIMILARITY_THRESHOLD
        
        # Ensure test runs fast
        execution_time = (time.time() - start_time) * 1000
        assert execution_time < 10
    
    def test_integration_with_business_rules(self):
        """Test that integration properly uses business rule specifications."""
        # Test uses exact threshold from spec
        assert self.duplicate_service.detect_duplicates.__doc__ is not None
        
        # Configure boundary test
        query = "境界値テスト"
        self.search_service.set_similarity(query, "req_001", 0.95)     # At threshold
        self.search_service.set_similarity(query, "req_002", 0.9499)   # Just below
        
        duplicates = self.duplicate_service.detect_duplicates(query)
        
        # Only req_001 should be detected
        assert len(duplicates) == 1
        assert duplicates[0][0] == "req_001"
    
    def test_search_service_ordering(self):
        """Test that search results are properly ordered by similarity."""
        query = "順序テスト"
        self.search_service.set_similarity(query, "req_001", 0.85)
        self.search_service.set_similarity(query, "req_002", 0.95)
        self.search_service.set_similarity(query, "req_003", 0.99)
        self.search_service.set_similarity(query, "req_004", 0.90)
        
        results = self.search_service.find_similar(query)
        
        # Verify descending order
        assert results[0].requirement_id == "req_003"  # 0.99
        assert results[1].requirement_id == "req_002"  # 0.95
        assert results[2].requirement_id == "req_004"  # 0.90
        assert results[3].requirement_id == "req_001"  # 0.85