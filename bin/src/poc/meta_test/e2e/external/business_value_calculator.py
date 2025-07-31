"""Business value and ROI calculation utilities.

Provides utilities for calculating the business value of tests,
including ROI, prevented losses, and revenue improvements.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from ...infrastructure.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BusinessImpact:
    """Represents the business impact of tests."""
    
    prevented_losses: float
    actual_losses: float
    baseline_revenue: float
    improved_revenue: float
    revenue_improvement: float
    test_cost: float
    total_benefit: float
    roi_percentage: float
    payback_days: float
    
    def __str__(self) -> str:
        """Format business impact as readable string."""
        return (
            f"Business Impact:\n"
            f"  Prevented Losses: ¥{self.prevented_losses:,.0f}\n"
            f"  Actual Losses: ¥{self.actual_losses:,.0f}\n"
            f"  Revenue Improvement: ¥{self.revenue_improvement:,.0f}/month\n"
            f"  Test Investment: ¥{self.test_cost:,.0f}\n"
            f"  Total Benefit: ¥{self.total_benefit:,.0f}\n"
            f"  ROI: {self.roi_percentage:.1f}%\n"
            f"  Payback Period: {self.payback_days:.1f} days"
        )


class BusinessValueCalculator:
    """Calculates business value and ROI of test investments."""
    
    def __init__(self, 
                 test_development_cost: float = 500000,
                 daily_test_maintenance_cost: float = 50000):
        """Initialize calculator with cost parameters.
        
        Args:
            test_development_cost: Initial cost to develop tests
            daily_test_maintenance_cost: Daily cost to maintain tests
        """
        self.test_development_cost = test_development_cost
        self.daily_test_maintenance_cost = daily_test_maintenance_cost
        
    def calculate_business_impact(self,
                                  operational_data: Dict[str, List[Dict]],
                                  evaluation_days: int = 30) -> BusinessImpact:
        """Calculate complete business impact from operational data.
        
        Args:
            operational_data: Dict containing test_executions, business_metrics, 
                            incidents, and prevented_incidents
            evaluation_days: Number of days to evaluate
            
        Returns:
            BusinessImpact with calculated metrics
        """
        # Calculate prevented losses
        prevented_losses = self._calculate_prevented_losses(
            operational_data.get("prevented_incidents", [])
        )
        
        # Calculate actual losses
        actual_losses = self._calculate_actual_losses(
            operational_data.get("incidents", [])
        )
        
        # Calculate revenue metrics
        revenue_metrics = self._calculate_revenue_metrics(
            operational_data.get("business_metrics", [])
        )
        
        # Calculate test costs
        total_test_cost = self._calculate_test_cost(evaluation_days)
        
        # Calculate total benefit and ROI
        monthly_revenue_improvement = revenue_metrics["improvement"] * 30
        total_benefit = prevented_losses + monthly_revenue_improvement
        
        roi_percentage = 0.0
        payback_days = float('inf')
        
        if total_test_cost > 0:
            roi_percentage = ((total_benefit - total_test_cost) / total_test_cost) * 100
            
        if total_benefit > 0:
            daily_benefit = total_benefit / evaluation_days
            payback_days = total_test_cost / daily_benefit
            
        return BusinessImpact(
            prevented_losses=prevented_losses,
            actual_losses=actual_losses,
            baseline_revenue=revenue_metrics["baseline"],
            improved_revenue=revenue_metrics["improved"],
            revenue_improvement=monthly_revenue_improvement,
            test_cost=total_test_cost,
            total_benefit=total_benefit,
            roi_percentage=roi_percentage,
            payback_days=payback_days
        )
    
    def _calculate_prevented_losses(self, prevented_incidents: List[Dict]) -> float:
        """Calculate total prevented losses from incidents caught by tests."""
        return sum(
            incident.get("impact_prevented", 0) 
            for incident in prevented_incidents
        )
    
    def _calculate_actual_losses(self, incidents: List[Dict]) -> float:
        """Calculate total actual losses from incidents that occurred."""
        return sum(
            incident.get("impact", 0) 
            for incident in incidents
        )
    
    def _calculate_revenue_metrics(self, business_metrics: List[Dict]) -> Dict[str, float]:
        """Calculate revenue metrics comparing periods with/without tests."""
        if not business_metrics:
            return {"baseline": 0.0, "improved": 0.0, "improvement": 0.0}
            
        # Group metrics by test coverage period
        baseline_metrics = [
            m for m in business_metrics if m.get("day", 0) < 11
        ]
        
        comprehensive_test_metrics = [
            m for m in business_metrics if m.get("day", 0) >= 21
        ]
        
        # Calculate averages
        baseline_revenue = 0.0
        if baseline_metrics:
            baseline_revenue = sum(
                m.get("daily_revenue", 0) for m in baseline_metrics
            ) / len(baseline_metrics)
            
        improved_revenue = 0.0
        if comprehensive_test_metrics:
            improved_revenue = sum(
                m.get("daily_revenue", 0) for m in comprehensive_test_metrics
            ) / len(comprehensive_test_metrics)
            
        daily_improvement = improved_revenue - baseline_revenue
        
        return {
            "baseline": baseline_revenue,
            "improved": improved_revenue,
            "improvement": daily_improvement
        }
    
    def _calculate_test_cost(self, days: int) -> float:
        """Calculate total test cost for the evaluation period."""
        maintenance_cost = self.daily_test_maintenance_cost * days / 365
        return self.test_development_cost + maintenance_cost
    
    def calculate_test_effectiveness(self,
                                     test_executions: List[Dict],
                                     prevented_incidents: List[Dict]) -> Dict[str, float]:
        """Calculate test effectiveness metrics.
        
        Args:
            test_executions: List of test execution records
            prevented_incidents: List of prevented incident records
            
        Returns:
            Dict with effectiveness metrics
        """
        if not test_executions:
            return {
                "detection_rate": 0.0,
                "false_positive_rate": 0.0,
                "mean_time_to_detect": 0.0
            }
            
        # Calculate detection rate
        failed_tests = [t for t in test_executions if not t.get("passed", True)]
        detection_rate = len(prevented_incidents) / len(failed_tests) if failed_tests else 0.0
        
        # Calculate false positive rate (tests that failed but no incident)
        false_positives = len(failed_tests) - len(prevented_incidents)
        false_positive_rate = false_positives / len(failed_tests) if failed_tests else 0.0
        
        # Calculate mean time to detect (average test duration for failed tests)
        if failed_tests:
            total_duration = sum(t.get("duration_ms", 0) for t in failed_tests)
            mean_time_to_detect = total_duration / len(failed_tests) / 1000  # Convert to seconds
        else:
            mean_time_to_detect = 0.0
            
        return {
            "detection_rate": detection_rate,
            "false_positive_rate": max(0.0, false_positive_rate),  # Ensure non-negative
            "mean_time_to_detect": mean_time_to_detect
        }
    
    def generate_value_report(self,
                              business_impact: BusinessImpact,
                              test_effectiveness: Dict[str, float],
                              requirement_id: str) -> str:
        """Generate comprehensive value report.
        
        Args:
            business_impact: Calculated business impact
            test_effectiveness: Test effectiveness metrics
            requirement_id: Requirement being analyzed
            
        Returns:
            Formatted report string
        """
        return f"""
