#!/usr/bin/env python3
"""Initialize metrics for all requirements in the system."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from application.calculate_metrics import MetricsCalculator
from infrastructure.embedding_service import EmbeddingService
from infrastructure.graph_adapter import GraphAdapter
from infrastructure.logger import get_logger
from infrastructure.metrics_collector import MetricsCollector

logger = get_logger(__name__)


def main():
    """Initialize metrics for all requirements."""
    logger.info("Initializing metrics for all requirements...")

    # Initialize components
    data_dir = "./meta_test_data"
    graph_adapter = GraphAdapter(f"{data_dir}/graph")
    embedding_service = EmbeddingService()
    metrics_collector = MetricsCollector(f"{data_dir}/metrics")

    calculator = MetricsCalculator(graph_adapter, embedding_service, metrics_collector)

    # Get all requirements (in real implementation, would query from graph)
    requirement_ids = ["req_auth_001", "req_payment_dup_001"]

    success_count = 0
    error_count = 0

    for req_id in requirement_ids:
        try:
            logger.info(f"Calculating metrics for {req_id}...")
            results = calculator.calculate_all_metrics(req_id)

            # Print summary
            logger.info(f"Completed: {len(results)} metrics calculated", requirement_id=req_id)
            low_scores = [name for name, r in results.items() if r.score < 0.7]
            if low_scores:
                logger.warn(f"Low scores for {', '.join(low_scores)}", requirement_id=req_id)

            success_count += 1

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}", requirement_id=req_id)
            error_count += 1

    logger.info("Summary:", success=success_count, errors=error_count, total=len(requirement_ids))

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
