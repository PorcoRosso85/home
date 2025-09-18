"""E2E tests for boundary coverage and change sensitivity metrics."""

import shutil
import tempfile

from ...application.calculate_metrics import MetricsCalculator
from ...infrastructure.embedding_service import EmbeddingService
from ...infrastructure.graph_adapter import GraphAdapter
from ...infrastructure.metrics_collector import MetricsCollector


class TestE2EBoundarySensitivity:
    """E2E tests for boundary coverage and change sensitivity metrics."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.graph_adapter = GraphAdapter(self.temp_dir)
        self.embedding_service = EmbeddingService()
        self.metrics_collector = MetricsCollector(self.temp_dir)

        self.calculator = MetricsCalculator(
            self.graph_adapter,
            self.embedding_service,
            self.metrics_collector
        )

        self._setup_test_data()

    def teardown_method(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_test_data(self):
        """Set up test data with boundaries and thresholds."""
        data = self.graph_adapter._load_data()

        # Requirement with boundaries
        data["requirements"]["req_payment"] = {
            "title": "Payment Processing",
            "description": "Process payments with validation",
            "thresholds": {
                "amount": {"min": 1, "max": 10000},
                "timeout": {"min": 100, "max": 5000}
            },
            "constraints": {
                "retry_limit": 3
            },
            "business_rules": [
                {"condition": "amount > 0", "action": "process"},
                {"condition": "timeout < 5000", "action": "accept"}
            ]
        }

        # Tests with boundary coverage
        data["tests"]["test_payment_boundaries"] = {
            "id": "test_payment_boundaries",
            "test_type": "integration",
            "description": "Test payment boundaries",
            "test_cases": [
                {"input_values": {"amount": 0}},     # Below min
                {"input_values": {"amount": 1}},     # At min
                {"input_values": {"amount": 10000}}, # At max
                {"input_values": {"amount": 10001}}, # Above max
                {"input_values": {"timeout": 99}},   # Below min
                {"input_values": {"timeout": 100}},  # At min
                {"input_values": {"timeout": 5000}}, # At max
                {"input_values": {"retry_limit": 3}} # Exact constraint
            ]
        }

        # Mutation test results for change sensitivity
        data["tests"]["test_payment_boundaries"]["mutation_results"] = {
            "threshold_change_amount": {"test_failed": True},
            "threshold_change_timeout": {"test_failed": True},
            "rule_change_0": {"test_failed": False}  # Missing sensitivity
        }

        data["relationships"].append({
            "type": "VERIFIED_BY",
            "from": "req_payment",
            "to": "test_payment_boundaries"
        })

        self.graph_adapter._save_data(data)

    def test_boundary_coverage_complete(self):
        """Test boundary coverage with complete coverage."""
        result = self.calculator.calculate_specific_metric("req_payment", "boundary_coverage")

        assert result.score > 0.8  # Should have good coverage
        assert result.details["boundary_count"] > 0
        assert result.details["covered_count"] > 0

        # Check specific boundary coverage
        coverage = result.details.get("coverage_details", {})
        assert any("amount_min" in k for k in coverage)
        assert any("amount_max" in k for k in coverage)

    def test_boundary_coverage_missing(self):
        """Test boundary coverage with missing test cases."""
        # Create requirement with missing boundary tests
        data = self.graph_adapter._load_data()

        data["requirements"]["req_incomplete"] = {
            "title": "Incomplete Tests",
            "thresholds": {
                "value": {"min": 0, "max": 100}
            }
        }

        data["tests"]["test_incomplete"] = {
            "id": "test_incomplete",
            "test_cases": [
                {"input_values": {"value": 50}}  # Only middle value
            ]
        }

        data["relationships"].append({
            "type": "VERIFIED_BY",
            "from": "req_incomplete",
            "to": "test_incomplete"
        })

        self.graph_adapter._save_data(data)

        result = self.calculator.calculate_specific_metric("req_incomplete", "boundary_coverage")

        assert result.score < 0.5  # Poor coverage
        assert len(result.suggestions) > 0
        assert any("boundary" in s for s in result.suggestions)

    def test_change_sensitivity_good(self):
        """Test change sensitivity with good mutation coverage."""
        result = self.calculator.calculate_specific_metric("req_payment", "change_sensitivity")

        # Should detect some changes but not all
        assert 0.4 < result.score < 0.8
        assert result.details["change_count"] > 0
        assert result.details["sensitive_count"] > 0
        assert result.details["sensitive_count"] < result.details["change_count"]

    def test_change_sensitivity_suggestions(self):
        """Test that change sensitivity provides useful suggestions."""
        result = self.calculator.calculate_specific_metric("req_payment", "change_sensitivity")

        assert len(result.suggestions) > 0
        # Should suggest adding sensitivity for rule changes
        assert any("rule_change" in s for s in result.suggestions)

    def test_combined_boundary_sensitivity_flow(self):
        """Test both metrics together for comprehensive validation."""
        results = self.calculator.calculate_all_metrics("req_payment")

        # Both metrics should be calculated
        assert "boundary_coverage" in results
        assert "change_sensitivity" in results

        # Boundary coverage should be good
        assert results["boundary_coverage"].score > 0.7

        # Change sensitivity should be moderate
        assert 0.3 < results["change_sensitivity"].score < 0.9

        # Should have some suggestions for improvement
        all_suggestions = []
        for result in results.values():
            all_suggestions.extend(result.suggestions)

        assert len(all_suggestions) > 0
