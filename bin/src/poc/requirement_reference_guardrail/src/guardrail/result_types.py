"""
Result type definitions for requirement_reference_guardrail.

This module provides Result types following the error handling convention:
Union[SuccessType, ErrorDict] pattern using TypedDict.
"""
from typing import Union, TypedDict, List, Optional, Any, Literal


class ErrorResult(TypedDict):
    """Base error result structure."""
    ok: Literal[False]
    error: str
    details: Optional[dict[str, Any]]


class DetectCategorySuccess(TypedDict):
    """Success result for detect_security_category."""
    ok: Literal[True]
    category: Optional[str]


class DetectCategoryError(ErrorResult):
    """Error result for detect_security_category."""
    pass


# Result type for detect_security_category
DetectCategoryResult = Union[DetectCategorySuccess, DetectCategoryError]


class CheckComplianceSuccess(TypedDict):
    """Success result for check_reference_compliance."""
    ok: Literal[True]
    compliant: bool
    message: Optional[str]


class CheckComplianceError(ErrorResult):
    """Error result for check_reference_compliance."""
    pass


# Result type for check_reference_compliance
CheckComplianceResult = Union[CheckComplianceSuccess, CheckComplianceError]


class GuardrailValidationSuccess(TypedDict):
    """Success result for guardrail validation."""
    ok: Literal[True]
    requirement_id: str
    category: Optional[str]
    compliant: bool
    message: Optional[str]
    reference_ids: List[str]


class GuardrailValidationError(ErrorResult):
    """Error result for guardrail validation."""
    requirement_id: Optional[str]


# Result type for guardrail validation operations
GuardrailValidationResult = Union[GuardrailValidationSuccess, GuardrailValidationError]


class ExceptionRequestSuccess(TypedDict):
    """Success result for creating an exception request."""
    ok: Literal[True]
    exception_id: str
    requirement_id: str
    status: str


class ExceptionRequestError(ErrorResult):
    """Error result for creating an exception request."""
    requirement_id: Optional[str]


# Result type for exception request operations
ExceptionRequestResult = Union[ExceptionRequestSuccess, ExceptionRequestError]


class RequirementQuerySuccess(TypedDict):
    """Success result for querying requirements."""
    ok: Literal[True]
    requirements: List[dict[str, Any]]
    total_count: int


class RequirementQueryError(ErrorResult):
    """Error result for querying requirements."""
    query: Optional[str]


# Result type for requirement query operations
RequirementQueryResult = Union[RequirementQuerySuccess, RequirementQueryError]


class ReferenceQuerySuccess(TypedDict):
    """Success result for querying references."""
    ok: Literal[True]
    references: List[dict[str, Any]]
    total_count: int


class ReferenceQueryError(ErrorResult):
    """Error result for querying references."""
    entity_type: Optional[str]


# Result type for reference query operations
ReferenceQueryResult = Union[ReferenceQuerySuccess, ReferenceQueryError]