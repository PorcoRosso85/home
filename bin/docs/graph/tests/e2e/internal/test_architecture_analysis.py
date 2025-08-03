"""E2E tests for architecture analysis functionality."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typing import Dict, Any, List

from flake_graph.architecture_analyzer import (
    analyze_architecture,
    ArchitectureAnalysisResult,
    ArchitectureHealth,
    ArchitectureIssue,
    ArchitectureMetrics
)


class TestArchitectureAnalysis:
    """Test suite for architecture analysis functionality."""
    
    def test_vss_only_analysis(self):
        """Test VSS-only analysis when similarity is not available."""
        # Arrange
        flake_path = "/test/flake"
        query = "test query"
        flakes = [
            {"id": "flake1", "content": "Test flake 1 content"},
            {"id": "flake2", "content": "Test flake 2 content"},
            {"id": "flake3", "content": "Test flake 3 content"}
        ]
        db_path = "/test/db.db"
        
        # Mock VSS results
        mock_vss_results = [
            {"id": "flake1", "content": "Test flake 1 content", "score": 0.9},
            {"id": "flake2", "content": "Test flake 2 content", "score": 0.85},
            {"id": "flake3", "content": "Test flake 3 content", "score": 0.6}
        ]
        
        # Mock similarity to fail (tool not found)
        mock_similarity_error = {
            "ok": False,
            "error": "Tool 'similarity-python' is not installed or not in PATH"
        }
        
        with patch('flake_graph.vss_adapter.search_similar_flakes', 
                  return_value=mock_vss_results) as mock_vss, \
             patch('flake_graph.similarity_adapter.detect_code_similarity',
                  return_value=mock_similarity_error) as mock_ast:
            
            # Act
            result = analyze_architecture(flake_path, query, flakes, db_path)
            
            # Assert
            mock_vss.assert_called_once_with(query, flakes, db_path, limit=10)
            mock_ast.assert_called_once_with(flake_path, "python")
            
            assert isinstance(result, dict)
            assert "architecture_health" in result
            health = result["architecture_health"]
            
            # Check health structure
            assert isinstance(health["score"], float)
            assert 0.0 <= health["score"] <= 1.0
            assert isinstance(health["issues"], list)
            assert isinstance(health["metrics"], dict)
            
            # Check metrics
            metrics = health["metrics"]
            assert metrics["vss_score"] == (0.9 + 0.85 + 0.6) / 3  # Average of scores
            assert metrics["ast_score"] is None  # AST analysis failed
            assert metrics["duplication_ratio"] == 2 / 3  # 2 high similarity scores > 0.8
            
            # Check issues
            issues = health["issues"]
            # Should have duplication issue from VSS and AST failure issue
            duplication_issues = [i for i in issues if i["type"] == "duplication"]
            assert len(duplication_issues) == 1
            assert duplication_issues[0]["severity"] == "high"
            assert len(duplication_issues[0]["affected_files"]) == 2  # flake1 and flake2
            
            ast_failure_issues = [i for i in issues if "AST analysis failed" in i["description"]]
            assert len(ast_failure_issues) == 1
            assert ast_failure_issues[0]["severity"] == "low"
    
    def test_combined_analysis(self):
        """Test combined VSS+AST analysis with mocks."""
        # Arrange
        flake_path = "/test/flake"
        query = "test query"
        flakes = [
            {"id": "module1", "content": "Module 1 functionality"},
            {"id": "module2", "content": "Module 2 functionality"},
            {"id": "module3", "content": "Module 3 functionality"}
        ]
        db_path = "/test/db.db"
        
        # Mock VSS results with moderate similarity
        mock_vss_results = [
            {"id": "module1", "content": "Module 1 functionality", "score": 0.7},
            {"id": "module2", "content": "Module 2 functionality", "score": 0.65},
            {"id": "module3", "content": "Module 3 functionality", "score": 0.5}
        ]
        
        # Mock AST results with some code duplication
        mock_ast_success = {
            "ok": True,
            "matches": [
                {
                    "file1": "module1.py",
                    "file2": "module2.py",
                    "similarity": 88.5,
                    "details": "- Similar class structures\n- Shared utility functions"
                },
                {
                    "file1": "module2.py",
                    "file2": "module3.py",
                    "similarity": 65.0,
                    "details": "- Some shared patterns\n- Could benefit from refactoring"
                }
            ],
            "total_files": 5,
            "language": "python"
        }
        
        with patch('flake_graph.vss_adapter.search_similar_flakes',
                  return_value=mock_vss_results) as mock_vss, \
             patch('flake_graph.similarity_adapter.detect_code_similarity',
                  return_value=mock_ast_success) as mock_ast:
            
            # Act
            result = analyze_architecture(flake_path, query, flakes, db_path, language="python")
            
            # Assert
            mock_vss.assert_called_once_with(query, flakes, db_path, limit=10)
            mock_ast.assert_called_once_with(flake_path, "python")
            
            health = result["architecture_health"]
            metrics = health["metrics"]
            
            # Check both scores are present
            assert metrics["vss_score"] is not None
            assert metrics["ast_score"] is not None
            assert metrics["vss_score"] == (0.7 + 0.65 + 0.5) / 3
            assert metrics["ast_score"] == pytest.approx((88.5 + 65.0) / 2 / 100.0)
            
            # Check duplication ratio is set from AST (since VSS found no duplicates)
            # VSS: 0/3 (no scores > 0.8)
            # AST: 1/5 (one match > 85%)
            assert metrics["duplication_ratio"] == 1/5  # Only AST duplication, not averaged
            
            # Check issues
            issues = health["issues"]
            
            # Should have code duplication issue from AST
            code_dup_issues = [i for i in issues if i["type"] == "duplication" and "88.5%" in i["description"]]
            assert len(code_dup_issues) == 1
            assert code_dup_issues[0]["severity"] == "high"
            assert set(code_dup_issues[0]["affected_files"]) == {"module1.py", "module2.py"}
            
            # Should have inconsistency issue for partial matches
            inconsistency_issues = [i for i in issues if i["type"] == "inconsistency" and "partially similar" in i["description"]]
            assert len(inconsistency_issues) == 1
            assert inconsistency_issues[0]["severity"] == "medium"
            
            # Health score should be reduced due to issues
            assert health["score"] < 1.0
    
    def test_error_handling(self):
        """Test that analysis continues when one component fails."""
        # Arrange
        flake_path = "/test/flake"
        query = "test query"
        flakes = [
            {"id": "service1", "content": "Service 1 implementation"},
            {"id": "service2", "content": "Service 2 implementation"}
        ]
        db_path = "/test/db.db"
        
        # Mock VSS to raise an exception
        def vss_exception(*args, **kwargs):
            raise Exception("VSS database connection failed")
        
        # Mock AST to succeed
        mock_ast_success = {
            "ok": True,
            "matches": [
                {
                    "file1": "service1.py",
                    "file2": "service2.py",
                    "similarity": 75.0,
                    "details": "- Similar service patterns"
                }
            ],
            "total_files": 3,
            "language": "python"
        }
        
        with patch('flake_graph.vss_adapter.search_similar_flakes',
                  side_effect=vss_exception) as mock_vss, \
             patch('flake_graph.similarity_adapter.detect_code_similarity',
                  return_value=mock_ast_success) as mock_ast:
            
            # Act
            result = analyze_architecture(flake_path, query, flakes, db_path)
            
            # Assert
            mock_vss.assert_called_once_with(query, flakes, db_path, limit=10)
            mock_ast.assert_called_once_with(flake_path, "python")
            
            health = result["architecture_health"]
            metrics = health["metrics"]
            
            # VSS score should be None due to exception
            assert metrics["vss_score"] is None
            # AST score should be calculated
            assert metrics["ast_score"] == 0.75
            
            # Check issues
            issues = health["issues"]
            
            # Should have VSS failure issue
            vss_failure_issues = [i for i in issues if "VSS analysis failed" in i["description"]]
            assert len(vss_failure_issues) == 1
            assert vss_failure_issues[0]["severity"] == "medium"
            assert "database connection failed" in vss_failure_issues[0]["description"]
            
            # Should still have inconsistency issue from AST
            partial_match_issues = [i for i in issues if "partially similar" in i["description"]]
            assert len(partial_match_issues) == 1
            
            # Health score should still be calculated
            assert isinstance(health["score"], float)
            assert 0.0 <= health["score"] <= 1.0
            
            # Verify error doesn't prevent analysis completion
            assert metrics["consistency_score"] < 1.0  # Reduced due to partial matches
            assert metrics["coupling_index"] == 0.75  # Set from AST score