"""Tests for result type definitions."""
import pytest
from typing import assert_type
from guardrail.result_types import (
    DetectCategoryResult,
    CheckComplianceResult,
    GuardrailValidationResult,
    ExceptionRequestResult,
    RequirementQueryResult,
    ReferenceQueryResult,
    DetectCategorySuccess,
    DetectCategoryError,
    CheckComplianceSuccess,
    CheckComplianceError,
    GuardrailValidationSuccess,
    GuardrailValidationError,
    ExceptionRequestSuccess,
    ExceptionRequestError,
    RequirementQuerySuccess,
    RequirementQueryError,
    ReferenceQuerySuccess,
    ReferenceQueryError
)


def test_detect_category_success():
    """Test DetectCategorySuccess type."""
    result: DetectCategorySuccess = {
        "ok": True,
        "category": "authentication"
    }
    assert result["ok"] is True
    assert result["category"] == "authentication"
    
    # Test with None category
    result_none: DetectCategorySuccess = {
        "ok": True,
        "category": None
    }
    assert result_none["ok"] is True
    assert result_none["category"] is None


def test_detect_category_error():
    """Test DetectCategoryError type."""
    result: DetectCategoryError = {
        "ok": False,
        "error": "Failed to analyze description",
        "details": {"reason": "empty description"}
    }
    assert result["ok"] is False
    assert result["error"] == "Failed to analyze description"
    assert result["details"]["reason"] == "empty description"
    
    # Test without details
    result_no_details: DetectCategoryError = {
        "ok": False,
        "error": "Unknown error",
        "details": None
    }
    assert result_no_details["ok"] is False
    assert result_no_details["error"] == "Unknown error"
    assert result_no_details["details"] is None


def test_check_compliance_success():
    """Test CheckComplianceSuccess type."""
    result: CheckComplianceSuccess = {
        "ok": True,
        "compliant": True,
        "message": None
    }
    assert result["ok"] is True
    assert result["compliant"] is True
    assert result["message"] is None
    
    # Test non-compliant with message
    result_non_compliant: CheckComplianceSuccess = {
        "ok": True,
        "compliant": False,
        "message": "Missing required ASVS reference"
    }
    assert result_non_compliant["ok"] is True
    assert result_non_compliant["compliant"] is False
    assert result_non_compliant["message"] == "Missing required ASVS reference"


def test_guardrail_validation_success():
    """Test GuardrailValidationSuccess type."""
    result: GuardrailValidationSuccess = {
        "ok": True,
        "requirement_id": "req_001",
        "category": "authentication",
        "compliant": True,
        "message": None,
        "reference_ids": ["ASVS-V2.1", "NIST-IA-01"]
    }
    assert result["ok"] is True
    assert result["requirement_id"] == "req_001"
    assert result["category"] == "authentication"
    assert result["compliant"] is True
    assert result["message"] is None
    assert len(result["reference_ids"]) == 2


def test_guardrail_validation_error():
    """Test GuardrailValidationError type."""
    result: GuardrailValidationError = {
        "ok": False,
        "error": "Database connection failed",
        "details": {"host": "localhost", "port": 5432},
        "requirement_id": "req_001"
    }
    assert result["ok"] is False
    assert result["error"] == "Database connection failed"
    assert result["details"]["host"] == "localhost"
    assert result["requirement_id"] == "req_001"
    
    # Test without requirement_id
    result_no_req: GuardrailValidationError = {
        "ok": False,
        "error": "Invalid input",
        "details": None,
        "requirement_id": None
    }
    assert result_no_req["ok"] is False
    assert result_no_req["error"] == "Invalid input"
    assert result_no_req["requirement_id"] is None


def test_exception_request_success():
    """Test ExceptionRequestSuccess type."""
    result: ExceptionRequestSuccess = {
        "ok": True,
        "exception_id": "exc_123",
        "requirement_id": "req_001",
        "status": "pending_approval"
    }
    assert result["ok"] is True
    assert result["exception_id"] == "exc_123"
    assert result["requirement_id"] == "req_001"
    assert result["status"] == "pending_approval"


def test_requirement_query_success():
    """Test RequirementQuerySuccess type."""
    result: RequirementQuerySuccess = {
        "ok": True,
        "requirements": [
            {"id": "req_001", "description": "User authentication"},
            {"id": "req_002", "description": "Session management"}
        ],
        "total_count": 2
    }
    assert result["ok"] is True
    assert len(result["requirements"]) == 2
    assert result["total_count"] == 2


def test_reference_query_success():
    """Test ReferenceQuerySuccess type."""
    result: ReferenceQuerySuccess = {
        "ok": True,
        "references": [
            {"entity_id": "ASVS-V2.1", "title": "Authentication Verification"},
            {"entity_id": "NIST-IA-01", "title": "Identity and Authentication"}
        ],
        "total_count": 2
    }
    assert result["ok"] is True
    assert len(result["references"]) == 2
    assert result["total_count"] == 2


def test_union_types():
    """Test that union types work correctly."""
    # Test DetectCategoryResult
    success_result: DetectCategoryResult = {
        "ok": True,
        "category": "authentication"
    }
    assert success_result["ok"] is True
    
    error_result: DetectCategoryResult = {
        "ok": False,
        "error": "Failed",
        "details": None
    }
    assert error_result["ok"] is False
    
    # Test CheckComplianceResult
    compliance_success: CheckComplianceResult = {
        "ok": True,
        "compliant": True,
        "message": None
    }
    assert compliance_success["ok"] is True
    
    compliance_error: CheckComplianceResult = {
        "ok": False,
        "error": "Invalid input",
        "details": None
    }
    assert compliance_error["ok"] is False