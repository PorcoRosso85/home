#!/usr/bin/env python3
"""
Example script demonstrating the minimal guardrail enforcer.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

import kuzu
from guardrail import enforce_basic_guardrails, create_exception_request


def main():
    """Demonstrate guardrail enforcement"""
    # Create in-memory database for demo
    db = kuzu.Database("")
    conn = kuzu.Connection(db)
    
    # Create schema
    print("Creating schema...")
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
    print("\nInserting sample references...")
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
    
    print("\nDemonstrating guardrail enforcement:")
    print("=" * 60)
    
    # Example 1: Non-security requirement (passes without references)
    print("\n1. Non-security requirement:")
    result = enforce_basic_guardrails(
        conn,
        "REQ-001",
        "Display user dashboard with recent activity",
        []
    )
    print(f"   Result: {'✓ Success' if result['success'] else '✗ Failed'}")
    print(f"   References linked: {result['references_linked']}")
    if result['error']:
        print(f"   Error: {result['error']}")
    
    # Example 2: Security requirement with correct reference (passes)
    print("\n2. Authentication requirement with correct reference:")
    result = enforce_basic_guardrails(
        conn,
        "REQ-002",
        "Implement secure user authentication with password hashing",
        ["ASVS-V2.1.1"]
    )
    print(f"   Result: {'✓ Success' if result['success'] else '✗ Failed'}")
    print(f"   References linked: {result['references_linked']}")
    if result['error']:
        print(f"   Error: {result['error']}")
    
    # Example 3: Security requirement with wrong reference (fails)
    print("\n3. Authentication requirement with wrong reference:")
    result = enforce_basic_guardrails(
        conn,
        "REQ-003",
        "Add login functionality with secure session management",
        ["ASVS-V4.1.1"]  # This is for access control, not authentication
    )
    print(f"   Result: {'✓ Success' if result['success'] else '✗ Failed'}")
    print(f"   References linked: {result['references_linked']}")
    if result['error']:
        print(f"   Error: {result['error']}")
    
    # Example 4: Security requirement without references (fails)
    print("\n4. Security requirement without references:")
    result = enforce_basic_guardrails(
        conn,
        "REQ-004",
        "Implement role-based access control for admin panel",
        []
    )
    print(f"   Result: {'✓ Success' if result['success'] else '✗ Failed'}")
    print(f"   References linked: {result['references_linked']}")
    if result['error']:
        print(f"   Error: {result['error']}")
    
    # Example 5: Create exception for legacy system
    print("\n5. Creating exception request:")
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
    print(f"   Result: {'✓ Success' if result['success'] else '✗ Failed'}")
    print(f"   Exception ID: {result['exception_id']}")
    print(f"   Status: {result['status']}")
    
    # Show summary
    print("\n" + "=" * 60)
    print("Summary of created entities:")
    
    # Count requirements
    req_count = conn.execute("""
        MATCH (r:RequirementEntity)
        RETURN COUNT(r)
    """).get_next()[0]
    print(f"Requirements created: {req_count}")
    
    # Count relationships
    impl_count = conn.execute("""
        MATCH ()-[i:IMPLEMENTS]->()
        RETURN COUNT(i)
    """).get_next()[0]
    print(f"IMPLEMENTS relationships: {impl_count}")
    
    # Count exceptions
    exc_count = conn.execute("""
        MATCH (e:ExceptionRequest)
        RETURN COUNT(e)
    """).get_next()[0]
    print(f"Exception requests: {exc_count}")
    
    conn.close()


if __name__ == "__main__":
    main()