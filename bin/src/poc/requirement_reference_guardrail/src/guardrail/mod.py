"""
Guardrail module - Public API exports.

This module serves as the single entry point for all public APIs from the guardrail module,
following the module design convention where mod.{ext} is the only public interface.
"""

# Core logic functions (no database dependencies)
from .guardrail_logic import (
    detect_security_category,
    check_reference_compliance,
    SECURITY_CATEGORIES,
    SECURITY_KEYWORDS
)

# Database-dependent functions
from .minimal_enforcer import (
    enforce_basic_guardrails,
    create_exception_request
)

# Result types
from .result_types import (
    # Base types
    ErrorResult,
    
    # Category detection types
    DetectCategorySuccess,
    DetectCategoryError,
    DetectCategoryResult,
    
    # Compliance checking types
    CheckComplianceSuccess,
    CheckComplianceError,
    CheckComplianceResult,
    
    # Guardrail validation types
    GuardrailValidationSuccess,
    GuardrailValidationError,
    GuardrailValidationResult,
    
    # Exception request types
    ExceptionRequestSuccess,
    ExceptionRequestError,
    ExceptionRequestResult,
    
    # Query types
    RequirementQuerySuccess,
    RequirementQueryError,
    RequirementQueryResult,
    ReferenceQuerySuccess,
    ReferenceQueryError,
    ReferenceQueryResult
)

# Configuration and environment variables
from .variables import (
    GuardrailConfig,
    GuardrailOptionalConfig,
    get_required_env,
    get_guardrail_config,
    get_optional_config,
    validate_log_level,
    get_database_connection_params,
    is_development_mode,
    get_security_config
)

__all__ = [
    # Core logic functions
    "detect_security_category",
    "check_reference_compliance",
    "SECURITY_CATEGORIES",
    "SECURITY_KEYWORDS",
    
    # Database-dependent functions
    "enforce_basic_guardrails",
    "create_exception_request",
    
    # Base error type
    "ErrorResult",
    
    # Category detection types
    "DetectCategorySuccess",
    "DetectCategoryError",
    "DetectCategoryResult",
    
    # Compliance checking types
    "CheckComplianceSuccess",
    "CheckComplianceError",
    "CheckComplianceResult",
    
    # Guardrail validation types
    "GuardrailValidationSuccess",
    "GuardrailValidationError",
    "GuardrailValidationResult",
    
    # Exception request types
    "ExceptionRequestSuccess",
    "ExceptionRequestError",
    "ExceptionRequestResult",
    
    # Query types
    "RequirementQuerySuccess",
    "RequirementQueryError",
    "RequirementQueryResult",
    "ReferenceQuerySuccess",
    "ReferenceQueryError",
    "ReferenceQueryResult",
    
    # Configuration types
    "GuardrailConfig",
    "GuardrailOptionalConfig",
    
    # Configuration functions
    "get_required_env",
    "get_guardrail_config",
    "get_optional_config",
    "validate_log_level",
    "get_database_connection_params",
    "is_development_mode",
    "get_security_config"
]