#!/usr/bin/env python3
"""
Example script demonstrating the minimal guardrail enforcer.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

import kuzu
from guardrail import enforce_basic_guardrails, create_exception_request
from log_py import log


def main():
    """Demonstrate guardrail enforcement"""
    # Create in-memory database for demo
    db = kuzu.Database("")
    conn = kuzu.Connection(db)
    
    # Create schema
    log("info", {"message": "Creating schema"})
    conn.execute("""
        CREATE NODE TABLE RequirementEntity (
            id STRING PRIMARY KEY,
            description STRING,
            status STRING DEFAULT 'pending',
            security_category STRING
        )
    """)
    
    conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            id STRING PRIMARY KEY,
            title STRING,
            description STRING,
            source STRING,
            category STRING,
            level STRING,
            embedding DOUBLE[384],
            version STRING,
            url STRING
        )
    """)
    
    conn.execute("""
        CREATE NODE TABLE ExceptionRequest (
            id STRING PRIMARY KEY,
            reason STRING,
            status STRING DEFAULT 'pending',
            requested_at STRING,
            approved_by STRING,
            approved_at STRING
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IMPLEMENTS (
            FROM RequirementEntity TO ReferenceEntity,
            implementation_type STRING DEFAULT 'full',
            notes STRING
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE HAS_EXCEPTION (
            FROM RequirementEntity TO ExceptionRequest,
            exception_type STRING DEFAULT 'deviation',
            mitigation STRING
        )
    """)
    
    # Insert sample references
    log("info", {"message": "Inserting sample references"})
    references = [
        {
            "id": "ASVS-V2.1.1",
            "title": "Password Requirements",
            "description": "Verify that user set passwords are at least 12 characters in length.",
            "source": "OWASP ASVS 5.0",
            "category": "Authentication",
            "level": "L1",
            "embedding": [0.0] * 384,
            "version": "5.0",
            "url": "https://example.com"
        },
        {
            "id": "ASVS-V4.1.1",
            "title": "Access Control Enforcement",
            "description": "Verify that the application enforces access control rules.",
            "source": "OWASP ASVS 5.0",
            "category": "Access Control",
            "level": "L1",
            "embedding": [0.0] * 384,
            "version": "5.0",
            "url": "https://example.com"
        }
    ]
    
    for ref in references:
        conn.execute("""
            CREATE (r:ReferenceEntity {
                id: $id,
                title: $title,
                description: $description,
                source: $source,
                category: $category,
                level: $level,
                embedding: $embedding,
                version: $version,
                url: $url
            })
        """, ref)
    
    log("info", {"message": "Demonstrating guardrail enforcement"})
    log("info", {"message": "=" * 60})
    
    # Example 1: Non-security requirement (passes without references)
    log("info", {"message": "Example 1: Non-security requirement"})
    result = enforce_basic_guardrails(
        conn,
        "REQ-001",
        "Display user dashboard with recent activity",
        []
    )
    log("info" if result['success'] else "error", {"message": "Enforcement result",
        "example": "1",
        "success": result['success'],
        "references_linked": result['references_linked'],
        "error": result.get('error')
    })
    
    # Example 2: Security requirement with correct reference (passes)
    log("info", {"message": "Example 2: Authentication requirement with correct reference"})
    result = enforce_basic_guardrails(
        conn,
        "REQ-002",
        "Implement secure user authentication with password hashing",
        ["ASVS-V2.1.1"]
    )
    log("info" if result['success'] else "error", {"message": "Enforcement result",
        "example": "2",
        "success": result['success'],
        "references_linked": result['references_linked'],
        "error": result.get('error')
    })
    
    # Example 3: Security requirement with wrong reference (fails)
    log("info", {"message": "Example 3: Authentication requirement with wrong reference"})
    result = enforce_basic_guardrails(
        conn,
        "REQ-003",
        "Add login functionality with secure session management",
        ["ASVS-V4.1.1"]  # This is for access control, not authentication
    )
    log("info" if result['success'] else "error", {"message": "Enforcement result",
        "example": "3",
        "success": result['success'],
        "references_linked": result['references_linked'],
        "error": result.get('error')
    })
    
    # Example 4: Security requirement without references (fails)
    log("info", {"message": "Example 4: Security requirement without references"})
    result = enforce_basic_guardrails(
        conn,
        "REQ-004",
        "Implement role-based access control for admin panel",
        []
    )
    log("info" if result['success'] else "error", {"message": "Enforcement result",
        "example": "4",
        "success": result['success'],
        "references_linked": result['references_linked'],
        "error": result.get('error')
    })
    
    # Example 5: Create exception for legacy system
    log("info", {"message": "Example 5: Creating exception request"})
    # First create a requirement manually
    conn.execute("""
        CREATE (r:RequirementEntity {
            id: 'REQ-LEGACY',
            description: 'Integrate with legacy authentication system',
            status: 'pending'
        })
    """)
    
    result = create_exception_request(
        conn,
        "REQ-LEGACY",
        "Legacy system uses proprietary authentication that cannot comply with ASVS standards",
        "Implement additional monitoring and network isolation for legacy endpoints"
    )
    log("info" if result['success'] else "error", {"message": "Exception request result",
        "success": result['success'],
        "exception_id": result.get('exception_id'),
        "status": result.get('status')
    })
    
    # Show summary
    log("info", {"message": "=" * 60})
    log("info", {"message": "Summary of created entities"})
    
    # Count requirements
    req_count = conn.execute("""
        MATCH (r:RequirementEntity)
        RETURN COUNT(r)
    """).get_next()[0]
    log("info", {"message": "Requirements created", "count": req_count})
    
    # Count relationships
    impl_count = conn.execute("""
        MATCH ()-[i:IMPLEMENTS]->()
        RETURN COUNT(i)
    """).get_next()[0]
    log("info", {"message": "IMPLEMENTS relationships", "count": impl_count})
    
    # Count exceptions
    exc_count = conn.execute("""
        MATCH (e:ExceptionRequest)
        RETURN COUNT(e)
    """).get_next()[0]
    log("info", {"message": "Exception requests", "count": exc_count})
    
    conn.close()


if __name__ == "__main__":
    main()