"""Referral relationship establishment functions.

This module provides functions to establish and manage referral relationships
in preparation for future GraphDB integration. All functions return structured
results following the error handling conventions.
"""

from typing import TypedDict, Union, Optional, Dict, List
from datetime import datetime


class ReferralData(TypedDict):
    """Data for a referral relationship."""
    referrer_id: str
    referee_id: str
    established_at: str
    metadata: Optional[Dict[str, str]]


class EstablishmentSuccess(TypedDict):
    """Successful establishment result."""
    ok: bool  # Always True for success
    referral: ReferralData
    message: str


class EstablishmentError(TypedDict):
    """Failed establishment result."""
    ok: bool  # Always False for error
    error: str
    details: Optional[dict]


EstablishmentResult = Union[EstablishmentSuccess, EstablishmentError]


class ValidationSuccess(TypedDict):
    """Successful validation result."""
    ok: bool  # Always True for success
    is_valid: bool
    checks_passed: List[str]


class ValidationError(TypedDict):
    """Failed validation result."""
    ok: bool  # Always False for error
    error: str
    details: Optional[dict]


ValidationResult = Union[ValidationSuccess, ValidationError]


class RemovalSuccess(TypedDict):
    """Successful removal result."""
    ok: bool  # Always True for success
    removed_count: int
    message: str


class RemovalError(TypedDict):
    """Failed removal result."""
    ok: bool  # Always False for error
    error: str
    details: Optional[dict]


RemovalResult = Union[RemovalSuccess, RemovalError]


def establish_referral(
    referrer_id: str,
    referee_id: str,
    metadata: Optional[Dict[str, str]] = None
) -> EstablishmentResult:
    """Establish a new referral relationship between two entities.
    
    Args:
        referrer_id: The ID of the entity making the referral
        referee_id: The ID of the entity being referred
        metadata: Optional metadata about the referral
        
    Returns:
        EstablishmentResult with the created referral or error details
    """
    if not referrer_id or not referee_id:
        return EstablishmentError(
            ok=False,
            error="Invalid referrer or referee ID",
            details={
                "referrer_id": referrer_id,
                "referee_id": referee_id
            }
        )
    
    if referrer_id == referee_id:
        return EstablishmentError(
            ok=False,
            error="Self-referral not allowed",
            details={"id": referrer_id}
        )
    
    # Placeholder for future GraphDB integration
    # This will create a new edge in the referral graph
    referral_data = ReferralData(
        referrer_id=referrer_id,
        referee_id=referee_id,
        established_at=datetime.utcnow().isoformat(),
        metadata=metadata
    )
    
    return EstablishmentSuccess(
        ok=True,
        referral=referral_data,
        message=f"Referral established from {referrer_id} to {referee_id}"
    )


def validate_referral(referrer_id: str, referee_id: str) -> ValidationResult:
    """Validate if a referral relationship can be established.
    
    Checks:
    - Both IDs are valid
    - No self-referral
    - No circular reference would be created
    - Referral doesn't already exist
    
    Args:
        referrer_id: The ID of the proposed referrer
        referee_id: The ID of the proposed referee
        
    Returns:
        ValidationResult indicating if the referral is valid
    """
    checks_passed = []
    
    if not referrer_id or not referee_id:
        return ValidationError(
            ok=False,
            error="Invalid IDs provided",
            details={
                "referrer_id": referrer_id,
                "referee_id": referee_id
            }
        )
    
    # Check for self-referral
    if referrer_id == referee_id:
        return ValidationSuccess(
            ok=True,
            is_valid=False,
            checks_passed=["id_format"]
        )
    
    checks_passed.append("no_self_referral")
    
    # Placeholder checks for future GraphDB integration
    # - Check for existing relationship
    # - Check for circular reference
    # - Check referral limits
    
    return ValidationSuccess(
        ok=True,
        is_valid=True,
        checks_passed=checks_passed
    )


def remove_referral(referrer_id: str, referee_id: str) -> RemovalResult:
    """Remove an existing referral relationship.
    
    Args:
        referrer_id: The ID of the referrer
        referee_id: The ID of the referee
        
    Returns:
        RemovalResult with removal details or error
    """
    if not referrer_id or not referee_id:
        return RemovalError(
            ok=False,
            error="Invalid referrer or referee ID",
            details={
                "referrer_id": referrer_id,
                "referee_id": referee_id
            }
        )
    
    # Placeholder for future GraphDB integration
    # This will remove the edge from the referral graph
    return RemovalSuccess(
        ok=True,
        removed_count=0,
        message=f"No referral found from {referrer_id} to {referee_id}"
    )


def bulk_establish_referrals(
    referrals: List[Dict[str, str]]
) -> List[EstablishmentResult]:
    """Establish multiple referral relationships in batch.
    
    Args:
        referrals: List of referral data containing referrer_id and referee_id
        
    Returns:
        List of EstablishmentResult for each attempted referral
    """
    results = []
    
    for referral in referrals:
        referrer_id = referral.get("referrer_id", "")
        referee_id = referral.get("referee_id", "")
        metadata = referral.get("metadata")
        
        result = establish_referral(referrer_id, referee_id, metadata)
        results.append(result)
    
    return results


def update_referral_metadata(
    referrer_id: str,
    referee_id: str,
    metadata: Dict[str, str]
) -> EstablishmentResult:
    """Update metadata for an existing referral relationship.
    
    Args:
        referrer_id: The ID of the referrer
        referee_id: The ID of the referee
        metadata: New metadata to apply
        
    Returns:
        EstablishmentResult with updated referral or error
    """
    if not referrer_id or not referee_id:
        return EstablishmentError(
            ok=False,
            error="Invalid referrer or referee ID",
            details={
                "referrer_id": referrer_id,
                "referee_id": referee_id
            }
        )
    
    if not metadata:
        return EstablishmentError(
            ok=False,
            error="No metadata provided",
            details={}
        )
    
    # Placeholder for future GraphDB integration
    # This will update the edge properties in the graph
    referral_data = ReferralData(
        referrer_id=referrer_id,
        referee_id=referee_id,
        established_at=datetime.utcnow().isoformat(),
        metadata=metadata
    )
    
    return EstablishmentSuccess(
        ok=True,
        referral=referral_data,
        message=f"Metadata updated for referral from {referrer_id} to {referee_id}"
    )


def check_referral_exists(referrer_id: str, referee_id: str) -> bool:
    """Check if a referral relationship exists between two entities.
    
    Args:
        referrer_id: The ID of the referrer
        referee_id: The ID of the referee
        
    Returns:
        True if the referral exists, False otherwise
    """
    if not referrer_id or not referee_id:
        return False
    
    # Placeholder for future GraphDB integration
    # This will query the graph for the specific edge
    return False