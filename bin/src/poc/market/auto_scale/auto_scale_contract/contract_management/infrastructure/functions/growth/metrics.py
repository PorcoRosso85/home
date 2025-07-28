"""Growth metrics calculation functions for auto-scale mechanism.

RESPONSIBILITY: Measure and predict viral growth patterns.
AUTO-SCALE CONTRIBUTION: Provides quantitative metrics to identify when the system
achieves self-sustaining growth (K > 1) and exponential network value increase.

This module provides functions to calculate K-factor, network value using
Metcalfe's Law, and growth rates. All functions return structured results
following the error handling conventions.
"""

from typing import TypedDict, Union, Optional, Dict, List
from datetime import datetime


class MetricsData(TypedDict):
    """Calculated metrics data."""
    value: float
    calculation_time: str
    metadata: Optional[Dict[str, str]]


class MetricsSuccess(TypedDict):
    """Successful metrics calculation result."""
    ok: bool  # Always True for success
    metrics: MetricsData
    message: str


class MetricsError(TypedDict):
    """Failed metrics calculation result."""
    ok: bool  # Always False for error
    error: str
    details: Optional[dict]


MetricsResult = Union[MetricsSuccess, MetricsError]


def calculate_k_factor(
    invites_sent: int,
    conversion_rate: float,
    metadata: Optional[Dict[str, str]] = None
) -> MetricsResult:
    """Calculate K-factor (viral coefficient).
    
    AUTO-SCALE: Core metric that determines if the system has achieved viral growth.
    K > 1 means each customer brings more than one new customer, creating 
    exponential growth without additional marketing spend.
    
    K-factor = invites_sent * conversion_rate
    
    Args:
        invites_sent: Average number of invites sent per user
        conversion_rate: Rate at which invites convert to new users (0-1)
        metadata: Optional metadata for the calculation
    
    Returns:
        MetricsResult with K-factor value or error
    """
    try:
        # Validate inputs
        if invites_sent < 0:
            return {
                "ok": False,
                "error": "Invalid invites_sent value",
                "details": {"invites_sent": invites_sent, "reason": "Must be non-negative"}
            }
        
        if not 0 <= conversion_rate <= 1:
            return {
                "ok": False,
                "error": "Invalid conversion_rate value",
                "details": {"conversion_rate": conversion_rate, "reason": "Must be between 0 and 1"}
            }
        
        # Calculate K-factor
        k_factor = invites_sent * conversion_rate
        
        return {
            "ok": True,
            "metrics": {
                "value": k_factor,
                "calculation_time": datetime.utcnow().isoformat(),
                "metadata": metadata
            },
            "message": f"K-factor calculated: {k_factor:.3f}"
        }
    
    except Exception as e:
        return {
            "ok": False,
            "error": "Failed to calculate K-factor",
            "details": {"exception": str(e)}
        }


def calculate_network_value(
    user_count: int,
    value_per_connection: float = 1.0,
    metadata: Optional[Dict[str, str]] = None
) -> MetricsResult:
    """Calculate network value using Metcalfe's Law.
    
    AUTO-SCALE: Demonstrates exponential value creation as the network grows.
    Each new user adds value not just linearly but quadratically, making
    the platform increasingly attractive and creating a self-reinforcing cycle.
    
    V = n² * value_per_connection
    
    Args:
        user_count: Number of users in the network
        value_per_connection: Optional value multiplier per connection (default: 1.0)
        metadata: Optional metadata for the calculation
    
    Returns:
        MetricsResult with network value or error
    """
    try:
        # Validate inputs
        if user_count < 0:
            return {
                "ok": False,
                "error": "Invalid user_count value",
                "details": {"user_count": user_count, "reason": "Must be non-negative"}
            }
        
        if value_per_connection < 0:
            return {
                "ok": False,
                "error": "Invalid value_per_connection",
                "details": {"value_per_connection": value_per_connection, "reason": "Must be non-negative"}
            }
        
        # Calculate network value using Metcalfe's Law
        network_value = (user_count ** 2) * value_per_connection
        
        return {
            "ok": True,
            "metrics": {
                "value": network_value,
                "calculation_time": datetime.utcnow().isoformat(),
                "metadata": metadata
            },
            "message": f"Network value calculated: {network_value:.2f}"
        }
    
    except Exception as e:
        return {
            "ok": False,
            "error": "Failed to calculate network value",
            "details": {"exception": str(e)}
        }


def calculate_growth_rate(
    current_value: float,
    previous_value: float,
    time_period: str = "period",
    metadata: Optional[Dict[str, str]] = None
) -> MetricsResult:
    """Calculate growth rate between two values.
    
    Growth Rate = ((current - previous) / previous) * 100
    
    Args:
        current_value: Current period value
        previous_value: Previous period value
        time_period: Description of the time period (e.g., "month", "week")
        metadata: Optional metadata for the calculation
    
    Returns:
        MetricsResult with growth rate percentage or error
    """
    try:
        # Validate inputs
        if current_value < 0:
            return {
                "ok": False,
                "error": "Invalid current_value",
                "details": {"current_value": current_value, "reason": "Must be non-negative"}
            }
        
        if previous_value <= 0:
            return {
                "ok": False,
                "error": "Invalid previous_value",
                "details": {"previous_value": previous_value, "reason": "Must be positive"}
            }
        
        # Calculate growth rate
        growth_rate = ((current_value - previous_value) / previous_value) * 100
        
        return {
            "ok": True,
            "metrics": {
                "value": growth_rate,
                "calculation_time": datetime.utcnow().isoformat(),
                "metadata": {
                    **(metadata or {}),
                    "time_period": time_period,
                    "current_value": str(current_value),
                    "previous_value": str(previous_value)
                }
            },
            "message": f"Growth rate for {time_period}: {growth_rate:.2f}%"
        }
    
    except Exception as e:
        return {
            "ok": False,
            "error": "Failed to calculate growth rate",
            "details": {"exception": str(e)}
        }