=== Test Value Analysis Report ===
Requirement: {requirement_id}
Generated: {datetime.now().isoformat()}

{str(business_impact)}

Test Effectiveness:
  Detection Rate: {test_effectiveness['detection_rate']:.1%}
  False Positive Rate: {test_effectiveness['false_positive_rate']:.1%}
  Mean Time to Detect: {test_effectiveness['mean_time_to_detect']:.1f}s

Key Insights:
  • Tests prevented ¥{business_impact.prevented_losses:,.0f} in potential losses
  • Revenue improved by ¥{business_impact.revenue_improvement:,.0f}/month
  • Investment pays back in {business_impact.payback_days:.0f} days
  • {business_impact.roi_percentage:.0f}% return on test investment

Recommendations:
  • {"Maintain current test coverage" if business_impact.roi_percentage > 100 else "Improve test effectiveness"}
  • {"Consider expanding test scenarios" if test_effectiveness['detection_rate'] < 0.8 else "Current detection rate is excellent"}
  • {"Investigate false positives" if test_effectiveness['false_positive_rate'] > 0.2 else "False positive rate is acceptable"}
"""
    
    def calculate_cumulative_value(self,
                                   daily_impacts: List[BusinessImpact]) -> Dict[str, List[float]]:
        """Calculate cumulative value over time.
        
        Args:
            daily_impacts: List of daily business impacts
            
        Returns:
            Dict with cumulative metrics over time
        """
        cumulative = {
            "days": list(range(1, len(daily_impacts) + 1)),
            "cumulative_benefit": [],
            "cumulative_cost": [],
            "cumulative_roi": []
        }
        
        total_benefit = 0.0
        total_cost = 0.0
        
        for i, impact in enumerate(daily_impacts):
            total_benefit += impact.total_benefit
            total_cost += impact.test_cost
            
            cumulative["cumulative_benefit"].append(total_benefit)
            cumulative["cumulative_cost"].append(total_cost)
            
            if total_cost > 0:
                roi = ((total_benefit - total_cost) / total_cost) * 100
                cumulative["cumulative_roi"].append(roi)
            else:
                cumulative["cumulative_roi"].append(0.0)
                
        return cumulative