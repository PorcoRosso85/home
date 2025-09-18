"""Use case for generating improvement suggestions based on metrics."""

from dataclasses import dataclass

from ..domain.metrics.base import MetricResult


@dataclass
class ImprovementPriority:
    """Priority information for an improvement."""
    requirement_id: str
    metric_name: str
    current_score: float
    impact: float  # Potential improvement impact
    effort: str  # low, medium, high
    suggestions: list[str]


class ImprovementSuggestionGenerator:
    """Generates prioritized improvement suggestions."""

    def __init__(self, threshold: float = 0.7):
        """Initialize with quality threshold."""
        self.threshold = threshold

        # Define metric weights based on importance
        self.metric_weights = {
            "existence": 1.0,  # Most fundamental
            "reachability": 0.9,  # Critical for execution
            "boundary_coverage": 0.8,  # Important for robustness
            "change_sensitivity": 0.7,  # Important for maintenance
            "semantic_alignment": 0.6,  # Important for understanding
            "runtime_correlation": 0.5,  # Learning-based
            "value_probability": 0.5  # Learning-based
        }

        # Define effort estimates
        self.effort_estimates = {
            "existence": "low",  # Just add tests
            "reachability": "medium",  # Refactor dependencies
            "boundary_coverage": "low",  # Add test cases
            "change_sensitivity": "medium",  # Add assertions
            "semantic_alignment": "low",  # Update descriptions
            "runtime_correlation": "high",  # Requires runtime data
            "value_probability": "high"  # Requires business data
        }

    def generate_suggestions(self,
                           metrics_results: dict[str, dict[str, MetricResult]]) -> list[ImprovementPriority]:
        """Generate prioritized improvement suggestions from metrics results."""
        priorities = []

        for requirement_id, requirement_metrics in metrics_results.items():
            for metric_name, result in requirement_metrics.items():
                if result.score < self.threshold:
                    priority = self._create_priority(requirement_id, metric_name, result)
                    priorities.append(priority)

        # Sort by impact (descending) and effort (ascending)
        priorities.sort(key=lambda p: (-p.impact, self._effort_to_number(p.effort)))

        return priorities

    def get_quick_wins(self,
                      metrics_results: dict[str, dict[str, MetricResult]]) -> list[ImprovementPriority]:
        """Get improvements with high impact and low effort."""
        all_suggestions = self.generate_suggestions(metrics_results)

        quick_wins = [
            p for p in all_suggestions
            if p.effort == "low" and p.impact > 0.3
        ]

        return quick_wins

    def get_critical_improvements(self,
                                metrics_results: dict[str, dict[str, MetricResult]]) -> list[ImprovementPriority]:
        """Get critical improvements regardless of effort."""
        critical = []

        for requirement_id, requirement_metrics in metrics_results.items():
            # Check for critical metrics
            existence_score = requirement_metrics.get("existence", MetricResult("", "", 1.0, {}, [])).score
            reachability_score = requirement_metrics.get("reachability", MetricResult("", "", 1.0, {}, [])).score

            if existence_score == 0.0:
                # No tests at all - critical
                priority = self._create_priority(
                    requirement_id,
                    "existence",
                    requirement_metrics["existence"]
                )
                priority.impact = 1.0  # Maximum impact
                critical.append(priority)

            elif reachability_score == 0.0:
                # Tests can't run - critical
                priority = self._create_priority(
                    requirement_id,
                    "reachability",
                    requirement_metrics["reachability"]
                )
                priority.impact = 0.9  # Very high impact
                critical.append(priority)

        return critical

    def generate_improvement_plan(self,
                                metrics_results: dict[str, dict[str, MetricResult]]) -> dict[str, list[ImprovementPriority]]:
        """Generate a phased improvement plan."""
        plan = {
            "immediate": [],  # Critical issues
            "quick_wins": [],  # High impact, low effort
            "planned": [],  # Medium priority
            "backlog": []  # Low priority
        }

        all_suggestions = self.generate_suggestions(metrics_results)
        critical = {(p.requirement_id, p.metric_name) for p in self.get_critical_improvements(metrics_results)}

        for priority in all_suggestions:
            key = (priority.requirement_id, priority.metric_name)

            if key in critical:
                plan["immediate"].append(priority)
            elif priority.effort == "low" and priority.impact > 0.3:
                plan["quick_wins"].append(priority)
            elif priority.impact > 0.5 or priority.effort == "medium":
                plan["planned"].append(priority)
            else:
                plan["backlog"].append(priority)

        return plan

    def _create_priority(self,
                        requirement_id: str,
                        metric_name: str,
                        result: MetricResult) -> ImprovementPriority:
        """Create improvement priority from metric result."""
        # Calculate impact based on how far below threshold
        gap = self.threshold - result.score
        weight = self.metric_weights.get(metric_name, 0.5)
        impact = gap * weight

        return ImprovementPriority(
            requirement_id=requirement_id,
            metric_name=metric_name,
            current_score=result.score,
            impact=impact,
            effort=self.effort_estimates.get(metric_name, "medium"),
            suggestions=result.suggestions
        )

    def _effort_to_number(self, effort: str) -> int:
        """Convert effort string to number for sorting."""
        return {"low": 1, "medium": 2, "high": 3}.get(effort, 2)

    def format_suggestion_report(self,
                               improvement_plan: dict[str, list[ImprovementPriority]]) -> str:
        """Format improvement plan as readable report."""
        lines = ["# Test Quality Improvement Plan\n"]

        sections = [
            ("Immediate Actions", "immediate", "Critical issues that block testing"),
            ("Quick Wins", "quick_wins", "High impact improvements with minimal effort"),
            ("Planned Improvements", "planned", "Medium priority improvements"),
            ("Backlog", "backlog", "Lower priority improvements for future consideration")
        ]

        for title, key, description in sections:
            priorities = improvement_plan.get(key, [])
            if priorities:
                lines.append(f"## {title}")
                lines.append(f"{description}\n")

                for priority in priorities:
                    lines.append(f"### {priority.requirement_id} - {priority.metric_name}")
                    lines.append(f"- Current Score: {priority.current_score:.2f}")
                    lines.append(f"- Impact: {priority.impact:.2f}")
                    lines.append(f"- Effort: {priority.effort}")
                    lines.append("- Suggestions:")
                    for suggestion in priority.suggestions:
                        lines.append(f"  - {suggestion}")
                    lines.append("")

        return "\n".join(lines)
