"""CLI entry point for meta-test system."""

import argparse
import sys
from pathlib import Path

from .application.calculate_metrics import MetricsCalculator
from .application.improve_suggestions import ImprovementSuggestionGenerator
from .application.learn_from_runtime import RuntimeLearner
from .infrastructure.cypher_writer import CypherWriter
from .infrastructure.embedding_service import EmbeddingService
from .infrastructure.graph_adapter import GraphAdapter
from .infrastructure.logger import get_logger
from .infrastructure.metrics_collector import MetricsCollector

logger = get_logger(__name__)


def init_dependencies(data_dir: str = "./meta_test_data"):
    """Initialize all dependencies."""
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    graph_adapter = GraphAdapter(str(data_path / "graph"))
    embedding_service = EmbeddingService()
    metrics_collector = MetricsCollector(str(data_path / "metrics"))
    cypher_writer = CypherWriter(str(data_path / "cypher"))

    return graph_adapter, embedding_service, metrics_collector, cypher_writer


def cmd_init(args):
    """Initialize the meta-test system."""
    logger.info("Initializing meta-test system...")

    # Create data directories
    data_dir = Path(args.data_dir)
    dirs = ["graph", "metrics", "cypher", "cypher/daily"]

    for dir_name in dirs:
        dir_path = data_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created: {dir_path}")

    # Initialize components
    graph_adapter, _, _, _ = init_dependencies(args.data_dir)

    logger.info("Meta-test system initialized successfully!", data_directory=str(data_dir.absolute()))
    return 0


def cmd_calculate(args):
    """Calculate metrics for requirements."""
    graph_adapter, embedding_service, metrics_collector, _ = init_dependencies(args.data_dir)
    calculator = MetricsCalculator(graph_adapter, embedding_service, metrics_collector)

    try:
        if args.metric:
            # Calculate specific metric
            logger.info(f"Calculating {args.metric} for {args.requirement_id}...")
            result = calculator.calculate_specific_metric(args.requirement_id, args.metric)

            logger.info(f"Metric: {result.metric_name}", score=result.score)
            logger.debug("Metric details", extra={"data": result.details})

            if result.suggestions:
                logger.info("Suggestions:", suggestions=result.suggestions)
        else:
            # Calculate all metrics
            logger.info(f"Calculating all metrics for {args.requirement_id}...")
            results = calculator.calculate_all_metrics(args.requirement_id)

            logger.info("Metric Results:")
            for metric_name, result in results.items():
                logger.info(f"{metric_name}: {result.score:.2f}", metric=metric_name, score=result.score)

            # Show suggestions for low scores
            logger.info("Improvement Suggestions:")
            for metric_name, result in results.items():
                if result.score < 0.7 and result.suggestions:
                    logger.info(f"{metric_name} suggestions:", metric=metric_name, suggestions=result.suggestions)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


def cmd_check(args):
    """Check a specific metric across all requirements."""
    graph_adapter, embedding_service, metrics_collector, _ = init_dependencies(args.data_dir)

    # For demo, check the metric for all requirements with data
    logger.info(f"Checking {args.metric} metric...")

    # In real implementation, would query all requirements
    # For now, show example output
    logger.info(f"{args.metric.upper()} Metric Report")

    # Example data
    example_data = [
        ("req_auth_001", 1.0, "GOOD"),
        ("req_payment_dup_001", 0.83, "GOOD"),
        ("req_export_001", 0.0, "MISSING"),
    ]

    for req_id, score, status in example_data:
        logger.info(f"{req_id}: {score:.2f} ({status})", requirement_id=req_id, score=score, status=status)

    return 0


def cmd_suggest(args):
    """Generate improvement suggestions."""
    graph_adapter, embedding_service, metrics_collector, _ = init_dependencies(args.data_dir)
    generator = ImprovementSuggestionGenerator(threshold=args.threshold)

    logger.info(f"Generating suggestions (threshold: {args.threshold})...")

    # For demo, create sample data
    # In real implementation, would calculate metrics for all requirements
    sample_results = {
        "req_001": {
            "existence": type('obj', (object,), {
                'score': 0.0,
                'suggestions': ["No tests found. Create tests."],
                'metric_name': 'existence',
                'requirement_id': 'req_001',
                'details': {}
            })(),
            "reachability": type('obj', (object,), {
                'score': 1.0,
                'suggestions': [],
                'metric_name': 'reachability',
                'requirement_id': 'req_001',
                'details': {}
            })(),
        }
    }

    # Generate improvement plan
    plan = generator.generate_improvement_plan(sample_results)
    report = generator.format_suggestion_report(plan)

    logger.info("Improvement plan generated")
    # Print report to stdout for CLI usage
    print(report)
    return 0


def cmd_learn(args):
    """Run learning process."""
    graph_adapter, embedding_service, metrics_collector, cypher_writer = init_dependencies(args.data_dir)
    learner = RuntimeLearner(graph_adapter, metrics_collector, cypher_writer)

    logger.info("Running learning cycle...")

    if args.requirement_id:
        # Learn for specific requirement
        results = learner.run_learning_cycle([args.requirement_id])
    else:
        # Learn for all requirements with data
        results = learner.run_learning_cycle()

    if results:
        logger.info("Learning Results:")

        for req_id, result in results.items():
            if "error" in result:
                logger.error(f"{req_id}: {result['error']}", requirement_id=req_id)
            else:
                logger.info(f"{req_id}: Data points: {result.get('data_points', 0)}", requirement_id=req_id, data_points=result.get('data_points', 0))

                if "updates" in result:
                    for metric, value in result["updates"].items():
                        old_val = result["previous_values"].get(metric, 0.5)
                        logger.info(f"{metric}: {old_val:.2f} → {value:.2f}", requirement_id=req_id, metric=metric, old_value=old_val, new_value=value)
    else:
        logger.info("No runtime data available for learning.")

    return 0


def main(args: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="meta_test",
        description="Meta-Test System - Test Quality Evaluation with 7 Independent Metrics"
    )
    parser.add_argument(
        "--data-dir",
        default="./meta_test_data",
        help="Data directory for meta-test system (default: ./meta_test_data)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    parser_init = subparsers.add_parser("init", help="Initialize the meta-test system")

    # Calculate command
    parser_calc = subparsers.add_parser("calculate", help="Calculate metrics for a requirement")
    parser_calc.add_argument("--requirement-id", required=True, help="Requirement ID")
    parser_calc.add_argument("--metric", help="Specific metric to calculate (optional)")

    # Check command
    parser_check = subparsers.add_parser("check", help="Check specific metric across requirements")
    parser_check.add_argument("metric", help="Metric name to check")

    # Suggest command
    parser_suggest = subparsers.add_parser("suggest", help="Generate improvement suggestions")
    parser_suggest.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Quality threshold (default: 0.7)"
    )

    # Learn command
    parser_learn = subparsers.add_parser("learn", help="Run learning process for runtime metrics")
    parser_learn.add_argument(
        "--requirement-id",
        help="Specific requirement to learn (optional)"
    )

    # Parse arguments
    if args is None:
        args = sys.argv[1:]
    parsed_args = parser.parse_args(args)

    # Execute command
    if not parsed_args.command:
        parser.print_help()
        return 0

    command_map = {
        "init": cmd_init,
        "calculate": cmd_calculate,
        "check": cmd_check,
        "suggest": cmd_suggest,
        "learn": cmd_learn,
    }

    if parsed_args.command in command_map:
        return command_map[parsed_args.command](parsed_args)
    else:
        logger.error(f"Unknown command: {parsed_args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
