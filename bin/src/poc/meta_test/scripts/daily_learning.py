#!/usr/bin/env python3
"""Daily learning script for updating runtime metrics."""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from application.learn_from_runtime import RuntimeLearner
from infrastructure.cypher_writer import CypherWriter
from infrastructure.graph_adapter import GraphAdapter
from infrastructure.logger import get_logger
from infrastructure.metrics_collector import MetricsCollector

logger = get_logger(__name__)


def main():
    """Run daily learning cycle."""
    logger.info(f"Running daily learning cycle - {datetime.now().strftime('%Y-%m-%d')}")

    # Initialize components
    data_dir = "./meta_test_data"
    graph_adapter = GraphAdapter(f"{data_dir}/graph")
    metrics_collector = MetricsCollector(f"{data_dir}/metrics")
    cypher_writer = CypherWriter(f"{data_dir}/cypher/daily")

    learner = RuntimeLearner(graph_adapter, metrics_collector, cypher_writer)

    # Run learning for all requirements
    logger.info("Processing requirements...")
    results = learner.run_learning_cycle()

    if not results:
        logger.info("No runtime data available for learning.")
        return 0

    # Summary statistics
    total_requirements = len(results)
    successful_updates = sum(1 for r in results.values() if "error" not in r)
    total_updates = sum(len(r.get("updates", {})) for r in results.values() if "error" not in r)

    logger.info("Learning Summary:",
                requirements_processed=total_requirements,
                successful=successful_updates,
                failed=total_requirements - successful_updates,
                total_metric_updates=total_updates)

    # Show significant changes
    logger.info("Significant Changes (>0.1 change):")
    for req_id, result in results.items():
        if "error" not in result and "updates" in result:
            for metric, new_value in result["updates"].items():
                old_value = result["previous_values"].get(metric, 0.5)
                change = new_value - old_value

                if abs(change) > 0.1:
                    direction = "↑" if change > 0 else "↓"
                    logger.info(f"{req_id}/{metric}: {old_value:.2f} → {new_value:.2f} {direction}")

    # Check for requirements needing attention
    logger.info("Requirements Needing Attention:")
    attention_needed = False

    for req_id in results:
        try:
            # Get latest metric values
            runtime_corr = graph_adapter.get_metric_history(req_id, "runtime_correlation")
            value_prob = graph_adapter.get_metric_history(req_id, "value_probability")

            if runtime_corr and runtime_corr[-1].get("score", 1.0) < 0.3:
                logger.warn(f"{req_id}: Low runtime correlation ({runtime_corr[-1]['score']:.2f})")
                attention_needed = True

            if value_prob and value_prob[-1].get("score", 1.0) < 0.3:
                logger.warn(f"{req_id}: Low value probability ({value_prob[-1]['score']:.2f})")
                attention_needed = True

        except Exception:
            pass

    if not attention_needed:
        logger.info("None - all requirements showing healthy metrics")

    # Trends analysis
    logger.info("Trend Analysis:")
    for req_id in list(results.keys())[:3]:  # Show top 3
        try:
            trends = learner.analyze_correlation_trends(req_id)

            logger.info(f"{req_id}:")
            for metric, trend_data in trends.items():
                if trend_data:
                    logger.info(f"{metric}: {trend_data['trend']} ({trend_data['initial']:.2f} → {trend_data['current']:.2f})", requirement_id=req_id)
        except Exception:
            pass

    logger.info(f"Daily learning complete. Results saved to {data_dir}/cypher/daily/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
