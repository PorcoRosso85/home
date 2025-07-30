"""Tests for improvement suggestion generator."""


from ..domain.metrics.base import MetricResult
from .improve_suggestions import ImprovementSuggestionGenerator


class TestImprovementSuggestionGenerator:
    """Test improvement suggestion generation."""

    def setup_method(self):
        """Set up test fixture."""
        self.generator = ImprovementSuggestionGenerator(threshold=0.7)

    def _create_test_results(self):
        """Create test metric results."""
        return {
            "req_001": {
                "existence": MetricResult(
                    "existence", "req_001", 0.0,
                    {"has_tests": False},
                    ["No tests found. Create tests."]
                ),
                "reachability": MetricResult(
                    "reachability", "req_001", 1.0,
                    {"has_circular_dependencies": False},
                    []
                ),
                "boundary_coverage": MetricResult(
                    "boundary_coverage", "req_001", 0.5,
                    {"covered": 2, "total": 4},
                    ["Add test for boundary: max_value"]
                ),
                "semantic_alignment": MetricResult(
                    "semantic_alignment", "req_001", 0.6,
                    {"alignment": 0.6},
                    ["Update test descriptions"]
                )
            },
            "req_002": {
                "existence": MetricResult(
                    "existence", "req_002", 1.0,
                    {"has_tests": True},
                    []
                ),
                "reachability": MetricResult(
                    "reachability", "req_002", 0.0,
                    {"has_circular_dependencies": True},
                    ["Remove circular dependencies"]
                )
            }
        }

    def test_generate_suggestions(self):
        """Test generating improvement suggestions."""
        results = self._create_test_results()
        suggestions = self.generator.generate_suggestions(results)

        # Should have suggestions for metrics below threshold
        assert len(suggestions) > 0

        # Check critical issues are included
        existence_suggestions = [s for s in suggestions
                               if s.requirement_id == "req_001" and s.metric_name == "existence"]
        assert len(existence_suggestions) == 1
        assert existence_suggestions[0].current_score == 0.0

        # Check ordering by impact
        assert suggestions[0].impact >= suggestions[-1].impact

    def test_get_quick_wins(self):
        """Test identifying quick wins."""
        results = self._create_test_results()
        quick_wins = self.generator.get_quick_wins(results)

        # Should only include low effort improvements
        assert all(p.effort == "low" for p in quick_wins)
        assert all(p.impact > 0.3 for p in quick_wins)

        # Boundary coverage and semantic alignment should be quick wins
        metric_names = [p.metric_name for p in quick_wins]
        assert "boundary_coverage" in metric_names
        assert "semantic_alignment" in metric_names

    def test_get_critical_improvements(self):
        """Test identifying critical improvements."""
        results = self._create_test_results()
        critical = self.generator.get_critical_improvements(results)

        # Should include existence and reachability issues
        assert len(critical) == 2

        # req_001 has no tests - critical
        req_001_critical = [c for c in critical if c.requirement_id == "req_001"]
        assert len(req_001_critical) == 1
        assert req_001_critical[0].metric_name == "existence"
        assert req_001_critical[0].impact == 1.0

        # req_002 has circular dependencies - critical
        req_002_critical = [c for c in critical if c.requirement_id == "req_002"]
        assert len(req_002_critical) == 1
        assert req_002_critical[0].metric_name == "reachability"

    def test_generate_improvement_plan(self):
        """Test generating phased improvement plan."""
        results = self._create_test_results()
        plan = self.generator.generate_improvement_plan(results)

        # Check plan structure
        assert "immediate" in plan
        assert "quick_wins" in plan
        assert "planned" in plan
        assert "backlog" in plan

        # Critical issues should be immediate
        assert len(plan["immediate"]) > 0
        immediate_metrics = [(p.requirement_id, p.metric_name) for p in plan["immediate"]]
        assert ("req_001", "existence") in immediate_metrics
        assert ("req_002", "reachability") in immediate_metrics

        # Quick wins should be separate from immediate
        assert len(plan["quick_wins"]) > 0

    def test_format_suggestion_report(self):
        """Test formatting improvement plan as report."""
        results = self._create_test_results()
        plan = self.generator.generate_improvement_plan(results)
        report = self.generator.format_suggestion_report(plan)

        # Check report structure
        assert "# Test Quality Improvement Plan" in report
        assert "## Immediate Actions" in report
        assert "## Quick Wins" in report

        # Check content
        assert "req_001 - existence" in report
        assert "Current Score: 0.00" in report
        assert "No tests found" in report
