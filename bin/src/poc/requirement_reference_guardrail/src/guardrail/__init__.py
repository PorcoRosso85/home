"""
Guardrail module for requirement reference validation.
"""

# Import core logic that doesn't require database dependencies
from .guardrail_logic import (
    detect_security_category,
    check_reference_compliance,
    SECURITY_CATEGORIES,
    SECURITY_KEYWORDS
)

__all__ = [
    "detect_security_category",
    "check_reference_compliance",
    "SECURITY_CATEGORIES",
    "SECURITY_KEYWORDS"
]

# Database-dependent functions can be imported explicitly when needed
# from .minimal_enforcer import enforce_basic_guardrails, create_exception_request