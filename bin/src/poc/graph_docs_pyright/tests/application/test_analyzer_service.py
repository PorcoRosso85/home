"""Tests for the analyzer service application layer."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

from graph_docs.application.analyzer_service import (
    AnalyzerService,
    AnalysisRequest,
    AnalysisResult,
    DualDBAnalysisResult,
    AnalysisError
)
from graph_docs.domain.entities import QueryResult, DualQueryResult
from graph_docs.application.interfaces.repository import IDualKuzuRepository


class TestAnalyzerService:
    """Test suite for AnalyzerService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        repo = Mock(spec=IDualKuzuRepository)
        return repo

    @pytest.fixture
    def mock_pyright_analyzer(self):
        """Create a mock Pyright analyzer."""
        with patch('graph_docs.application.analyzer_service.PyrightAnalyzer') as mock:
            analyzer_instance = Mock()
            mock.return_value = analyzer_instance
            yield analyzer_instance

    @pytest.fixture
    def analyzer_service(self, mock_repository):
        """Create an AnalyzerService instance with mocked dependencies."""
        return AnalyzerService(repository=mock_repository)

    def test_init_creates_service_with_repository(self, mock_repository):
        """Test that AnalyzerService initializes with a repository."""
        service = AnalyzerService(repository=mock_repository)
        assert service.repository == mock_repository

    def test_analyze_single_db_success(self, analyzer_service, mock_repository):
        """Test successful single database analysis."""
        # Arrange
        request = AnalysisRequest(
            db1_path="/path/to/db1",
            db2_path="/path/to/db2",
            query="MATCH (n) RETURN n",
            target_db="db1"
        )
        
        expected_result = QueryResult(
            source="db1",
            columns=["n"],
            rows=[["node1"], ["node2"]],
            error=None
        )
        
        mock_repository.connect.return_value = {"success": True, "message": "Connected"}
        mock_repository.query_single.return_value = expected_result
        
        # Act
        result = analyzer_service.analyze(request)
        
        # Assert
        assert isinstance(result, AnalysisResult)
        assert result.ok is True
        assert result.single_result == expected_result
        assert result.dual_result is None
        assert result.error is None
        
        mock_repository.connect.assert_called_once()
        mock_repository.query_single.assert_called_once_with("db1", request.query)
        mock_repository.disconnect.assert_called_once()

    def test_analyze_dual_db_success(self, analyzer_service, mock_repository):
        """Test successful dual database analysis."""
        # Arrange
        request = AnalysisRequest(
            db1_path="/path/to/db1",
            db2_path="/path/to/db2",
            query="MATCH (n) RETURN n",
            target_db=None  # Both databases
        )
        
        db1_result = QueryResult(
            source="db1",
            columns=["n"],
            rows=[["node1"]],
            error=None
        )
        
        db2_result = QueryResult(
            source="db2",
            columns=["n"],
            rows=[["node2"]],
            error=None
        )
        
        expected_dual_result = DualQueryResult(
            db1_result=db1_result,
            db2_result=db2_result,
            combined=None
        )
        
        mock_repository.connect.return_value = {"success": True, "message": "Connected"}
        mock_repository.query_both.return_value = expected_dual_result
        
        # Act
        result = analyzer_service.analyze(request)
        
        # Assert
        assert isinstance(result, AnalysisResult)
        assert result.ok is True
        assert result.single_result is None
        assert result.dual_result == expected_dual_result
        assert result.error is None
        
        mock_repository.connect.assert_called_once()
        mock_repository.query_both.assert_called_once_with(request.query)
        mock_repository.disconnect.assert_called_once()

    def test_analyze_connection_failure(self, analyzer_service, mock_repository):
        """Test analysis when database connection fails."""
        # Arrange
        request = AnalysisRequest(
            db1_path="/path/to/db1",
            db2_path="/path/to/db2",
            query="MATCH (n) RETURN n",
            target_db="db1"
        )
        
        mock_repository.connect.return_value = {
            "error": "Failed to connect",
            "details": "Connection refused"
        }
        
        # Act
        result = analyzer_service.analyze(request)
        
        # Assert
        assert isinstance(result, AnalysisResult)
        assert result.ok is False
        assert result.single_result is None
        assert result.dual_result is None
        assert result.error == "Failed to connect: Connection refused"
        
        mock_repository.connect.assert_called_once()
        mock_repository.query_single.assert_not_called()
        mock_repository.disconnect.assert_not_called()

    def test_analyze_query_error(self, analyzer_service, mock_repository):
        """Test analysis when query execution fails."""
        # Arrange
        request = AnalysisRequest(
            db1_path="/path/to/db1",
            db2_path="/path/to/db2",
            query="INVALID QUERY",
            target_db="db1"
        )
        
        error_result = QueryResult(
            source="db1",
            columns=[],
            rows=[],
            error="Syntax error in query"
        )
        
        mock_repository.connect.return_value = {"success": True, "message": "Connected"}
        mock_repository.query_single.return_value = error_result
        
        # Act
        result = analyzer_service.analyze(request)
        
        # Assert
        assert isinstance(result, AnalysisResult)
        assert result.ok is False
        assert result.single_result == error_result
        assert result.error == "Query failed: Syntax error in query"
        
        mock_repository.disconnect.assert_called_once()

    def test_analyze_parallel_queries_success(self, analyzer_service, mock_repository):
        """Test successful parallel query analysis."""
        # Arrange
        request = AnalysisRequest(
            db1_path="/path/to/db1",
            db2_path="/path/to/db2",
            query=None,
            target_db=None,
            db1_query="MATCH (n:User) RETURN n",
            db2_query="MATCH (p:Product) RETURN p"
        )
        
        db1_result = QueryResult(
            source="db1",
            columns=["n"],
            rows=[["user1"]],
            error=None
        )
        
        db2_result = QueryResult(
            source="db2",
            columns=["p"],
            rows=[["product1"]],
            error=None
        )
        
        expected_dual_result = DualQueryResult(
            db1_result=db1_result,
            db2_result=db2_result,
            combined=None
        )
        
        mock_repository.connect.return_value = {"success": True, "message": "Connected"}
        mock_repository.query_parallel.return_value = expected_dual_result
        
        # Act
        result = analyzer_service.analyze_parallel(request)
        
        # Assert
        assert isinstance(result, AnalysisResult)
        assert result.ok is True
        assert result.dual_result == expected_dual_result
        
        mock_repository.connect.assert_called_once()
        mock_repository.query_parallel.assert_called_once_with(
            request.db1_query,
            request.db2_query
        )
        mock_repository.disconnect.assert_called_once()

    def test_analyze_with_pyright_integration(self, analyzer_service, mock_repository, mock_pyright_analyzer):
        """Test analysis with Pyright code analysis integration."""
        # Arrange
        request = AnalysisRequest(
            db1_path="/path/to/db1",
            db2_path="/path/to/db2",
            query="MATCH (n) RETURN n",
            target_db="db1",
            enable_pyright=True,
            workspace_path="/workspace"
        )
        
        query_result = QueryResult(
            source="db1",
            columns=["n"],
            rows=[["node1"]],
            error=None
        )
        
        pyright_result = {
            "ok": True,
            "diagnostics": [],
            "summary": {"errors": 0, "warnings": 0},
            "files": []
        }
        
        mock_repository.connect.return_value = {"success": True, "message": "Connected"}
        mock_repository.query_single.return_value = query_result
        mock_pyright_analyzer.analyze.return_value = pyright_result
        
        # Act
        result = analyzer_service.analyze_with_pyright(request)
        
        # Assert
        assert isinstance(result, DualDBAnalysisResult)
        assert result.ok is True
        assert result.query_result.single_result == query_result
        assert result.pyright_result == pyright_result
        
        mock_pyright_analyzer.analyze.assert_called_once()

    def test_get_database_info_success(self, analyzer_service, mock_repository):
        """Test successful retrieval of database information."""
        # Arrange
        db1_path = "/path/to/db1"
        db2_path = "/path/to/db2"
        
        db1_tables = QueryResult(
            source="db1",
            columns=["name", "type"],
            rows=[["User", "NODE"], ["Product", "NODE"]],
            error=None
        )
        
        db2_tables = QueryResult(
            source="db2",
            columns=["name", "type"],
            rows=[["Order", "NODE"], ["CONTAINS", "REL"]],
            error=None
        )
        
        mock_repository.connect.return_value = {"success": True, "message": "Connected"}
        mock_repository.query_single.side_effect = [db1_tables, db2_tables]
        
        # Act
        result = analyzer_service.get_database_info(db1_path, db2_path)
        
        # Assert
        assert result["ok"] is True
        assert result["db1_tables"] == db1_tables
        assert result["db2_tables"] == db2_tables
        assert "error" not in result
        
        mock_repository.connect.assert_called_once()
        assert mock_repository.query_single.call_count == 2
        mock_repository.disconnect.assert_called_once()

    def test_create_local_database_success(self, analyzer_service, mock_repository):
        """Test successful local database creation."""
        # Arrange
        local_path = "/path/to/local"
        
        mock_repository.init_local_db.return_value = {
            "success": True,
            "message": "Local DB initialized"
        }
        
        # Act
        result = analyzer_service.create_local_database(local_path)
        
        # Assert
        assert result["ok"] is True
        assert result["message"] == "Local DB initialized"
        assert "error" not in result
        
        mock_repository.init_local_db.assert_called_once_with(local_path)

    def test_create_relations_success(self, analyzer_service, mock_repository):
        """Test successful relation creation."""
        # Arrange
        relations = [
            {
                "from_id": 1,
                "from_type": "User",
                "to_id": 100,
                "to_type": "Product",
                "rel_type": "OWNS"
            }
        ]
        
        create_result = QueryResult(
            source="local",
            columns=["success_count", "error_count"],
            rows=[[1, 0]],
            error=None
        )
        
        mock_repository.create_relations.return_value = create_result
        
        # Act
        result = analyzer_service.create_relations(relations)
        
        # Assert
        assert result["ok"] is True
        assert result["result"] == create_result
        assert "error" not in result
        
        mock_repository.create_relations.assert_called_once_with(relations)

    def test_import_csv_data_success(self, analyzer_service, mock_repository):
        """Test successful CSV data import."""
        # Arrange
        target = "db1"
        table_name = "User"
        csv_path = "/path/to/users.csv"
        
        import_result = QueryResult(
            source="db1",
            columns=["rows_copied"],
            rows=[["10 tuples have been copied"]],
            error=None
        )
        
        mock_repository.copy_from.return_value = import_result
        
        # Act
        result = analyzer_service.import_csv_data(target, table_name, csv_path)
        
        # Assert
        assert result["ok"] is True
        assert result["result"] == import_result
        assert "error" not in result
        
        mock_repository.copy_from.assert_called_once_with(target, table_name, csv_path)

    def test_analyze_with_invalid_target_db(self, analyzer_service):
        """Test analysis with invalid target database."""
        # Arrange
        request = AnalysisRequest(
            db1_path="/path/to/db1",
            db2_path="/path/to/db2",
            query="MATCH (n) RETURN n",
            target_db="invalid_db"
        )
        
        # Act
        result = analyzer_service.analyze(request)
        
        # Assert
        assert result.ok is False
        assert result.error == "Invalid target_db: invalid_db. Must be 'db1', 'db2', or None"

    def test_analyze_parallel_missing_queries(self, analyzer_service):
        """Test parallel analysis with missing queries."""
        # Arrange
        request = AnalysisRequest(
            db1_path="/path/to/db1",
            db2_path="/path/to/db2",
            query=None,
            target_db=None,
            db1_query=None,  # Missing
            db2_query="MATCH (p:Product) RETURN p"
        )
        
        # Act
        result = analyzer_service.analyze_parallel(request)
        
        # Assert
        assert result.ok is False
        assert result.error == "Both db1_query and db2_query must be provided for parallel analysis"

    def test_repository_initialization_error(self, mock_repository):
        """Test service behavior when repository is None."""
        # Arrange
        service = AnalyzerService(repository=None)
        request = AnalysisRequest(
            db1_path="/path/to/db1",
            db2_path="/path/to/db2",
            query="MATCH (n) RETURN n",
            target_db="db1"
        )
        
        # Act
        result = service.analyze(request)
        
        # Assert
        assert result.ok is False
        assert result.error == "Repository not initialized"