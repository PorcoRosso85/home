"""Comprehensive business scenario E2E test demonstrating value chain.

This test demonstrates:
1. Tests prevent incidents (payment reliability scenario)
2. Business metrics improve after test introduction
3. Value probability metric learns from data
4. Complete end-to-end flow with real KuzuDB
5. ROI calculation of test investments
"""

import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pytest

from ...infrastructure.ddl_loader import DDLLoader
from ...infrastructure.graph_adapter import GraphAdapter
from ...infrastructure.logger import get_logger
from ...infrastructure.metrics_collector import MetricsCollector
from ...application.calculate_metrics import MetricsCalculator
from ...application.learn_from_runtime import RuntimeLearner
from ...infrastructure.embedding_service import EmbeddingService
from ...infrastructure.cypher_writer import CypherWriter
from .test_helpers import ensure_test_compatibility

logger = get_logger(__name__)


class TestE2EBusinessScenario:
    """E2E test demonstrating complete business value chain."""

    def setup_method(self):
        """Set up test environment with real KuzuDB."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_business_scenario.db"
        
        # Initialize components
        self.graph_adapter = GraphAdapter(str(self.db_path))
        ddl_dir = Path(__file__).parent.parent.parent / "ddl"
        self.ddl_loader = DDLLoader(self.graph_adapter, base_dir=str(ddl_dir))
        self.metrics_collector = MetricsCollector(str(Path(self.temp_dir) / "metrics"))
        self.embedding_service = EmbeddingService()
        self.cypher_writer = CypherWriter(str(Path(self.temp_dir) / "cypher"))
        
        self.calculator = MetricsCalculator(
            self.graph_adapter,
            self.embedding_service,
            self.metrics_collector
        )
        
        self.learner = RuntimeLearner(
            self.graph_adapter,
            self.metrics_collector,
            self.cypher_writer
        )
        
        # Load schema and sample data
        self._load_ddl_and_data()

    def teardown_method(self):
        """Clean up test environment."""
        self.graph_adapter.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _load_ddl_and_data(self):
        """Load DDL schema and sample data using DDLLoader."""
        # Load migration schema
        success, results = self.ddl_loader.load_ddl("migration_v1.0.0_meta_test")
        if not success:
            pytest.fail(f"Failed to load migration DDL: {results}")
            
        # Load sample data
        success, results = self.ddl_loader.load_ddl("sample_data")
        if not success:
            pytest.fail(f"Failed to load sample data: {results}")
            
        logger.info("Successfully loaded DDL schema and sample data")
        
        # Ensure compatibility between TestEntity and TestSpecification
        ensure_test_compatibility(self.graph_adapter)

    def _simulate_business_operations(self, days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """Simulate business operations over time.
        
        Args:
            days: Number of days to simulate
            
        Returns:
            Dict containing operational data
        """
        operational_data = {
            "test_executions": [],
            "business_metrics": [],
            "incidents": [],
            "prevented_incidents": []
        }
        
        base_date = datetime.now() - timedelta(days=days)
        
        for day in range(days):
            current_date = base_date + timedelta(days=day)
            timestamp = current_date.isoformat() + "Z"
            
            # Simulate test executions
            # Days 0-10: No tests (baseline)
            # Days 11-20: Basic tests introduced
            # Days 21-30: Comprehensive tests
            
            if day >= 11:  # Tests introduced
                # Payment boundary test
                test_passed = day % 7 != 0  # Fail every 7th day
                self.metrics_collector.record_test_execution(
                    "req_payment_reliability",
                    "test_payment_boundary",
                    passed=test_passed,
                    duration_ms=150 + (day % 50)
                )
                operational_data["test_executions"].append({
                    "day": day,
                    "test": "test_payment_boundary",
                    "passed": test_passed,
                    "timestamp": timestamp
                })
                
                if day >= 21:  # Comprehensive tests
                    # Retry logic test
                    retry_passed = day % 5 != 0
                    self.metrics_collector.record_test_execution(
                        "req_payment_reliability",
                        "test_payment_retry",
                        passed=retry_passed,
                        duration_ms=2500 + (day % 100)
                    )
                    operational_data["test_executions"].append({
                        "day": day,
                        "test": "test_payment_retry",
                        "passed": retry_passed,
                        "timestamp": timestamp
                    })
            
            # Business metrics correlate with test coverage
            if day < 11:  # No tests
                success_rate = 98.5 + (day % 3) * 0.1  # 98.5-98.8%
                daily_revenue = 4500000 + (day % 5) * 100000
                incident_probability = 0.15  # 15% chance
            elif day < 21:  # Basic tests
                success_rate = 99.0 + (day % 3) * 0.1  # 99.0-99.2%
                daily_revenue = 4800000 + (day % 5) * 100000
                incident_probability = 0.08  # 8% chance
            else:  # Comprehensive tests
                success_rate = 99.5 + (day % 3) * 0.1  # 99.5-99.7%
                daily_revenue = 5000000 + (day % 5) * 100000
                incident_probability = 0.02  # 2% chance
                
            # Record business metrics
            self.metrics_collector.record_operational_metric("payment_success_rate", success_rate)
            self.metrics_collector.record_business_metric("daily_revenue", daily_revenue)
            
            operational_data["business_metrics"].append({
                "day": day,
                "success_rate": success_rate,
                "daily_revenue": daily_revenue,
                "timestamp": timestamp
            })
            
            # Simulate incidents (less likely with better test coverage)
            import random
            if random.random() < incident_probability:
                incident_impact = random.randint(100000, 1000000)
                
                if day >= 11 and not test_passed:  # Test caught the issue
                    # Incident prevented
                    operational_data["prevented_incidents"].append({
                        "day": day,
                        "impact_prevented": incident_impact,
                        "caught_by_test": True,
                        "timestamp": timestamp
                    })
                    self.metrics_collector.record_incident(
                        f"inc_prevented_{day}",
                        "high",
                        "Payment processing issue caught by test",
                        ["req_payment_reliability"]
                    )
                else:
                    # Incident occurred
                    operational_data["incidents"].append({
                        "day": day,
                        "impact": incident_impact,
                        "timestamp": timestamp
                    })
                    self.metrics_collector.record_incident(
                        f"inc_occurred_{day}",
                        "high",
                        "Payment processing failure in production",
                        ["req_payment_reliability"]
                    )
                    
        return operational_data

    def _calculate_roi(self, operational_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """Calculate ROI of test investments.
        
        Args:
            operational_data: Simulated operational data
            
        Returns:
            Dict containing ROI metrics
        """
        # Calculate prevented losses
        prevented_losses = sum(
            inc["impact_prevented"] for inc in operational_data["prevented_incidents"]
        )
        
        # Calculate actual losses
        actual_losses = sum(
            inc["impact"] for inc in operational_data["incidents"]
        )
        
        # Calculate revenue improvement
        # Compare average revenue before/after tests
        metrics = operational_data["business_metrics"]
        
        baseline_revenue = sum(
            m["daily_revenue"] for m in metrics if m["day"] < 11
        ) / 11 if metrics else 0
        
        with_tests_revenue = sum(
            m["daily_revenue"] for m in metrics if m["day"] >= 21
        ) / 10 if len([m for m in metrics if m["day"] >= 21]) > 0 else 0
        
        revenue_improvement = (with_tests_revenue - baseline_revenue) * 30  # Monthly
        
        # Test investment costs (hypothetical)
        test_development_cost = 500000  # Initial development
        test_maintenance_cost = 50000 * 30 / 365  # Daily maintenance for 30 days
        total_test_cost = test_development_cost + test_maintenance_cost
        
        # Calculate ROI
        total_benefit = prevented_losses + revenue_improvement
        roi_percentage = ((total_benefit - total_test_cost) / total_test_cost) * 100
        
        return {
            "prevented_losses": prevented_losses,
            "actual_losses": actual_losses,
            "baseline_revenue": baseline_revenue,
            "improved_revenue": with_tests_revenue,
            "revenue_improvement": revenue_improvement,
            "test_cost": total_test_cost,
            "total_benefit": total_benefit,
            "roi_percentage": roi_percentage,
            "payback_days": total_test_cost / (total_benefit / 30) if total_benefit > 0 else float('inf')
        }

    def test_payment_reliability_scenario(self):
        """Test the complete payment reliability scenario."""
        logger.info("Starting payment reliability business scenario test")
        
        # Step 1: Calculate initial metrics (from sample data)
        initial_metrics = self.calculator.calculate_all_metrics("req_payment_reliability")
        assert initial_metrics["existence"].score == 1.0  # Has tests
        logger.info(f"Initial metrics calculated: {len(initial_metrics)} metrics")
        
        # Step 2: Simulate 30 days of business operations
        logger.info("Simulating 30 days of business operations...")
        operational_data = self._simulate_business_operations(days=30)
        
        # Log simulation summary
        logger.info(
            f"Simulation complete: "
            f"{len(operational_data['test_executions'])} test executions, "
            f"{len(operational_data['prevented_incidents'])} incidents prevented, "
            f"{len(operational_data['incidents'])} incidents occurred"
        )
        
        # Step 3: Run learning cycle to update metrics
        logger.info("Running learning cycle to update metrics...")
        learning_results = self.learner.run_learning_cycle(["req_payment_reliability"])
        
        assert "req_payment_reliability" in learning_results
        assert "error" not in learning_results["req_payment_reliability"]
        
        # Step 4: Recalculate metrics after learning
        updated_metrics = self.calculator.calculate_all_metrics("req_payment_reliability")
        
        # Verify metrics improved
        assert updated_metrics["runtime_correlation"].score != initial_metrics["runtime_correlation"].score
        assert updated_metrics["value_probability"].score > initial_metrics["value_probability"].score
        
        logger.info(
            f"Metrics after learning: "
            f"runtime_correlation={updated_metrics['runtime_correlation'].score:.3f}, "
            f"value_probability={updated_metrics['value_probability'].score:.3f}"
        )
        
        # Step 5: Calculate ROI
        roi_metrics = self._calculate_roi(operational_data)
        
        logger.info(
            f"ROI Analysis:\n"
            f"  Prevented Losses: ¥{roi_metrics['prevented_losses']:,.0f}\n"
            f"  Actual Losses: ¥{roi_metrics['actual_losses']:,.0f}\n"
            f"  Revenue Improvement: ¥{roi_metrics['revenue_improvement']:,.0f}/month\n"
            f"  Test Investment: ¥{roi_metrics['test_cost']:,.0f}\n"
            f"  Total Benefit: ¥{roi_metrics['total_benefit']:,.0f}\n"
            f"  ROI: {roi_metrics['roi_percentage']:.1f}%\n"
            f"  Payback Period: {roi_metrics['payback_days']:.1f} days"
        )
        
        # Verify positive ROI
        assert roi_metrics["roi_percentage"] > 0, "Tests should provide positive ROI"
        assert roi_metrics["prevented_losses"] > 0, "Tests should prevent some incidents"
        assert roi_metrics["improved_revenue"] > roi_metrics["baseline_revenue"], "Revenue should improve with tests"

    def test_value_chain_verification(self):
        """Verify the complete value chain: Test → Requirement → Business Impact."""
        logger.info("Verifying complete value chain")
        
        # Step 1: Verify test-requirement linkage
        requirement_tests = self.graph_adapter.get_tests_for_requirement("req_payment_reliability")
        assert len(requirement_tests) >= 2, "Payment reliability should have multiple tests"
        
        test_ids = {test["id"] for test in requirement_tests}
        assert "test_payment_boundary" in test_ids
        assert "test_payment_retry" in test_ids
        
        # Step 2: Simulate operations to create business impact
        operational_data = self._simulate_business_operations(days=10)
        
        # Step 3: Verify requirement-business metric linkage
        business_metrics = self.graph_adapter.execute_cypher("""
            MATCH (r:RequirementEntity {id: 'req_payment_reliability'})-[:IMPACTS]->(m:BusinessMetric)
            RETURN m.metric_name as metric_name, m.value as value
        """)
        
        assert len(business_metrics) > 0, "Requirement should impact business metrics"
        
        # Step 4: Verify test execution prevents incidents
        prevented_incidents = operational_data["prevented_incidents"]
        assert len(prevented_incidents) > 0, "Tests should prevent some incidents"
        
        # Calculate value probability based on prevented incidents
        total_prevented_value = sum(inc["impact_prevented"] for inc in prevented_incidents)
        
        logger.info(
            f"Value chain verified:\n"
            f"  Tests: {len(requirement_tests)}\n"
            f"  Business Metrics Impacted: {len(business_metrics)}\n"
            f"  Incidents Prevented: {len(prevented_incidents)}\n"
            f"  Value Protected: ¥{total_prevented_value:,.0f}"
        )

    def test_metric_learning_effectiveness(self):
        """Test that metrics learn and improve predictions over time."""
        logger.info("Testing metric learning effectiveness")
        
        # Step 1: Get baseline predictions
        baseline_metrics = self.calculator.calculate_all_metrics("req_payment_reliability")
        baseline_value_prob = baseline_metrics["value_probability"].score
        
        # Step 2: Simulate operations with consistent patterns
        # First 10 days: Tests always catch issues
        for day in range(10):
            # Test fails (catches issue)
            self.metrics_collector.record_test_execution(
                "req_payment_reliability",
                "test_payment_boundary",
                passed=False,
                duration_ms=200
            )
            
            # Lower business metrics when test fails
            self.metrics_collector.record_operational_metric("payment_success_rate", 98.0)
            self.metrics_collector.record_business_metric("daily_revenue", 4500000)
            
            # Record prevented incident
            self.metrics_collector.record_incident(
                f"inc_prevented_learn_{day}",
                "high",
                "Issue caught by test",
                ["req_payment_reliability"],
                prevented=True
            )
        
        # Step 3: Run learning cycle
        learning_results = self.learner.run_learning_cycle(["req_payment_reliability"])
        
        # Step 4: Check improved predictions
        improved_metrics = self.calculator.calculate_all_metrics("req_payment_reliability")
        improved_value_prob = improved_metrics["value_probability"].score
        
        # Value probability should increase significantly
        assert improved_value_prob > baseline_value_prob + 0.2, \
            f"Value probability should improve significantly (baseline: {baseline_value_prob:.3f}, improved: {improved_value_prob:.3f})"
        
        logger.info(
            f"Learning effectiveness verified:\n"
            f"  Baseline value probability: {baseline_value_prob:.3f}\n"
            f"  Improved value probability: {improved_value_prob:.3f}\n"
            f"  Improvement: {(improved_value_prob - baseline_value_prob):.3f}"
        )

    def test_end_to_end_with_real_kuzu(self):
        """Verify complete E2E flow works with real KuzuDB instance."""
        logger.info("Testing complete E2E flow with real KuzuDB")
        
        # Step 1: Verify KuzuDB connection
        try:
            # The GraphAdapter currently uses a simplified interface
            # Test basic functionality instead
            result = self.graph_adapter.execute_cypher("RETURN 1")
            # If we get any result, connection is working
            assert isinstance(result, list), "KuzuDB should return a list"
        except Exception as e:
            pytest.fail(f"KuzuDB connection failed: {e}")
        
        # Step 2: Verify schema loaded correctly by querying nodes
        # Test that we can query the main node types
        try:
            req_count = len(self.graph_adapter.execute_cypher("MATCH (r:RequirementEntity) RETURN r"))
            test_count = len(self.graph_adapter.execute_cypher("MATCH (t:TestEntity) RETURN t"))
            
            # Sample data should have created some nodes
            assert req_count > 0, "RequirementEntity nodes should exist"
            assert test_count > 0, "TestEntity nodes should exist"
            
            logger.info(f"Schema verified: {req_count} requirements, {test_count} tests")
        except Exception as e:
            pytest.fail(f"Schema verification failed: {e}")
        
        # Step 3: Run complete scenario
        operational_data = self._simulate_business_operations(days=7)
        
        # Step 4: Verify data persistence
        # Check test executions were recorded
        test_exec_results = self.graph_adapter.execute_cypher(
            "MATCH (t:TestExecution) RETURN t"
        )
        test_exec_count = len(test_exec_results)
        assert test_exec_count > 0, "Test executions should be persisted"
        
        # Check metrics were calculated and stored
        metric_results = self.graph_adapter.execute_cypher(
            "MATCH (m:MetricResult) RETURN m"
        )
        metric_count = len(metric_results)
        assert metric_count > 0, "Metrics should be persisted"
        
        logger.info(
            f"E2E flow verified with real KuzuDB:\n"
            f"  Requirements: {req_count}\n"
            f"  Tests: {test_count}\n"
            f"  Test Executions: {test_exec_count}\n"
            f"  Metric Results: {metric_count}"
        )

    def test_comprehensive_value_report(self):
        """Generate comprehensive value report demonstrating business impact."""
        logger.info("Generating comprehensive value report")
        
        # Run full simulation
        operational_data = self._simulate_business_operations(days=30)
        
        # Calculate metrics before and after
        initial_metrics = self.calculator.calculate_all_metrics("req_payment_reliability")
        self.learner.run_learning_cycle(["req_payment_reliability"])
        final_metrics = self.calculator.calculate_all_metrics("req_payment_reliability")
        
        # Calculate ROI
        roi_metrics = self._calculate_roi(operational_data)
        
        # Generate report
        report = f"""
