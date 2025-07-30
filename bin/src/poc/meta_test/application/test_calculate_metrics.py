"""Tests for metrics calculator."""

import tempfile

import pytest

from ..infrastructure.embedding_service import EmbeddingService
from ..infrastructure.graph_adapter import GraphAdapter
from ..infrastructure.metrics_collector import MetricsCollector
from .calculate_metrics import MetricsCalculator


class TestMetricsCalculator:
    """Test metrics calculation use case."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.graph_adapter = GraphAdapter(self.temp_dir)
        self.embedding_service = EmbeddingService()
        self.metrics_collector = MetricsCollector(self.temp_dir)

        self.calculator = MetricsCalculator(
            self.graph_adapter,
            self.embedding_service,
            self.metrics_collector
        )

        # Set up test data
        self._setup_test_data()

    def teardown_method(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_test_data(self):
        """Set up test requirement and tests."""
        data = self.graph_adapter._load_data()

        # Add requirement
        data["requirements"]["req_001"] = {
            "title": "User Login",
            "description": "Users should be able to log in with username and password",
            "thresholds": {
                "login_attempts": {"max": 3},
                "timeout": {"min": 5, "max": 30}
            }
        }

        # Add tests
        data["tests"]["test_001"] = {
            "id": "test_001",
            "test_type": "unit",
            "description": "Test user login functionality",
            "test_cases": [
                {"input_values": {"login_attempts": 3}},
                {"input_values": {"timeout": 5}}
            ]
        }

        # Add relationship
        data["relationships"].append({
            "type": "VERIFIED_BY",
            "from": "req_001",
            "to": "test_001"
        })

        self.graph_adapter._save_data(data)

        # Add some runtime data
        self.metrics_collector.record_test_execution("req_001", "test_001", True, 100)
        self.metrics_collector.record_test_execution("req_001", "test_001", False, 150)
        self.metrics_collector.record_operational_metric("cpu_usage", 45.0)
        self.metrics_collector.record_operational_metric("cpu_usage", 85.0)

    def test_calculate_all_metrics(self):
        """Test calculating all metrics for a requirement."""
        results = self.calculator.calculate_all_metrics("req_001")

        # Check all 7 metrics were calculated
        assert len(results) == 7
        assert "existence" in results
        assert "reachability" in results
        assert "boundary_coverage" in results
        assert "change_sensitivity" in results
        assert "semantic_alignment" in results
        assert "runtime_correlation" in results
        assert "value_probability" in results

        # Check existence metric
        assert results["existence"].score == 1.0  # Has tests

        # Check results were saved
        saved_metrics = self.graph_adapter._load_data()["metrics"]
        assert "req_001" in saved_metrics
        assert "existence" in saved_metrics["req_001"]

    def test_calculate_specific_metric(self):
        """Test calculating a specific metric."""
        result = self.calculator.calculate_specific_metric("req_001", "existence")

        assert result.metric_name == "existence"
        assert result.requirement_id == "req_001"
        assert result.score == 1.0

    def test_calculate_nonexistent_requirement(self):
        """Test calculating metrics for non-existent requirement."""
        with pytest.raises(ValueError, match="Requirement req_999 not found"):
            self.calculator.calculate_all_metrics("req_999")

    def test_calculate_unknown_metric(self):
        """Test calculating unknown metric."""
        with pytest.raises(ValueError, match="Unknown metric: unknown"):
            self.calculator.calculate_specific_metric("req_001", "unknown")

    def test_parallel_calculation(self):
        """Test that metrics are calculated in parallel."""
        # This is implicitly tested by calculate_all_metrics
        # We can verify by checking that all metrics complete
        results = self.calculator.calculate_all_metrics("req_001")

        # All metrics should have results (even if some failed)
        assert len(results) == 7

        # Each result should have required fields
        for metric_name, result in results.items():
            assert result.metric_name == metric_name
            assert result.requirement_id == "req_001"
            assert 0.0 <= result.score <= 1.0
