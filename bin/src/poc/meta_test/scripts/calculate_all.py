#!/usr/bin/env python3
"""Calculate all metrics for all requirements and generate report."""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from application.calculate_metrics import MetricsCalculator
from application.improve_suggestions import ImprovementSuggestionGenerator
from infrastructure.embedding_service import EmbeddingService
from infrastructure.graph_adapter import GraphAdapter
from infrastructure.logger import get_logger
from infrastructure.metrics_collector import MetricsCollector

logger = get_logger(__name__)


def generate_report(all_results: dict) -> str:
    """Generate comprehensive metrics report."""
    lines = [
        "# Meta-Test Metrics Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        f"Requirements analyzed: {len(all_results)}",
        ""
    ]

    # Calculate aggregate statistics
    metric_scores = {metric: [] for metric in ["existence", "reachability", "boundary_coverage",
                                               "change_sensitivity", "semantic_alignment",
                                               "runtime_correlation", "value_probability"]}

    for req_id, results in all_results.items():
        for metric_name, result in results.items():
            metric_scores[metric_name].append(result.score)

    # Average scores
    lines.append("### Average Scores by Metric")
    for metric, scores in metric_scores.items():
        if scores:
            avg = sum(scores) / len(scores)
            lines.append(f"- {metric}: {avg:.2f}")

    lines.append("")
    lines.append("## Detailed Results")

    # Detailed results per requirement
    for req_id, results in all_results.items():
        lines.append(f"\n### {req_id}")

        # Metric scores table
        lines.append("| Metric | Score | Status |")
        lines.append("|--------|-------|--------|")

        for metric_name, result in results.items():
            status = "✅" if result.score >= 0.7 else "⚠️" if result.score >= 0.4 else "❌"
            lines.append(f"| {metric_name} | {result.score:.2f} | {status} |")

        # Suggestions for low scores
        low_score_metrics = [(name, r) for name, r in results.items() if r.score < 0.7]
        if low_score_metrics:
            lines.append("\n**Improvement Areas:**")
            for metric_name, result in low_score_metrics:
                if result.suggestions:
                    lines.append(f"\n*{metric_name}:*")
                    for suggestion in result.suggestions:
                        lines.append(f"- {suggestion}")

    return "\n".join(lines)


def main():
    """Calculate all metrics and generate report."""
    logger.info("Calculating metrics for all requirements...")

    # Initialize components
    data_dir = "./meta_test_data"
    graph_adapter = GraphAdapter(f"{data_dir}/graph")
    embedding_service = EmbeddingService()
    metrics_collector = MetricsCollector(f"{data_dir}/metrics")

    calculator = MetricsCalculator(graph_adapter, embedding_service, metrics_collector)

    # Get all requirements (in real implementation, would query from graph)
    requirement_ids = ["req_auth_001", "req_payment_dup_001"]

    all_results = {}

    for req_id in requirement_ids:
        try:
            logger.info(f"Processing {req_id}...")
            results = calculator.calculate_all_metrics(req_id)
            all_results[req_id] = results
        except Exception as e:
            logger.error(f"Error processing {req_id}: {e}")

    # Generate report
    report = generate_report(all_results)

    # Save report
    report_file = Path(data_dir) / "metrics_report.md"
    report_file.write_text(report)
    logger.info(f"Report saved to: {report_file}")

    # Also save raw data as JSON
    json_file = Path(data_dir) / "metrics_data.json"
    json_data = {
        req_id: {
            metric: {
                "score": result.score,
                "details": result.details,
                "suggestions": result.suggestions
            }
            for metric, result in results.items()
        }
        for req_id, results in all_results.items()
    }

    json_file.write_text(json.dumps(json_data, indent=2))
    logger.info(f"Raw data saved to: {json_file}")

    # Generate improvement suggestions
    logger.info("Generating improvement plan...")
    generator = ImprovementSuggestionGenerator()
    plan = generator.generate_improvement_plan(all_results)
    suggestions_report = generator.format_suggestion_report(plan)

    suggestions_file = Path(data_dir) / "improvement_plan.md"
    suggestions_file.write_text(suggestions_report)
    logger.info(f"Improvement plan saved to: {suggestions_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
