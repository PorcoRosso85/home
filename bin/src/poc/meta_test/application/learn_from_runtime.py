"""Use case for learning from runtime data."""

from datetime import datetime

from ..domain.learning.correlation_updater import CorrelationUpdater, LearningData
from ..infrastructure.cypher_writer import CypherWriter
from ..infrastructure.graph_adapter import GraphAdapter
from ..infrastructure.logger import get_logger
from ..infrastructure.metrics_collector import MetricsCollector

logger = get_logger(__name__)


class RuntimeLearner:
    """Learns from runtime data to update metrics 6 and 7."""

    def __init__(self,
                 graph_adapter: GraphAdapter,
                 metrics_collector: MetricsCollector,
                 cypher_writer: CypherWriter,
                 learning_rate: float = 0.1):
        """Initialize learner with dependencies."""
        self.graph_adapter = graph_adapter
        self.metrics_collector = metrics_collector
        self.cypher_writer = cypher_writer
        self.correlation_updater = CorrelationUpdater(learning_rate)

    def run_learning_cycle(self, requirement_ids: list[str] | None = None) -> dict[str, dict]:
        """Run learning cycle for specified requirements or all."""
        results = {}

        # Get requirements to process
        if requirement_ids is None:
            # In real implementation, would query all requirements
            # For now, process requirements that have runtime data
            requirement_ids = self._get_requirements_with_runtime_data()

        # Process each requirement
        updates = []
        for requirement_id in requirement_ids:
            try:
                result = self._learn_for_requirement(requirement_id)
                if result:
                    results[requirement_id] = result

                    # Prepare updates for Cypher export
                    for metric_name, new_value in result["updates"].items():
                        updates.append({
                            "requirement_id": requirement_id,
                            "metric_name": metric_name,
                            "old_value": result["previous_values"].get(metric_name, 0.5),
                            "new_value": new_value,
                            "confidence_interval": result["confidence_intervals"].get(
                                metric_name, (new_value - 0.1, new_value + 0.1)
                            )
                        })
            except Exception as e:
                logger.error(f"Error learning for {requirement_id}: {e}")
                results[requirement_id] = {"error": str(e)}

        # Write updates to Cypher
        if updates:
            self.cypher_writer.write_learning_batch(updates)

        return results

    def _learn_for_requirement(self, requirement_id: str) -> dict | None:
        """Learn and update metrics for a single requirement."""
        # Get current metric values
        current_state = self._get_current_metric_values(requirement_id)

        # Get runtime data
        test_history = self.metrics_collector.get_test_history(requirement_id)
        if not test_history:
            return None

        # Extract test results
        test_results = [entry["passed"] for entry in test_history]

        # Get operational and business metrics
        operational_metrics = self.metrics_collector.get_operational_metrics()
        business_metrics = self.metrics_collector.get_business_metrics()
        incidents = self.metrics_collector.get_incidents(requirement_id)

        # Prepare learning data
        learning_data = LearningData(
            requirement_id=requirement_id,
            timestamp=datetime.now(),
            test_results=test_results,
            operational_metrics=operational_metrics,
            business_metrics=business_metrics,
            incidents=incidents
        )

        # Run learning update
        learning_result = self.correlation_updater.update_correlations(
            current_state, learning_data
        )

        # Save updated metrics
        for metric_name, new_value in learning_result.metric_updates.items():
            self.graph_adapter.save_metric_result(
                requirement_id,
                metric_name,
                {
                    "score": new_value,
                    "confidence_interval": learning_result.confidence_intervals[metric_name],
                    "updated_at": datetime.now().isoformat(),
                    "data_points": len(test_results)
                }
            )

        return {
            "updates": learning_result.metric_updates,
            "confidence_intervals": learning_result.confidence_intervals,
            "summary": learning_result.learning_summary,
            "previous_values": current_state,
            "data_points": len(test_results)
        }

    def _get_current_metric_values(self, requirement_id: str) -> dict[str, float]:
        """Get current values for learning metrics."""
        values = {}

        for metric_name in ["runtime_correlation", "value_probability"]:
            history = self.graph_adapter.get_metric_history(requirement_id, metric_name)
            if history:
                values[metric_name] = history[-1].get("score", 0.5)
            else:
                values[metric_name] = 0.5  # Default prior

        return values

    def _get_requirements_with_runtime_data(self) -> list[str]:
        """Get requirements that have runtime data available."""
        # Get all test executions
        all_executions = self.metrics_collector.get_test_history(None)

        # Extract unique requirement IDs
        requirement_ids = list(set(
            execution["requirement_id"]
            for execution in all_executions
            if "requirement_id" in execution
        ))

        return requirement_ids

    def analyze_correlation_trends(self, requirement_id: str) -> dict:
        """Analyze trends in correlation metrics over time."""
        trends = {
            "runtime_correlation": [],
            "value_probability": []
        }

        for metric_name in trends:
            history = self.graph_adapter.get_metric_history(requirement_id, metric_name)

            if len(history) > 1:
                # Calculate trend
                values = [h["score"] for h in history]
                timestamps = [h.get("updated_at", "") for h in history]

                # Simple trend: increasing, decreasing, or stable
                if values[-1] > values[0] + 0.1:
                    trend = "increasing"
                elif values[-1] < values[0] - 0.1:
                    trend = "decreasing"
                else:
                    trend = "stable"

                trends[metric_name] = {
                    "current": values[-1],
                    "initial": values[0],
                    "change": values[-1] - values[0],
                    "trend": trend,
                    "data_points": len(values),
                    "history": list(zip(timestamps, values))
                }

        return trends
