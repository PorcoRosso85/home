"""Growth prediction functions for auto-scale market system.

This module provides functions to predict user and revenue growth based on
the growth factor K, implementing exponential growth for K > 1 and linear
growth for K < 1.
"""

from typing import Union, TypedDict
import math


class GrowthPredictionError(TypedDict):
    """Error type for growth prediction failures."""
    ok: bool
    error: str


class UserGrowthResult(TypedDict):
    """Success type for user growth prediction."""
    ok: bool
    predicted_users: float
    growth_type: str  # 'exponential' or 'linear'


class RevenueGrowthResult(TypedDict):
    """Success type for revenue growth prediction."""
    ok: bool
    predicted_revenue: float
    growth_type: str  # 'exponential' or 'linear'


class CriticalMassResult(TypedDict):
    """Success type for critical mass estimation."""
    ok: bool
    periods_to_critical_mass: float
    growth_type: str  # 'exponential' or 'linear'


def predict_user_growth(
    initial_users: float,
    growth_factor_k: float,
    time_periods: int
) -> Union[UserGrowthResult, GrowthPredictionError]:
    """Predict user growth based on growth factor K and time periods.
    
    Args:
        initial_users: Starting number of users
        growth_factor_k: Growth factor (K > 1 for exponential, K < 1 for linear)
        time_periods: Number of time periods to predict
        
    Returns:
        UserGrowthResult on success, GrowthPredictionError on failure
    """
    # Validate inputs
    if initial_users < 0:
        return GrowthPredictionError(
            ok=False,
            error="Initial users must be non-negative"
        )
    
    if growth_factor_k <= 0:
        return GrowthPredictionError(
            ok=False,
            error="Growth factor K must be positive"
        )
    
    if time_periods < 0:
        return GrowthPredictionError(
            ok=False,
            error="Time periods must be non-negative"
        )
    
    # Calculate predicted users
    if growth_factor_k > 1:
        # Exponential growth: U(t) = U0 * K^t
        predicted_users = initial_users * math.pow(growth_factor_k, time_periods)
        growth_type = "exponential"
    else:
        # Linear growth: U(t) = U0 * (1 + K*t)
        predicted_users = initial_users * (1 + growth_factor_k * time_periods)
        growth_type = "linear"
    
    return UserGrowthResult(
        ok=True,
        predicted_users=predicted_users,
        growth_type=growth_type
    )


def predict_revenue_growth(
    initial_revenue: float,
    growth_factor_k: float,
    time_periods: int,
    revenue_per_user: float
) -> Union[RevenueGrowthResult, GrowthPredictionError]:
    """Predict revenue growth based on user growth and revenue per user.
    
    Args:
        initial_revenue: Starting revenue
        growth_factor_k: Growth factor (K > 1 for exponential, K < 1 for linear)
        time_periods: Number of time periods to predict
        revenue_per_user: Average revenue per user
        
    Returns:
        RevenueGrowthResult on success, GrowthPredictionError on failure
    """
    # Validate inputs
    if initial_revenue < 0:
        return GrowthPredictionError(
            ok=False,
            error="Initial revenue must be non-negative"
        )
    
    if revenue_per_user <= 0:
        return GrowthPredictionError(
            ok=False,
            error="Revenue per user must be positive"
        )
    
    # Calculate initial users from revenue
    initial_users = initial_revenue / revenue_per_user
    
    # Get user growth prediction
    user_result = predict_user_growth(initial_users, growth_factor_k, time_periods)
    
    if not user_result["ok"]:
        return GrowthPredictionError(
            ok=False,
            error=user_result["error"]
        )
    
    # Calculate predicted revenue
    predicted_revenue = user_result["predicted_users"] * revenue_per_user
    
    return RevenueGrowthResult(
        ok=True,
        predicted_revenue=predicted_revenue,
        growth_type=user_result["growth_type"]
    )


def estimate_critical_mass(
    initial_users: float,
    critical_mass_threshold: float,
    growth_factor_k: float
) -> Union[CriticalMassResult, GrowthPredictionError]:
    """Estimate time periods needed to reach critical mass.
    
    Args:
        initial_users: Starting number of users
        critical_mass_threshold: Target number of users for critical mass
        growth_factor_k: Growth factor (K > 1 for exponential, K < 1 for linear)
        
    Returns:
        CriticalMassResult on success, GrowthPredictionError on failure
    """
    # Validate inputs
    if initial_users <= 0:
        return GrowthPredictionError(
            ok=False,
            error="Initial users must be positive"
        )
    
    if critical_mass_threshold <= initial_users:
        return GrowthPredictionError(
            ok=False,
            error="Critical mass threshold must be greater than initial users"
        )
    
    if growth_factor_k <= 0:
        return GrowthPredictionError(
            ok=False,
            error="Growth factor K must be positive"
        )
    
    # Calculate periods to critical mass
    if growth_factor_k > 1:
        # Exponential: solve for t in threshold = initial * K^t
        # t = log(threshold/initial) / log(K)
        periods_to_critical_mass = (
            math.log(critical_mass_threshold / initial_users) / 
            math.log(growth_factor_k)
        )
        growth_type = "exponential"
    elif growth_factor_k < 1:
        # Linear: solve for t in threshold = initial * (1 + K*t)
        # t = (threshold/initial - 1) / K
        periods_to_critical_mass = (
            (critical_mass_threshold / initial_users - 1) / growth_factor_k
        )
        growth_type = "linear"
    else:
        # K = 1 means no growth
        return GrowthPredictionError(
            ok=False,
            error="Growth factor K = 1 results in no growth"
        )
    
    # Check if result is feasible
    if periods_to_critical_mass < 0:
        return GrowthPredictionError(
            ok=False,
            error="Critical mass cannot be reached with given growth factor"
        )
    
    return CriticalMassResult(
        ok=True,
        periods_to_critical_mass=periods_to_critical_mass,
        growth_type=growth_type
    )