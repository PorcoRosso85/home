"""Use case for calculating all metrics for a requirement."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from ..domain.metrics.base import BaseMetric, MetricInput, MetricResult
from ..domain.metrics.boundary_coverage import BoundaryCoverageMetric
from ..domain.metrics.change_sensitivity import ChangeSensitivityMetric
from ..domain.metrics.existence import ExistenceMetric
from ..domain.metrics.reachability import ReachabilityMetric
from ..domain.metrics.runtime_correlation import RuntimeCorrelationMetric
from ..domain.metrics.semantic_alignment import SemanticAlignmentMetric
from ..domain.metrics.value_probability import ValueProbabilityMetric
from ..infrastructure.embedding_service import EmbeddingService
from ..infrastructure.graph_adapter import GraphAdapter
from ..infrastructure.logger import get_logger
from ..infrastructure.metrics_collector import MetricsCollector

logger = get_logger(__name__)


class MetricsCalculator:
    """Calculates all metrics for requirements."""

    def __init__(self,
                 graph_adapter: GraphAdapter,
                 embedding_service: EmbeddingService,
                 metrics_collector: MetricsCollector):
        """Initialize calculator with dependencies."""
        self.graph_adapter = graph_adapter
        self.embedding_service = embedding_service
        self.metrics_collector = metrics_collector

        # Initialize all metrics
        self.metrics: list[BaseMetric] = [
            ExistenceMetric(),
            ReachabilityMetric(),
            BoundaryCoverageMetric(),
            ChangeSensitivityMetric(),
            SemanticAlignmentMetric(),
            RuntimeCorrelationMetric(),
            ValueProbabilityMetric()
        ]

    def calculate_all_metrics(self, requirement_id: str) -> dict[str, MetricResult]:
        """Calculate all 7 metrics for a requirement."""
        # Get requirement data
        requirement_data = self.graph_adapter.get_requirement(requirement_id)
        if not requirement_data:
            raise ValueError(f"Requirement {requirement_id} not found")

        # Get test data
        tests = self.graph_adapter.get_tests_for_requirement(requirement_id)
        test_data = self._prepare_test_data(requirement_id, tests)

        # Get runtime data for metrics 6 and 7
        runtime_data = self._prepare_runtime_data(requirement_id)

        # Add embeddings if needed
        if requirement_data.get("description") and not requirement_data.get("embedding"):
            requirement_data["embedding"] = self.embedding_service.generate_embedding(
                requirement_data["description"]
            )

        # Prepare input
        input_data = MetricInput(
            requirement_id=requirement_id,
            requirement_data=requirement_data,
            test_data=test_data,
            runtime_data=runtime_data
        )

        # Calculate metrics in parallel
        results = {}
        with ThreadPoolExecutor(max_workers=7) as executor:
            future_to_metric = {
                executor.submit(self._calculate_metric, metric, input_data): metric
                for metric in self.metrics
            }

            for future in as_completed(future_to_metric):
                metric = future_to_metric[future]
                try:
                    result = future.result()
                    results[metric.name] = result

                    # Save result to graph
                    self.graph_adapter.save_metric_result(
                        requirement_id,
                        metric.name,
                        {
                            "score": result.score,
                            "details": result.details,
                            "suggestions": result.suggestions
                        }
                    )
                except Exception as e:
                    logger.error(f"Error calculating {metric.name}: {e}")
                    results[metric.name] = MetricResult(
                        metric_name=metric.name,
                        requirement_id=requirement_id,
                        score=0.0,
                        details={"error": str(e)},
                        suggestions=[f"Failed to calculate: {e}"]
                    )

        return results

    def calculate_specific_metric(self,
                                requirement_id: str,
                                metric_name: str) -> MetricResult:
        """Calculate a specific metric for a requirement."""
        # Find the metric
        metric = next((m for m in self.metrics if m.name == metric_name), None)
        if not metric:
            raise ValueError(f"Unknown metric: {metric_name}")

        # Get requirement data
        requirement_data = self.graph_adapter.get_requirement(requirement_id)
        if not requirement_data:
            raise ValueError(f"Requirement {requirement_id} not found")

        # Get test data
        tests = self.graph_adapter.get_tests_for_requirement(requirement_id)
        test_data = self._prepare_test_data(requirement_id, tests)

        # Get runtime data if needed
        runtime_data = None
        if metric_name in ["runtime_correlation", "value_probability"]:
            runtime_data = self._prepare_runtime_data(requirement_id)

        # Add embeddings if needed for semantic alignment
        if metric_name == "semantic_alignment":
            if requirement_data.get("description") and not requirement_data.get("embedding"):
                requirement_data["embedding"] = self.embedding_service.generate_embedding(
                    requirement_data["description"]
                )

        # Prepare input
        input_data = MetricInput(
            requirement_id=requirement_id,
            requirement_data=requirement_data,
            test_data=test_data,
            runtime_data=runtime_data
        )

        # Calculate metric
        result = metric.calculate(input_data)

        # Save result
        self.graph_adapter.save_metric_result(
            requirement_id,
            metric_name,
            {
                "score": result.score,
                "details": result.details,
                "suggestions": result.suggestions
            }
        )

        return result

    def _calculate_metric(self, metric: BaseMetric, input_data: MetricInput) -> MetricResult:
        """Calculate a single metric."""
        return metric.calculate(input_data)

    def _prepare_test_data(self, requirement_id: str, tests: list[dict]) -> dict:
        """Prepare test data for metrics."""
        test_data = {
            "test_count": len(tests),
            "tests": tests
        }

        if tests:
            # Get dependencies for first test (for reachability)
            test_id = tests[0].get("id", f"test_for_{requirement_id}")
            test_data["test_id"] = test_id
            test_data["dependencies"] = self.graph_adapter.get_dependencies(test_id)

            # Extract test descriptions and add embeddings
            descriptions = []
            for test in tests:
                if test.get("description"):
                    desc_data = {
                        "description": test["description"],
                        "embedding": self.embedding_service.generate_embedding(test["description"])
                    }
                    descriptions.append(desc_data)

            test_data["descriptions"] = descriptions

            # Add test cases info if available
            test_cases = []
            for test in tests:
                if "test_cases" in test:
                    test_cases.extend(test["test_cases"])
            test_data["test_cases"] = test_cases

        return test_data

    def _prepare_runtime_data(self, requirement_id: str) -> dict:
        """Prepare runtime data for metrics 6 and 7."""
        runtime_data = {}

        # Get test execution history
        test_history = self.metrics_collector.get_test_history(requirement_id)
        runtime_data["test_history"] = [
            {
                "timestamp": entry["timestamp"],
                "passed": entry["passed"],
                "test_id": entry["test_id"]
            }
            for entry in test_history
        ]

        # Get operational metrics
        runtime_data["operational_metrics"] = self.metrics_collector.get_operational_metrics()

        # Get business metrics
        runtime_data["business_metrics"] = self.metrics_collector.get_business_metrics()

        # Get incidents
        runtime_data["incidents"] = self.metrics_collector.get_incidents(requirement_id)
        runtime_data["incident_history"] = runtime_data["incidents"]  # Alias for compatibility

        # Get prior probability if exists
        metric_history = self.graph_adapter.get_metric_history(requirement_id, "value_probability")
        if metric_history:
            runtime_data["prior_probability"] = metric_history[-1].get("score", 0.5)
        else:
            runtime_data["prior_probability"] = 0.5

        return runtime_data
