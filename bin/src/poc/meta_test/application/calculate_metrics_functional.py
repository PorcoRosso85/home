"""Functional implementation of metrics calculation."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Union

from domain.metrics.base import MetricInput, MetricResult
from domain.metrics.existence_functional import calculate_existence_metric
from domain.metrics.reachability_functional import calculate_reachability_metric
from domain.metrics.boundary_coverage_functional import calculate_boundary_coverage_metric
from domain.metrics.change_sensitivity_functional import calculate_change_sensitivity_metric
from domain.metrics.semantic_alignment_functional import calculate_semantic_alignment_metric
from domain.metrics.runtime_correlation_functional import calculate_runtime_correlation_metric
from domain.metrics.value_probability_functional import calculate_value_probability_metric
from infrastructure.embedding_service import EmbeddingService
from infrastructure.errors import ValidationError
from infrastructure.graph_adapter import GraphAdapter
from infrastructure.logger import get_logger
from infrastructure.metrics_collector import MetricsCollector

logger = get_logger(__name__)

# Type alias for metric calculation functions
MetricFunction = Callable[[MetricInput], Union[MetricResult, ValidationError]]


@dataclass
class MetricsCalculatorState:
    """State container for metrics calculator."""
    graph_adapter: GraphAdapter
    embedding_service: EmbeddingService
    metrics_collector: MetricsCollector
    metric_functions: list[MetricFunction]


def create_metrics_calculator(
    graph_adapter: GraphAdapter,
    embedding_service: EmbeddingService,
    metrics_collector: MetricsCollector
) -> MetricsCalculatorState:
    """Create calculator state with dependencies."""
    return MetricsCalculatorState(
        graph_adapter=graph_adapter,
        embedding_service=embedding_service,
        metrics_collector=metrics_collector,
        metric_functions=[
            calculate_existence_metric,
            calculate_reachability_metric,
            calculate_boundary_coverage_metric,
            calculate_change_sensitivity_metric,
            lambda input_data: calculate_semantic_alignment_metric(input_data, embedding_service),
            calculate_runtime_correlation_metric,
            calculate_value_probability_metric,
        ]
    )


def calculate_all_metrics(
    state: MetricsCalculatorState,
    requirement_id: str
) -> Union[dict[str, MetricResult], ValidationError]:
    """Calculate all metrics for a requirement."""
    # Get requirement data
    requirement_data = state.graph_adapter.get_requirement(requirement_id)
    if not requirement_data:
        return ValidationError(
            type="ValidationError",
            message=f"Requirement {requirement_id} not found",
            field="requirement_id",
            value=requirement_id,
            constraint="Requirement must exist in database",
            suggestion="Check requirement ID and ensure it's loaded"
        )
    
    # Get test data
    test_data_list = state.graph_adapter.get_tests_for_requirement(requirement_id)
    
    # Convert test data list to dict format expected by MetricInput
    test_data = {
        "test_count": len(test_data_list),
        "tests": test_data_list
    } if test_data_list else None
    
    # Create input for metrics
    metric_input = MetricInput(
        requirement_id=requirement_id,
        requirement_data=requirement_data,
        test_data=test_data
    )
    
    # Calculate metrics in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all metric calculations
        future_to_metric = {
            executor.submit(metric_fn, metric_input): metric_fn
            for metric_fn in state.metric_functions
        }
        
        # Collect results
        for future in as_completed(future_to_metric):
            result = future.result()
            if isinstance(result, dict) and result.get("type") == "ValidationError":
                logger.log_error(f"Metric calculation failed: {result['message']}")
            else:
                results[result.metric_name] = result
    
    return results