"""
Minimal guardrail enforcer with hardcoded basic enforcement rules.

This module provides a basic implementation of requirement reference guardrails
that can be replaced with GuardrailRule nodes in the future.
"""
from typing import Dict, List, Optional, Tuple, Any
import kuzu

# Import the core logic from guardrail_logic module
from .guardrail_logic import (
    detect_security_category,
    check_reference_compliance,
    SECURITY_CATEGORIES,
    SECURITY_KEYWORDS
)


def enforce_basic_guardrails(
    conn: kuzu.Connection,
    requirement_id: str,
    description: str,
    reference_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Enforce basic guardrail rules for requirement creation.
    
    This function checks if a requirement needs security references based on its
    description and ensures appropriate references are provided. It creates the
    requirement and IMPLEMENTS relationships within a transaction.
    
    Args:
        conn: KuzuDB connection
        requirement_id: Unique identifier for the requirement
        description: The requirement description
        reference_ids: Optional list of ReferenceEntity IDs to link
        
    Returns:
        Dict with keys:
            - success: bool indicating if enforcement passed
            - requirement_created: bool indicating if requirement was created
            - references_linked: List of linked reference IDs
            - error: Optional error message if enforcement failed
    """
    # Detect security category
    category = detect_security_category(description)
    
    # If not security-related, allow creation without references
    if category is None:
        try:
            # Begin transaction
            conn.execute("BEGIN TRANSACTION")
            
            # Create requirement
            conn.execute("""
                CREATE (r:RequirementEntity {
                    id: $id,
                    description: $description,
                    status: 'pending'
                })
            """, {"id": requirement_id, "description": description})
            
            # Link any provided references (optional for non-security requirements)
            linked_refs = []
            if reference_ids:
                for ref_id in reference_ids:
                    try:
                        conn.execute("""
                            MATCH (req:RequirementEntity {id: $req_id})
                            MATCH (ref:ReferenceEntity {id: $ref_id})
                            CREATE (req)-[:IMPLEMENTS {
                                implementation_type: 'full',
                                notes: 'Optional reference for non-security requirement'
                            }]->(ref)
                        """, {"req_id": requirement_id, "ref_id": ref_id})
                        linked_refs.append(ref_id)
                    except Exception:
                        # Reference might not exist, skip it
                        pass
            
            # Commit transaction
            conn.execute("COMMIT")
            
            return {
                "success": True,
                "requirement_created": True,
                "references_linked": linked_refs,
                "error": None
            }
            
        except Exception as e:
            # Rollback on error
            try:
                conn.execute("ROLLBACK")
            except:
                pass
            return {
                "success": False,
                "requirement_created": False,
                "references_linked": [],
                "error": f"Failed to create requirement: {str(e)}"
            }
    
    # Security-related requirement - check compliance
    is_compliant, error_msg = check_reference_compliance(
        category,
        reference_ids or []
    )
    
    if not is_compliant:
        return {
            "success": False,
            "requirement_created": False,
            "references_linked": [],
            "error": error_msg
        }
    
    # Compliance check passed - create requirement and relationships
    try:
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Create requirement
        conn.execute("""
            CREATE (r:RequirementEntity {
                id: $id,
                description: $description,
                status: 'pending',
                security_category: $category
            })
        """, {
            "id": requirement_id,
            "description": description,
            "category": category
        })
        
        # Create IMPLEMENTS relationships
        linked_refs = []
        for ref_id in reference_ids or []:
            try:
                conn.execute("""
                    MATCH (req:RequirementEntity {id: $req_id})
                    MATCH (ref:ReferenceEntity {id: $ref_id})
                    CREATE (req)-[:IMPLEMENTS {
                        implementation_type: 'full',
                        notes: $notes
                    }]->(ref)
                """, {
                    "req_id": requirement_id,
                    "ref_id": ref_id,
                    "notes": f"Required reference for {category} requirement"
                })
                linked_refs.append(ref_id)
            except Exception:
                # Reference might not exist, but we already validated
                # that we have at least one valid reference
                pass
        
        # Verify at least one reference was linked
        if not linked_refs:
            conn.execute("ROLLBACK")
            return {
                "success": False,
                "requirement_created": False,
                "references_linked": [],
                "error": "Failed to link any references - references may not exist in database"
            }
        
        # Commit transaction
        conn.execute("COMMIT")
        
        return {
            "success": True,
            "requirement_created": True,
            "references_linked": linked_refs,
            "error": None
        }
        
    except Exception as e:
        # Rollback on error
        try:
            conn.execute("ROLLBACK")
        except:
            pass
        return {
            "success": False,
            "requirement_created": False,
            "references_linked": [],
            "error": f"Failed to create requirement: {str(e)}"
        }


def create_exception_request(
    conn: kuzu.Connection,
    requirement_id: str,
    reason: str,
    mitigation: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an exception request for a requirement that cannot meet guardrails.
    
    Args:
        conn: KuzuDB connection
        requirement_id: The requirement requesting exception
        reason: Justification for the exception
        mitigation: Optional risk mitigation strategy
        
    Returns:
        Dict with exception request details or error
    """
    import datetime
    
    try:
        # Generate exception ID
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        exception_id = f"EXC-{timestamp}-{requirement_id[:8]}"
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Create exception request
        conn.execute("""
            CREATE (e:ExceptionRequest {
                id: $id,
                reason: $reason,
                status: 'pending',
                requested_at: $requested_at
            })
        """, {
            "id": exception_id,
            "reason": reason,
            "requested_at": datetime.datetime.now().isoformat()
        })
        
        # Link to requirement
        conn.execute("""
            MATCH (req:RequirementEntity {id: $req_id})
            MATCH (exc:ExceptionRequest {id: $exc_id})
            CREATE (req)-[:HAS_EXCEPTION {
                exception_type: 'deviation',
                mitigation: $mitigation
            }]->(exc)
        """, {
            "req_id": requirement_id,
            "exc_id": exception_id,
            "mitigation": mitigation or "No specific mitigation provided"
        })
        
        # Commit transaction
        conn.execute("COMMIT")
        
        return {
            "success": True,
            "exception_id": exception_id,
            "status": "pending",
            "error": None
        }
        
    except Exception as e:
        # Rollback on error
        try:
            conn.execute("ROLLBACK")
        except:
            pass
        return {
            "success": False,
            "exception_id": None,
            "status": None,
            "error": f"Failed to create exception request: {str(e)}"
        }