#!/usr/bin/env python3
"""
Example usage of ReferenceEntity Repository with DDL migration

This demonstrates:
1. Applying the DDL schema migration
2. Creating and managing reference entities
3. Creating IMPLEMENTS relationships
4. Querying the graph
"""
import os
import sys
from reference_repository import create_reference_repository


def main():
    print("=== ReferenceEntity Repository Example ===\n")
    
    # Step 1: Apply DDL migration
    print("Step 1: Applying DDL schema migration...")
    # In production, you would run: python3 migrate_ddl.py
    # For this example, we'll create an in-memory database with schema
    
    import kuzu
    db = kuzu.Database(":memory:")
    conn = kuzu.Connection(db)
    
    # Apply DDL (normally done by migration script)
    print("Creating schema...")
    conn.execute("""
        CREATE NODE TABLE ReferenceEntity (
            uri STRING PRIMARY KEY,
            title STRING,
            description STRING DEFAULT '',
            entity_type STRING,
            metadata STRING DEFAULT '{}',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE REL TABLE IMPLEMENTS (
            FROM ReferenceEntity TO ReferenceEntity,
            implementation_type STRING DEFAULT 'implements',
            confidence DOUBLE DEFAULT 1.0,
            created_at TIMESTAMP
        )
    """)
    print("✓ Schema created\n")
    
    # Step 2: Create repository
    print("Step 2: Creating repository...")
    os.environ["URI_SKIP_SCHEMA_CHECK"] = "true"
    repo = create_reference_repository(existing_db=db)
    del os.environ["URI_SKIP_SCHEMA_CHECK"]
    print("✓ Repository created\n")
    
    # Step 3: Create some reference entities
    print("Step 3: Creating reference entities...")
    
    # ISO standard clauses
    iso_references = [
        {
            "uri": "iso:9001:2015/clause/4.1",
            "title": "Understanding the organization and its context",
            "description": "The organization shall determine external and internal issues that are relevant to its purpose",
            "entity_type": "standard_clause"
        },
        {
            "uri": "iso:9001:2015/clause/4.2",
            "title": "Understanding the needs and expectations of interested parties",
            "description": "The organization shall determine the interested parties that are relevant to the QMS",
            "entity_type": "standard_clause"
        },
        {
            "uri": "iso:9001:2015/clause/5.1",
            "title": "Leadership and commitment",
            "description": "Top management shall demonstrate leadership and commitment with respect to the QMS",
            "entity_type": "standard_clause"
        }
    ]
    
    for ref in iso_references:
        result = repo["save"](ref)
        print(f"  Created: {ref['uri']}")
    
    # Company procedures implementing ISO clauses
    company_procedures = [
        {
            "uri": "company:acme/proc/context-analysis",
            "title": "Context Analysis Procedure",
            "description": "Procedure for analyzing organizational context per ISO 9001:2015",
            "entity_type": "procedure",
            "metadata": '{"version": "2.0", "owner": "Quality Department"}'
        },
        {
            "uri": "company:acme/proc/stakeholder-analysis",
            "title": "Stakeholder Analysis Procedure",
            "description": "Procedure for identifying and analyzing interested parties",
            "entity_type": "procedure",
            "metadata": '{"version": "1.5", "owner": "Quality Department"}'
        },
        {
            "uri": "company:acme/policy/quality-policy",
            "title": "Quality Policy",
            "description": "ACME Corporation Quality Policy Statement",
            "entity_type": "policy",
            "metadata": '{"approved_by": "CEO", "effective_date": "2024-01-01"}'
        }
    ]
    
    for proc in company_procedures:
        result = repo["save"](proc)
        print(f"  Created: {proc['uri']}")
    
    print("✓ Reference entities created\n")
    
    # Step 4: Create implementation relationships
    print("Step 4: Creating implementation relationships...")
    
    implementations = [
        ("company:acme/proc/context-analysis", "iso:9001:2015/clause/4.1", "procedural", 0.95),
        ("company:acme/proc/stakeholder-analysis", "iso:9001:2015/clause/4.2", "procedural", 0.90),
        ("company:acme/policy/quality-policy", "iso:9001:2015/clause/5.1", "policy", 0.85)
    ]
    
    for source, target, impl_type, confidence in implementations:
        result = repo["add_implementation"](source, target, impl_type, confidence)
        if result.get("success"):
            print(f"  ✓ {source} -> {target}")
        else:
            print(f"  ✗ Failed: {result}")
    
    print("\n")
    
    # Step 5: Query the graph
    print("Step 5: Querying the graph...")
    
    # Find all references
    print("\nAll references:")
    all_refs = repo["find_all"]()
    for ref in all_refs:
        print(f"  - {ref['uri']}: {ref['title']}")
    
    # Find what implements a specific ISO clause
    print("\nWhat implements ISO 9001:2015 clause 4.1?")
    implementations = repo["find_implementations"]("iso:9001:2015/clause/4.1", "incoming")
    for impl in implementations:
        ref = impl["reference"]
        rel = impl["relationship"]
        print(f"  - {ref['uri']} ({rel['type']}, confidence: {rel['confidence']})")
    
    # Find what a procedure implements
    print("\nWhat does the Context Analysis Procedure implement?")
    implementations = repo["find_implementations"]("company:acme/proc/context-analysis", "outgoing")
    for impl in implementations:
        ref = impl["reference"]
        rel = impl["relationship"]
        print(f"  - {ref['uri']} ({rel['type']}, confidence: {rel['confidence']})")
    
    # Search for references
    print("\nSearching for 'context':")
    results = repo["search"]("context")
    for ref in results:
        print(f"  - {ref['uri']}: {ref['title']}")
    
    # Custom query
    print("\nCustom query - Find all procedures with their implementations:")
    result = repo["execute"]("""
        MATCH (proc:ReferenceEntity {entity_type: 'procedure'})
              -[impl:IMPLEMENTS]->
              (target:ReferenceEntity)
        RETURN proc.uri as procedure, 
               target.uri as implements, 
               impl.confidence as confidence
        ORDER BY impl.confidence DESC
    """)
    
    if result["status"] == "success":
        for row in result["data"]:
            print(f"  - {row[0]} implements {row[1]} (confidence: {row[2]})")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    main()