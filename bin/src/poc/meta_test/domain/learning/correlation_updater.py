"""Bayesian updater for metrics 6 and 7 based on runtime data."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class LearningData:
    """Data for learning updates."""
    requirement_id: str
    timestamp: datetime
    test_results: list[bool]
    operational_metrics: dict[str, list[float]]
    business_metrics: dict[str, list[float]]
    incidents: list[dict]


@dataclass
class LearningResult:
    """Result of learning update."""
    requirement_id: str
    metric_updates: dict[str, float]
    confidence_intervals: dict[str, tuple[float, float]]
    learning_summary: str


class CorrelationUpdater:
    """Updates correlation probabilities based on runtime evidence."""

    def __init__(self, learning_rate: float = 0.1):
        """Initialize updater with learning rate."""
        self.learning_rate = learning_rate

    def update_correlations(self,
                          current_state: dict[str, float],
                          new_data: LearningData) -> LearningResult:
        """Update correlations based on new runtime data."""
        updates = {}
        confidence_intervals = {}

        # Update runtime correlation (metric 6)
        if new_data.operational_metrics:
            runtime_update = self._update_runtime_correlation(
                current_state.get("runtime_correlation", 0.5),
                new_data.test_results,
                new_data.operational_metrics
            )
            updates["runtime_correlation"] = runtime_update
            confidence_intervals["runtime_correlation"] = self._calculate_confidence_interval(
                runtime_update, len(new_data.test_results)
            )

        # Update value probability (metric 7)
        if new_data.business_metrics or new_data.incidents:
            value_update = self._update_value_probability(
                current_state.get("value_probability", 0.5),
                new_data.test_results,
                new_data.business_metrics,
                new_data.incidents
            )
            updates["value_probability"] = value_update
            confidence_intervals["value_probability"] = self._calculate_confidence_interval(
                value_update, len(new_data.test_results)
            )

        # Generate summary
        summary = self._generate_learning_summary(updates, new_data)

        return LearningResult(
            requirement_id=new_data.requirement_id,
            metric_updates=updates,
            confidence_intervals=confidence_intervals,
            learning_summary=summary
        )

    def _update_runtime_correlation(self,
                                  current: float,
                                  test_results: list[bool],
                                  operational_metrics: dict[str, list[float]]) -> float:
        """Update runtime correlation metric."""
        if not test_results or not operational_metrics:
            return current

        # Calculate new correlation evidence
        correlations = []
        for metric_values in operational_metrics.values():
            if len(metric_values) == len(test_results):
                corr = self._simple_correlation(test_results, metric_values)
                correlations.append(abs(corr))

        if correlations:
            new_evidence = max(correlations)
            # Weighted update
            updated = current * (1 - self.learning_rate) + new_evidence * self.learning_rate
            return max(0.0, min(1.0, updated))

        return current

    def _update_value_probability(self,
                                current: float,
                                test_results: list[bool],
                                business_metrics: dict[str, list[float]],
                                incidents: list[dict]) -> float:
        """Update value probability metric."""
        evidence_strength = 0.0
        evidence_count = 0

        # Evidence from business metrics
        if business_metrics:
            for metric_values in business_metrics.values():
                if len(metric_values) == len(test_results):
                    impact = self._calculate_business_impact(test_results, metric_values)
                    evidence_strength += impact
                    evidence_count += 1

        # Evidence from incidents
        if incidents:
            prevention_rate = self._calculate_incident_prevention_rate(test_results, incidents)
            evidence_strength += prevention_rate
            evidence_count += 1

        if evidence_count > 0:
            avg_evidence = evidence_strength / evidence_count
            # Bayesian-style update
            updated = current + (avg_evidence - current) * self.learning_rate
            return max(0.0, min(1.0, updated))

        return current

    def _simple_correlation(self, x: list[bool], y: list[float]) -> float:
        """Calculate simple correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        x_numeric = [1.0 if val else 0.0 for val in x]

        # Calculate means
        x_mean = sum(x_numeric) / len(x_numeric)
        y_mean = sum(y) / len(y)

        # Calculate correlation
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x_numeric, y))

        x_var = sum((xi - x_mean) ** 2 for xi in x_numeric)
        y_var = sum((yi - y_mean) ** 2 for yi in y)

        denominator = (x_var * y_var) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _calculate_business_impact(self, test_results: list[bool], metric_values: list[float]) -> float:
        """Calculate business impact score."""
        if not test_results or not metric_values:
            return 0.5

        # Compare metric when tests pass vs fail
        pass_values = [v for i, v in enumerate(metric_values) if i < len(test_results) and test_results[i]]
        fail_values = [v for i, v in enumerate(metric_values) if i < len(test_results) and not test_results[i]]

        if pass_values and fail_values:
            pass_avg = sum(pass_values) / len(pass_values)
            fail_avg = sum(fail_values) / len(fail_values)

            # Assume higher is better for now
            if pass_avg > fail_avg:
                return min(1.0, (pass_avg - fail_avg) / (abs(pass_avg) + 1))
            else:
                return 0.5 - min(0.5, (fail_avg - pass_avg) / (abs(fail_avg) + 1))

        return 0.5

    def _calculate_incident_prevention_rate(self, test_results: list[bool], incidents: list[dict]) -> float:
        """Calculate incident prevention rate."""
        if not incidents:
            return 0.5

        prevented = 0
        total = 0

        for incident in incidents:
            # Simple heuristic: test failure before incident = prevention
            incident_idx = incident.get("test_index", -1)
            if 0 <= incident_idx < len(test_results):
                total += 1
                if not test_results[incident_idx]:
                    prevented += 1

        if total == 0:
            return 0.5

        return prevented / total

    def _calculate_confidence_interval(self, value: float, sample_size: int) -> tuple[float, float]:
        """Calculate confidence interval for the metric."""
        # Simple confidence interval based on sample size
        if sample_size < 10:
            margin = 0.3
        elif sample_size < 50:
            margin = 0.2
        elif sample_size < 100:
            margin = 0.1
        else:
            margin = 0.05

        lower = max(0.0, value - margin)
        upper = min(1.0, value + margin)

        return (lower, upper)

    def _generate_learning_summary(self, updates: dict[str, float], data: LearningData) -> str:
        """Generate human-readable learning summary."""
        lines = [
            f"Learning update for requirement {data.requirement_id}",
            f"Based on {len(data.test_results)} test executions",
        ]

        for metric, new_value in updates.items():
            lines.append(f"- {metric}: updated to {new_value:.3f}")

        if data.incidents:
            lines.append(f"- Processed {len(data.incidents)} incidents")

        if data.business_metrics:
            lines.append(f"- Analyzed {len(data.business_metrics)} business metrics")

        return "\n".join(lines)
