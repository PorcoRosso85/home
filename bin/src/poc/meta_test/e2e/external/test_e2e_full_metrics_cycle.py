"""E2E test for full metrics calculation and learning cycle."""

import shutil
import tempfile
from pathlib import Path

from ...application.calculate_metrics import MetricsCalculator
from ...application.improve_suggestions import ImprovementSuggestionGenerator
from ...application.learn_from_runtime import RuntimeLearner
from ...infrastructure.cypher_writer import CypherWriter
from ...infrastructure.embedding_service import EmbeddingService
from ...infrastructure.graph_adapter import GraphAdapter
from ...infrastructure.logger import get_logger
from ...infrastructure.metrics_collector import MetricsCollector

logger = get_logger(__name__)


class TestE2EFullMetricsCycle:
    """E2E test for complete metrics lifecycle."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)

        # Initialize all components
        self.graph_adapter = GraphAdapter(str(self.data_dir / "graph"))
        self.embedding_service = EmbeddingService()
        self.metrics_collector = MetricsCollector(str(self.data_dir / "metrics"))
        self.cypher_writer = CypherWriter(str(self.data_dir / "cypher"))

        self.calculator = MetricsCalculator(
            self.graph_adapter,
            self.embedding_service,
            self.metrics_collector
        )

        self.suggestion_generator = ImprovementSuggestionGenerator()
        self.learner = RuntimeLearner(
            self.graph_adapter,
            self.metrics_collector,
            self.cypher_writer
        )

        self._setup_comprehensive_test_data()

    def teardown_method(self):
        """Clean up."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_comprehensive_test_data(self):
        """Set up comprehensive test data for all metrics."""
        data = self.graph_adapter._load_data()

        # Comprehensive requirement
        data["requirements"]["req_user_auth"] = {
            "title": "User Authentication",
            "description": "Secure user authentication with proper validation and security measures",
            "thresholds": {
                "password_length": {"min": 8, "max": 128},
                "login_attempts": {"max": 3},
                "session_timeout": {"min": 300, "max": 3600}
            },
            "business_rules": [
                {"condition": "password_complexity", "action": "enforce"},
                {"condition": "2fa_enabled", "action": "require_for_admin"}
            ]
        }

        # Multiple tests with varying quality
        data["tests"]["test_auth_login"] = {
            "id": "test_auth_login",
            "test_type": "integration",
            "description": "Test user login with valid credentials and security checks",
            "test_cases": [
                {"input_values": {"password_length": 7}},   # Below min
                {"input_values": {"password_length": 8}},   # At min
                {"input_values": {"password_length": 64}},  # Middle
                {"input_values": {"password_length": 128}}, # At max
                {"input_values": {"login_attempts": 3}},    # At max
                {"input_values": {"login_attempts": 4}},    # Above max
            ]
        }

        data["tests"]["test_auth_timeout"] = {
            "id": "test_auth_timeout",
            "test_type": "integration",
            "description": "Verify session timeout behavior",
            "test_cases": [
                {"input_values": {"session_timeout": 300}},
                {"input_values": {"session_timeout": 3600}}
            ]
        }

        # Add relationships
        data["relationships"].extend([
            {"type": "VERIFIED_BY", "from": "req_user_auth", "to": "test_auth_login"},
            {"type": "VERIFIED_BY", "from": "req_user_auth", "to": "test_auth_timeout"}
        ])

        self.graph_adapter._save_data(data)

        # Add runtime data for learning metrics
        self._add_runtime_data()

    def _add_runtime_data(self):
        """Add runtime data for metrics 6 and 7."""
        # Test execution history
        for i in range(10):
            self.metrics_collector.record_test_execution(
                "req_user_auth",
                "test_auth_login",
                passed=(i % 3 != 0),  # Fail every 3rd test
                duration_ms=100 + i * 10
            )

        # Operational metrics (correlate with test results)
        for i in range(10):
            self.metrics_collector.record_operational_metric(
                "auth_success_rate",
                0.95 if i % 3 != 0 else 0.85  # Lower when test fails
            )
            self.metrics_collector.record_operational_metric(
                "response_time_ms",
                150 if i % 3 != 0 else 250  # Higher when test fails
            )

        # Business metrics
        for i in range(10):
            self.metrics_collector.record_business_metric(
                "user_satisfaction",
                4.5 if i % 3 != 0 else 4.0
            )
            self.metrics_collector.record_business_metric(
                "security_incidents",
                0 if i % 3 != 0 else 1
            )

        # Add an incident
        self.metrics_collector.record_incident(
            "inc_auth_001",
            "medium",
            "Authentication service timeout",
            ["req_user_auth"]
        )

    def test_full_metrics_calculation(self):
        """Test calculating all 7 metrics."""
        results = self.calculator.calculate_all_metrics("req_user_auth")

        # All 7 metrics should be calculated
        assert len(results) == 7

        # Check each metric
        assert results["existence"].score == 1.0  # Has tests
        assert results["reachability"].score == 1.0  # No circular deps
        assert results["boundary_coverage"].score > 0.5  # Some boundaries covered
        assert results["semantic_alignment"].score > 0.5  # Descriptions match

        # Runtime metrics should have values
        assert 0.0 <= results["runtime_correlation"].score <= 1.0
        assert 0.0 <= results["value_probability"].score <= 1.0

        # Should have saved results
        saved_data = self.graph_adapter._load_data()
        assert "req_user_auth" in saved_data["metrics"]
        assert len(saved_data["metrics"]["req_user_auth"]) == 7

    def test_improvement_suggestions_generation(self):
        """Test generating improvement suggestions."""
        # Calculate metrics first
        all_results = {"req_user_auth": self.calculator.calculate_all_metrics("req_user_auth")}

        # Generate suggestions
        suggestions = self.suggestion_generator.generate_suggestions(all_results)

        # Should have suggestions for metrics below threshold
        assert len(suggestions) > 0

        # Generate improvement plan
        plan = self.suggestion_generator.generate_improvement_plan(all_results)

        assert "immediate" in plan
        assert "quick_wins" in plan
        assert "planned" in plan
        assert "backlog" in plan

        # Generate report
        report = self.suggestion_generator.format_suggestion_report(plan)
        assert "Test Quality Improvement Plan" in report

    def test_learning_cycle(self):
        """Test learning from runtime data."""
        # Run learning cycle
        results = self.learner.run_learning_cycle(["req_user_auth"])

        assert "req_user_auth" in results
        assert "error" not in results["req_user_auth"]

        result = results["req_user_auth"]
        assert "updates" in result
        assert "runtime_correlation" in result["updates"]
        assert "value_probability" in result["updates"]

        # Check that values changed from default
        assert result["updates"]["runtime_correlation"] != 0.5
        assert result["updates"]["value_probability"] != 0.5

        # Check Cypher files were created
        cypher_files = list((self.data_dir / "cypher").glob("*.cypher"))
        assert len(cypher_files) > 0

    def test_metric_persistence_and_history(self):
        """Test that metrics are persisted and history is maintained."""
        # Calculate metrics twice
        results1 = self.calculator.calculate_all_metrics("req_user_auth")

        # Modify some data
        self.metrics_collector.record_test_execution(
            "req_user_auth", "test_auth_login", False, 500
        )

        results2 = self.calculator.calculate_all_metrics("req_user_auth")

        # Get history
        history = self.graph_adapter.get_metric_history("req_user_auth", "existence")
        assert len(history) > 0

        # Values should be tracked
        assert history[-1]["score"] == 1.0

    def test_end_to_end_workflow(self):
        """Test complete workflow from calculation to learning to suggestions."""
        # Step 1: Calculate initial metrics
        logger.info("Step 1: Calculating initial metrics...")
        initial_results = self.calculator.calculate_all_metrics("req_user_auth")

        # Step 2: Generate initial suggestions
        logger.info("Step 2: Generating initial suggestions...")
        all_results = {"req_user_auth": initial_results}
        initial_plan = self.suggestion_generator.generate_improvement_plan(all_results)

        # Step 3: Simulate runtime and collect more data
        logger.info("Step 3: Simulating runtime...")
        for i in range(5):
            self.metrics_collector.record_test_execution(
                "req_user_auth", "test_auth_login", True, 120
            )
            self.metrics_collector.record_operational_metric("auth_success_rate", 0.98)

        # Step 4: Run learning cycle
        logger.info("Step 4: Running learning cycle...")
        learning_results = self.learner.run_learning_cycle(["req_user_auth"])

        # Step 5: Recalculate metrics after learning
        logger.info("Step 5: Recalculating metrics...")
        updated_results = self.calculator.calculate_all_metrics("req_user_auth")

        # Step 6: Generate updated suggestions
        logger.info("Step 6: Generating updated suggestions...")
        updated_all_results = {"req_user_auth": updated_results}
        updated_plan = self.suggestion_generator.generate_improvement_plan(updated_all_results)

        # Verify the workflow
        assert initial_results["runtime_correlation"].score != updated_results["runtime_correlation"].score
        assert learning_results["req_user_auth"]["data_points"] > 0

        # Report should reflect improvements
        initial_report = self.suggestion_generator.format_suggestion_report(initial_plan)
        updated_report = self.suggestion_generator.format_suggestion_report(updated_plan)

        # Reports should be different after learning
        assert initial_report != updated_report
