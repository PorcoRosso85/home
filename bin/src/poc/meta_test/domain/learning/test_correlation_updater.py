"""Tests for correlation updater."""

from datetime import datetime

from .correlation_updater import CorrelationUpdater, LearningData


class TestCorrelationUpdater:
    """Test Bayesian correlation updates."""

    def setup_method(self):
        """Set up test fixture."""
        self.updater = CorrelationUpdater(learning_rate=0.2)

    def test_update_runtime_correlation(self):
        """Test updating runtime correlation metric."""
        current_state = {"runtime_correlation": 0.5}

        learning_data = LearningData(
            requirement_id="req_001",
            timestamp=datetime.now(),
            test_results=[True, False, True, False, True],
            operational_metrics={
                "cpu_usage": [50, 80, 45, 85, 48],
                "response_time": [100, 200, 95, 210, 98]
            },
            business_metrics={},
            incidents=[]
        )

        result = self.updater.update_correlations(current_state, learning_data)

        assert "runtime_correlation" in result.metric_updates
        assert 0.0 <= result.metric_updates["runtime_correlation"] <= 1.0
        assert "runtime_correlation" in result.confidence_intervals

    def test_update_value_probability(self):
        """Test updating value probability metric."""
        current_state = {"value_probability": 0.5}

        learning_data = LearningData(
            requirement_id="req_001",
            timestamp=datetime.now(),
            test_results=[True, True, False, True, False],
            operational_metrics={},
            business_metrics={
                "revenue": [1000, 1100, 900, 1050, 850],
                "conversion_rate": [0.05, 0.06, 0.04, 0.055, 0.035]
            },
            incidents=[
                {"test_index": 2, "severity": "high"},
                {"test_index": 4, "severity": "medium"}
            ]
        )

        result = self.updater.update_correlations(current_state, learning_data)

        assert "value_probability" in result.metric_updates
        assert 0.0 <= result.metric_updates["value_probability"] <= 1.0
        assert len(result.learning_summary) > 0

    def test_confidence_intervals(self):
        """Test confidence interval calculation."""
        current_state = {"runtime_correlation": 0.7}

        # Small sample size
        small_data = LearningData(
            requirement_id="req_001",
            timestamp=datetime.now(),
            test_results=[True, False],
            operational_metrics={"metric": [100, 200]},
            business_metrics={},
            incidents=[]
        )

        result_small = self.updater.update_correlations(current_state, small_data)
        interval_small = result_small.confidence_intervals["runtime_correlation"]

        # Large sample size
        large_data = LearningData(
            requirement_id="req_001",
            timestamp=datetime.now(),
            test_results=[True] * 100,
            operational_metrics={"metric": list(range(100))},
            business_metrics={},
            incidents=[]
        )

        result_large = self.updater.update_correlations(current_state, large_data)
        interval_large = result_large.confidence_intervals["runtime_correlation"]

        # Larger sample should have tighter confidence interval
        assert (interval_small[1] - interval_small[0]) > (interval_large[1] - interval_large[0])
