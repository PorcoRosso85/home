#!/usr/bin/env python
"""Run the comprehensive business scenario E2E test.

This script demonstrates the complete value chain from tests to business impact,
showing how test quality metrics correlate with real business value.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from poc.meta_test.infrastructure.logger import get_logger, setup_logging
from poc.meta_test.e2e.external.test_e2e_business_scenario import TestE2EBusinessScenario

logger = get_logger(__name__)


def run_business_scenario():
    """Run the business scenario test and display results."""
    setup_logging(level="INFO")
    
    logger.info("=" * 60)
    logger.info("Meta-Test Business Value Demonstration")
    logger.info("=" * 60)
    
    # Create test instance
    test = TestE2EBusinessScenario()
    
    try:
        # Setup test environment
        logger.info("\n1. Setting up test environment with KuzuDB...")
        test.setup_method()
        
        # Run payment reliability scenario
        logger.info("\n2. Running payment reliability scenario...")
        test.test_payment_reliability_scenario()
        
        # Verify value chain
        logger.info("\n3. Verifying complete value chain...")
        test.test_value_chain_verification()
        
        # Test learning effectiveness
        logger.info("\n4. Testing metric learning effectiveness...")
        test.test_metric_learning_effectiveness()
        
        # Generate comprehensive report
        logger.info("\n5. Generating comprehensive value report...")
        test.test_comprehensive_value_report()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ All scenarios completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)
        raise
    finally:
        # Cleanup
        test.teardown_method()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run Meta-Test business scenario demonstration"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to simulate (default: 30)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        setup_logging(level="DEBUG")
    
    try:
        run_business_scenario()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to run scenario: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()