"""E2E tests for existence and reachability metrics."""

import shutil
import tempfile

from ...application.calculate_metrics import MetricsCalculator
from ...infrastructure.embedding_service import EmbeddingService
from ...infrastructure.graph_adapter import GraphAdapter
from ...infrastructure.metrics_collector import MetricsCollector


class TestE2EExistenceReachability:
    """E2E tests for existence and reachability metrics."""

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

        # Set up test data
        self._setup_test_requirements()

    def teardown_method(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_test_requirements(self):
        """Set up test requirements and tests."""
        data = self.graph_adapter._load_data()

        # Requirement with tests (good)
        data["requirements"]["req_good"] = {
            "title": "Good Requirement",
            "description": "This requirement has proper tests"
        }

        data["tests"]["test_good_1"] = {
            "id": "test_good_1",
            "test_type": "unit",
            "description": "Test for good requirement"
        }

        data["relationships"].append({
            "type": "VERIFIED_BY",
            "from": "req_good",
            "to": "test_good_1"
        })

        # Requirement without tests (bad)
        data["requirements"]["req_no_tests"] = {
            "title": "Untested Requirement",
            "description": "This requirement has no tests"
        }

        # Requirement with circular dependencies
        data["requirements"]["req_circular"] = {
            "title": "Circular Requirement",
            "description": "This requirement has circular test dependencies"
        }

        data["tests"]["test_circular_1"] = {"id": "test_circular_1"}
        data["tests"]["test_circular_2"] = {"id": "test_circular_2"}
        data["tests"]["test_circular_3"] = {"id": "test_circular_3"}

        data["relationships"].extend([
            {"type": "VERIFIED_BY", "from": "req_circular", "to": "test_circular_1"},
            {"type": "DEPENDS_ON", "from": "test_circular_1", "to": "test_circular_2"},
            {"type": "DEPENDS_ON", "from": "test_circular_2", "to": "test_circular_3"},
            {"type": "DEPENDS_ON", "from": "test_circular_3", "to": "test_circular_1"}
        ])

        self.graph_adapter._save_data(data)

    def test_existence_metric_with_tests(self):
        """Test existence metric for requirement with tests."""
        result = self.calculator.calculate_specific_metric("req_good", "existence")

        assert result.score == 1.0
        assert result.details["has_tests"] is True
        assert result.details["test_count"] > 0
        assert len(result.suggestions) == 0

    def test_existence_metric_without_tests(self):
        """Test existence metric for requirement without tests."""
        result = self.calculator.calculate_specific_metric("req_no_tests", "existence")

        assert result.score == 0.0
        assert result.details["has_tests"] is False
        assert result.details["test_count"] == 0
        assert len(result.suggestions) > 0
        assert "No tests found" in result.suggestions[0]

    def test_reachability_metric_no_dependencies(self):
        """Test reachability metric for tests without dependencies."""
        result = self.calculator.calculate_specific_metric("req_good", "reachability")

        assert result.score == 1.0
        assert result.details["has_circular_dependencies"] is False
        assert len(result.suggestions) == 0

    def test_reachability_metric_circular_dependencies(self):
        """Test reachability metric for tests with circular dependencies."""
        # Need to update test data with dependency info
        data = self.graph_adapter._load_data()
        data["tests"]["test_circular_1"]["dependencies"] = {
            "test_circular_1": ["test_circular_2"],
            "test_circular_2": ["test_circular_3"],
            "test_circular_3": ["test_circular_1"]
        }
        self.graph_adapter._save_data(data)

        result = self.calculator.calculate_specific_metric("req_circular", "reachability")

        assert result.score == 0.0
        assert result.details["has_circular_dependencies"] is True
        assert len(result.suggestions) > 0
        assert "Circular dependency" in result.suggestions[0]

    def test_combined_metrics_flow(self):
        """Test calculating both metrics in sequence."""
        # Calculate all metrics for a good requirement
        results = self.calculator.calculate_all_metrics("req_good")

        assert "existence" in results
        assert "reachability" in results
        assert results["existence"].score == 1.0
        assert results["reachability"].score == 1.0

        # Calculate for problematic requirement
        results = self.calculator.calculate_all_metrics("req_no_tests")

        assert results["existence"].score == 0.0
        # Reachability should handle missing tests gracefully