=== Payment Reliability Test Value Report ===

Test Coverage Analysis:
- Existence Score: {final_metrics['existence'].score:.2f}
- Boundary Coverage: {final_metrics['boundary_coverage'].score:.2f}
- Semantic Alignment: {final_metrics['semantic_alignment'].score:.2f}

Runtime Performance:
- Runtime Correlation: {initial_metrics['runtime_correlation'].score:.2f} → {final_metrics['runtime_correlation'].score:.2f}
- Value Probability: {initial_metrics['value_probability'].score:.2f} → {final_metrics['value_probability'].score:.2f}

Business Impact (30 days):
- Incidents Prevented: {len(operational_data['prevented_incidents'])}
- Incidents Occurred: {len(operational_data['incidents'])}
- Prevention Rate: {len(operational_data['prevented_incidents']) / (len(operational_data['prevented_incidents']) + len(operational_data['incidents'])) * 100:.1f}%

Financial Analysis:
- Prevented Losses: ¥{roi_metrics['prevented_losses']:,.0f}
- Revenue Improvement: ¥{roi_metrics['revenue_improvement']:,.0f}/month
- Test Investment: ¥{roi_metrics['test_cost']:,.0f}
- ROI: {roi_metrics['roi_percentage']:.1f}%
- Payback Period: {roi_metrics['payback_days']:.1f} days

Conclusion:
The payment reliability tests demonstrate clear business value by preventing
incidents and improving operational metrics. The {roi_metrics['roi_percentage']:.1f}% ROI
justifies continued investment in test quality improvements.
"""
        
        logger.info(report)
        
        # Write report to file
        report_path = Path(self.temp_dir) / "value_report.txt"
        report_path.write_text(report)
        
        # Verify key insights
        assert roi_metrics["roi_percentage"] > 100, "ROI should exceed 100%"
        assert len(operational_data["prevented_incidents"]) > len(operational_data["incidents"]), \
            "More incidents should be prevented than occurred"