"""Metric 7: Value contribution probability - probability of contributing to business goals."""


from .base import BaseMetric, MetricInput, MetricResult


class ValueProbabilityMetric(BaseMetric):
    """Measures probability of test contributing to business value."""

    @property
    def name(self) -> str:
        return "value_probability"

    @property
    def description(self) -> str:
        return "Value contribution probability - probability of contributing to business goals"

    def validate_input(self, input_data: MetricInput) -> bool:
        """Check if we have business impact data."""
        return bool(
            input_data.requirement_id and
            input_data.runtime_data and
            (input_data.runtime_data.get("business_metrics") or
             input_data.runtime_data.get("incident_history"))
        )

    def _calculate_incident_prevention_score(self,
                                           test_history: list[dict],
                                           incident_history: list[dict]) -> float:
        """Calculate how well tests predict/prevent incidents."""
        if not test_history or not incident_history:
            return 0.5  # Neutral score

        # Group incidents by time window around test failures
        prevented_incidents = 0
        missed_incidents = 0

        for incident in incident_history:
            incident_time = incident.get("timestamp", 0)
            incident_severity = incident.get("severity", "low")

            # Look for test failures before the incident
            warning_window = 24 * 60 * 60  # 24 hours
            test_warned = False

            for test in test_history:
                test_time = test.get("timestamp", 0)
                test_passed = test.get("passed", True)

                if (test_time < incident_time and
                    incident_time - test_time < warning_window and
                    not test_passed):
                    test_warned = True
                    break

            # Weight by severity
            weight = {"high": 3, "medium": 2, "low": 1}.get(incident_severity, 1)

            if test_warned:
                prevented_incidents += weight
            else:
                missed_incidents += weight

        total_weight = prevented_incidents + missed_incidents
        if total_weight == 0:
            return 0.5

        return prevented_incidents / total_weight

    def _calculate_business_metric_impact(self,
                                        test_results: list[bool],
                                        business_metrics: dict[str, list[float]]) -> float:
        """Calculate impact on business metrics."""
        if not test_results or not business_metrics:
            return 0.5

        impacts = []

        for metric_name, values in business_metrics.items():
            if len(values) != len(test_results):
                continue

            # Compare metric values when tests pass vs fail
            pass_values = [v for i, v in enumerate(values) if i < len(test_results) and test_results[i]]
            fail_values = [v for i, v in enumerate(values) if i < len(test_results) and not test_results[i]]

            if pass_values and fail_values:
                avg_pass = sum(pass_values) / len(pass_values)
                avg_fail = sum(fail_values) / len(fail_values)

                # Determine if higher is better based on metric name
                higher_is_better = any(
                    keyword in metric_name.lower()
                    for keyword in ["revenue", "conversion", "satisfaction", "uptime"]
                )

                if higher_is_better:
                    impact = (avg_pass - avg_fail) / (abs(avg_pass) + 0.001)
                else:
                    impact = (avg_fail - avg_pass) / (abs(avg_fail) + 0.001)

                impacts.append(max(0, min(1, impact)))

        return sum(impacts) / len(impacts) if impacts else 0.5

    def _apply_bayesian_update(self,
                             prior: float,
                             evidence_strength: float,
                             evidence_positive: bool) -> float:
        """Apply Bayesian update to probability based on new evidence."""
        # Simple Bayesian update
        if evidence_positive:
            posterior = prior + (1 - prior) * evidence_strength * 0.1
        else:
            posterior = prior * (1 - evidence_strength * 0.1)

        return max(0.01, min(0.99, posterior))

    def calculate(self, input_data: MetricInput) -> MetricResult:
        """Calculate value probability score."""
        if not self.validate_input(input_data):
            raise ValueError("Invalid input data for value probability metric")

        # Start with prior probability
        prior = input_data.runtime_data.get("prior_probability", 0.5)

        # Get runtime data
        test_history = input_data.runtime_data.get("test_history", [])
        incident_history = input_data.runtime_data.get("incident_history", [])
        business_metrics = input_data.runtime_data.get("business_metrics", {})

        # Calculate incident prevention score
        incident_score = self._calculate_incident_prevention_score(
            test_history, incident_history
        )

        # Calculate business metric impact
        test_results = [t.get("passed", False) for t in test_history]
        business_score = self._calculate_business_metric_impact(
            test_results, business_metrics
        )

        # Update probability based on evidence
        probability = prior

        if incident_score != 0.5:  # Not neutral
            evidence_positive = incident_score > 0.5
            evidence_strength = abs(incident_score - 0.5) * 2
            probability = self._apply_bayesian_update(
                probability, evidence_strength, evidence_positive
            )

        if business_score != 0.5:  # Not neutral
            evidence_positive = business_score > 0.5
            evidence_strength = abs(business_score - 0.5) * 2
            probability = self._apply_bayesian_update(
                probability, evidence_strength, evidence_positive
            )

        # Generate suggestions
        suggestions: list[str] = []

        if probability < 0.3:
            suggestions.append(
                "Low probability of business value contribution. "
                "Consider if this test aligns with business objectives."
            )

        if incident_score < 0.3:
            suggestions.append(
                "Test rarely prevents incidents. "
                "Review if test coverage matches production failure modes."
            )

        if business_score < 0.3 and business_metrics:
            suggestions.append(
                "Weak correlation with business metrics. "
                "Ensure test validates business-critical functionality."
            )

        if not incident_history and not business_metrics:
            suggestions.append(
                "No business impact data available. "
                "Start collecting incident and business metric data."
            )

        return MetricResult(
            metric_name=self.name,
            requirement_id=input_data.requirement_id,
            score=probability,
            details={
                "prior_probability": prior,
                "posterior_probability": probability,
                "incident_prevention_score": incident_score,
                "business_impact_score": business_score,
                "evidence_points": len(test_history),
                "incident_count": len(incident_history),
                "business_metrics_count": len(business_metrics),
            },
            suggestions=suggestions
        )
