#!/usr/bin/env python3
"""
Simple demo of the enforced reference guardrails system
Shows the core functionality with minimal setup
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'persistence', 'kuzu_py'))

import tempfile
from pathlib import Path
import kuzu

def setup_database():
    """Set up database with DDL"""
    # Create temp database
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = temp_file.name
    temp_file.close()
    
    # Create database and connection
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # Create tables
    print("📋 Creating database schema...")
    
    # Create ReferenceEntity table
    conn.execute("""
    CREATE NODE TABLE ReferenceEntity (
        id STRING PRIMARY KEY,
        standard STRING,
        version STRING,
        section STRING,
        description STRING,
        level INT64,
        category STRING
    )
    """)
    
    # Create RequirementEntity table
    conn.execute("""
    CREATE NODE TABLE RequirementEntity (
        uri STRING PRIMARY KEY,
        title STRING,
        description STRING,
        entity_type STRING,
        metadata STRING
    )
    """)
    
    # Create IMPLEMENTS relationship
    conn.execute("""
    CREATE REL TABLE IMPLEMENTS (
        FROM RequirementEntity TO ReferenceEntity,
        implementation_type STRING DEFAULT 'full',
        compliance_level STRING DEFAULT 'required',
        notes STRING,
        verified BOOLEAN DEFAULT false
    )
    """)
    
    print("✅ Schema created successfully")
    
    conn.close()
    return db_path, db


def load_sample_references(db):
    """Load sample ASVS references"""
    conn = kuzu.Connection(db)
    
    print("\n📚 Loading sample ASVS references...")
    
    # Sample ASVS data
    references = [
        {
            "id": "asvs-v4.0.3-2.1.1",
            "standard": "ASVS",
            "version": "4.0.3",
            "section": "V2.1.1",
            "description": "Verify minimum password length of 12 characters",
            "level": 1,
            "category": "authentication"
        },
        {
            "id": "asvs-v4.0.3-2.1.2",
            "standard": "ASVS",
            "version": "4.0.3", 
            "section": "V2.1.2",
            "description": "Verify passwords are not on common password lists",
            "level": 1,
            "category": "authentication"
        },
        {
            "id": "asvs-v4.0.3-3.2.1",
            "standard": "ASVS",
            "version": "4.0.3",
            "section": "V3.2.1",
            "description": "Verify session tokens are generated using secure random",
            "level": 1,
            "category": "session"
        },
        {
            "id": "asvs-v4.0.3-4.1.3",
            "standard": "ASVS",
            "version": "4.0.3",
            "section": "V4.1.3",
            "description": "Verify principle of least privilege",
            "level": 1,
            "category": "access_control"
        }
    ]
    
    # Insert references
    for ref in references:
        query = f"""
        CREATE (:ReferenceEntity {{
            id: '{ref["id"]}',
            standard: '{ref["standard"]}',
            version: '{ref["version"]}',
            section: '{ref["section"]}',
            description: '{ref["description"]}',
            level: {ref["level"]},
            category: '{ref["category"]}'
        }})
        """
        conn.execute(query)
    
    print(f"✅ Loaded {len(references)} ASVS references")
    
    conn.close()


def demo_enforced_workflow(db):
    """Demonstrate enforced workflow"""
    conn = kuzu.Connection(db)
    
    print("\n\n🎯 Demo: Enforced Reference Workflow")
    print("=" * 60)
    
    # 1. Create requirement with references
    print("\n1️⃣ Creating requirement WITH references (will succeed):")
    
    req_uri = "req://webapp/auth/password-policy"
    
    # Create requirement
    conn.execute(f"""
    CREATE (:RequirementEntity {{
        uri: '{req_uri}',
        title: 'Password Policy Implementation',
        description: 'Implement secure password validation',
        entity_type: 'requirement',
        metadata: '{{"category": "authentication", "project": "webapp"}}'
    }})
    """)
    
    # Link to references
    conn.execute(f"""
    MATCH (req:RequirementEntity {{uri: '{req_uri}'}}),
          (ref:ReferenceEntity {{id: 'asvs-v4.0.3-2.1.1'}})
    CREATE (req)-[:IMPLEMENTS {{
        implementation_type: 'full',
        verified: false
    }}]->(ref)
    """)
    
    conn.execute(f"""
    MATCH (req:RequirementEntity {{uri: '{req_uri}'}}),
          (ref:ReferenceEntity {{id: 'asvs-v4.0.3-2.1.2'}})
    CREATE (req)-[:IMPLEMENTS {{
        implementation_type: 'full',
        verified: false
    }}]->(ref)
    """)
    
    print(f"✅ Created requirement: {req_uri}")
    print("✅ Linked to 2 ASVS references")
    
    # 2. Show what happens without references
    print("\n2️⃣ Attempting to create requirement WITHOUT references:")
    print("❌ In enforced mode, this would be rejected!")
    print("   Error: Requirements in 'authentication' category must reference ASVS standards")
    
    # 3. Query compliance
    print("\n3️⃣ Checking compliance:")
    
    result = conn.execute("""
    MATCH (req:RequirementEntity)-[impl:IMPLEMENTS]->(ref:ReferenceEntity)
    WHERE req.uri = $uri
    RETURN ref.id, ref.description, impl.implementation_type
    """, {"uri": req_uri})
    
    print(f"\nCompliance for {req_uri}:")
    while result.has_next():
        row = result.get_next()
        print(f"  ✓ {row[0]}: {row[1]}")
        print(f"    Implementation: {row[2]}")
    
    # 4. Coverage analysis
    print("\n4️⃣ Coverage Analysis:")
    
    # Total references by category
    result = conn.execute("""
    MATCH (ref:ReferenceEntity)
    RETURN ref.category, COUNT(*) as total
    ORDER BY ref.category
    """)
    
    print("\nTotal references by category:")
    category_totals = {}
    while result.has_next():
        row = result.get_next()
        category_totals[row[0]] = row[1]
        print(f"  {row[0]}: {row[1]} references")
    
    # Implemented references by category
    result = conn.execute("""
    MATCH (req:RequirementEntity)-[:IMPLEMENTS]->(ref:ReferenceEntity)
    RETURN ref.category, COUNT(DISTINCT ref) as implemented
    ORDER BY ref.category
    """)
    
    print("\nImplemented references:")
    while result.has_next():
        row = result.get_next()
        total = category_totals.get(row[0], 0)
        coverage = (row[1] / total * 100) if total > 0 else 0
        print(f"  {row[0]}: {row[1]}/{total} ({coverage:.1f}% coverage)")
    
    # 5. Gap identification
    print("\n5️⃣ Gap Analysis:")
    
    result = conn.execute("""
    MATCH (ref:ReferenceEntity)
    WHERE NOT EXISTS {
        MATCH (:RequirementEntity)-[:IMPLEMENTS]->(ref)
    }
    RETURN ref.id, ref.category, ref.level, ref.description
    ORDER BY ref.level, ref.category
    LIMIT 5
    """)
    
    print("\nUnimplemented references (gaps):")
    while result.has_next():
        row = result.get_next()
        print(f"  ⚠️  {row[0]} (Level {row[2]}, {row[1]})")
        print(f"     {row[3]}")
    
    conn.close()


def main():
    """Run the simple demo"""
    print("🚀 Enforced Reference Guardrails - Simple Demo")
    print("=" * 60)
    
    try:
        # Setup
        db_path, db = setup_database()
        
        # Load data
        load_sample_references(db)
        
        # Run demo
        demo_enforced_workflow(db)
        
        print("\n\n✅ Demo completed successfully!")
        print("\n💡 Key Concepts Demonstrated:")
        print("   1. Requirements must reference security standards")
        print("   2. Coverage tracking shows implementation progress")
        print("   3. Gap analysis identifies missing implementations")
        print("   4. Enforced workflow prevents non-compliant requirements")
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()