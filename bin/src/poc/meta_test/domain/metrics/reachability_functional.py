"""Metric 2: Reachability - functional implementation."""

from typing import Union

from infrastructure.errors import ValidationError
from domain.metrics.base import MetricInput, MetricResult


def get_metric_info() -> dict[str, str]:
    """Get metric metadata."""
    return {
        "name": "reachability",
        "description": "Reachability - executable without circular references"
    }


def validate_input(input_data: MetricInput) -> bool:
    """Check if we have dependency data."""
    return bool(
        input_data.requirement_id and
        input_data.requirement_data and
        input_data.test_data
    )


def _detect_circular_dependencies(
    node: str,
    dependencies: dict[str, list[str]],
    visited: set[str],
    path: list[str]
) -> bool:
    """Detect circular dependencies using DFS."""
    if node in path:
        return True  # Circular dependency found
    
    if node in visited:
        return False  # Already checked this path
    
    visited.add(node)
    path.append(node)
    
    for dep in dependencies.get(node, []):
        if _detect_circular_dependencies(dep, dependencies, visited, path):
            return True
    
    path.pop()
    return False


def calculate_reachability_metric(input_data: MetricInput) -> Union[MetricResult, ValidationError]:
    """Calculate reachability score."""
    if not validate_input(input_data):
        return ValidationError(
            type="ValidationError",
            message="Invalid input data for reachability metric",
            field="input_data",
            value=str(input_data),
            constraint="Must have requirement_id, requirement_data, and test_data",
            suggestion="Ensure all required fields are provided with valid data"
        )
    
    # Get dependency graph
    dependencies = input_data.test_data.get("dependencies", {})
    test_id = input_data.test_data.get("test_id", input_data.requirement_id)
    
    # Check for circular dependencies
    visited: set[str] = set()
    has_circular = _detect_circular_dependencies(
        test_id, dependencies, visited, []
    )
    
    # Score: 1.0 if reachable (no circular deps), 0.0 if not
    score = 0.0 if has_circular else 1.0
    
    # Generate suggestions
    suggestions: list[str] = []
    if has_circular:
        suggestions.append(
            f"Circular dependency detected for test {test_id}. "
            "Refactor test dependencies to remove cycles."
        )
    
    metric_info = get_metric_info()
    return MetricResult(
        metric_name=metric_info["name"],
        requirement_id=input_data.requirement_id,
        score=score,
        details={
            "has_circular_dependencies": has_circular,
            "dependency_count": len(dependencies.get(test_id, [])),
            "visited_nodes": len(visited),
        },
        suggestions=suggestions
    )