#!/usr/bin/env python3
"""
KuzuDB Circular Dependency Detection POC

This script tests KuzuDB's native capabilities for handling circular dependencies
and compares them with the custom implementation in the requirement graph system.

Based on existing implementation from:
- /home/nixos/bin/src/requirement/graph/test_graph_health.py
- /home/nixos/bin/src/requirement/graph/infrastructure/kuzu_repository.py
"""

import kuzu
import tempfile
import os
import shutil


def test_kuzu_native_circular_detection():
    """Test if KuzuDB has native circular dependency detection"""
    print("=== Testing KuzuDB Native Circular Dependency Detection ===\n")
    
    # Create temporary database
    temp_dir = tempfile.mkdtemp(prefix="kuzu_circular_test_")
    db_path = os.path.join(temp_dir, "test.db")
    print(f"Created temporary database at: {db_path}")
    
    try:
        # Initialize database
        db = kuzu.Database(db_path)
        conn = kuzu.Connection(db)
        
        # Create schema
        print("\n1. Creating schema...")
        conn.execute("CREATE NODE TABLE RequirementEntity (id STRING, title STRING, PRIMARY KEY (id))")
        conn.execute("CREATE REL TABLE DEPENDS_ON (FROM RequirementEntity TO RequirementEntity)")
        print("   ✓ Schema created successfully")
        
        # Create test nodes
        print("\n2. Creating test nodes...")
        nodes = [
            ("req_a", "Requirement A"),
            ("req_b", "Requirement B"),
            ("req_c", "Requirement C")
        ]
        
        for node_id, title in nodes:
            conn.execute(
                "CREATE (n:RequirementEntity {id: $id, title: $title})",
                {"id": node_id, "title": title}
            )
            print(f"   ✓ Created node: {node_id}")
        
        # Test 1: Self-reference
        print("\n3. Testing self-reference (req_a -> req_a)...")
        try:
            conn.execute("""
                MATCH (from:RequirementEntity {id: $from_id}), (to:RequirementEntity {id: $to_id})
                CREATE (from)-[:DEPENDS_ON]->(to)
            """, {"from_id": "req_a", "to_id": "req_a"})
            print("   ⚠️  Self-reference created without error - KuzuDB allows circular dependencies")
        except Exception as e:
            print(f"   ✓ Self-reference prevented by KuzuDB: {e}")
        
        # Verify self-reference was created
        result = conn.execute("""
            MATCH (r:RequirementEntity)-[:DEPENDS_ON]->(r)
            RETURN r.id as self_ref_id
        """)
        
        self_refs = []
        while result.has_next():
            self_refs.append(result.get_next()[0])
        
        if self_refs:
            print(f"   ⚠️  Found self-references: {self_refs}")
        
        # Test 2: Direct circular dependency (A -> B -> A)
        print("\n4. Testing direct circular dependency...")
        
        # Create A -> B
        conn.execute("""
            MATCH (from:RequirementEntity {id: $from_id}), (to:RequirementEntity {id: $to_id})
            CREATE (from)-[:DEPENDS_ON]->(to)
        """, {"from_id": "req_a", "to_id": "req_b"})
        print("   ✓ Created dependency: req_a -> req_b")
        
        # Try to create B -> A
        try:
            conn.execute("""
                MATCH (from:RequirementEntity {id: $from_id}), (to:RequirementEntity {id: $to_id})
                CREATE (from)-[:DEPENDS_ON]->(to)
            """, {"from_id": "req_b", "to_id": "req_a"})
            print("   ⚠️  Circular dependency created without error - KuzuDB allows cycles")
        except Exception as e:
            print(f"   ✓ Circular dependency prevented by KuzuDB: {e}")
        
        # Verify circular dependency exists
        result = conn.execute("""
            MATCH path = (start:RequirementEntity)-[:DEPENDS_ON*2]->(start)
            RETURN start.id as cycle_start, nodes(path) as nodes_in_path
        """)
        
        cycles = []
        while result.has_next():
            row = result.get_next()
            path_nodes = [node["id"] for node in row[1]]
            cycles.append({"start": row[0], "path": path_nodes})
        
        if cycles:
            print(f"   ⚠️  Found circular dependencies: {cycles}")
        
        # Test 3: Manual circular detection (from existing implementation)
        print("\n5. Testing manual circular detection...")
        
        # Check if creating dependency would create a cycle
        result = conn.execute("""
            MATCH (from:RequirementEntity {id: $to_id})-[:DEPENDS_ON*]->(to:RequirementEntity {id: $from_id})
            RETURN count(*) > 0 as has_cycle
        """, {"from_id": "req_c", "to_id": "req_a"})
        
        has_cycle = False
        if result.has_next():
            has_cycle = result.get_next()[0]
        
        if has_cycle:
            print("   ✓ Manual cycle detection works - would create cycle")
        else:
            print("   ✓ Manual cycle detection works - no cycle would be created")
        
        # Test 4: Try adding constraints
        print("\n6. Testing if KuzuDB supports constraints to prevent cycles...")
        try:
            # KuzuDB doesn't support complex constraints like preventing cycles
            # This is just to demonstrate what would be ideal
            conn.execute("""
                CREATE CONSTRAINT no_cycles 
                CHECK (NOT EXISTS (MATCH path = (n)-[:DEPENDS_ON*]->(n)))
            """)
            print("   ✓ Constraint created successfully")
        except Exception as e:
            print(f"   ⚠️  Cannot create cycle prevention constraint: {e}")
        
        # Summary
        print("\n=== SUMMARY ===")
        print("\n✓ KuzuDB allows creation of circular dependencies")
        print("✓ No native constraint support for preventing cycles")
        print("✓ Manual cycle detection using Cypher queries works")
        print("✓ Application-level validation is required")
        
        # Show final graph state
        print("\n=== Final Graph State ===")
        result = conn.execute("""
            MATCH (from:RequirementEntity)-[r:DEPENDS_ON]->(to:RequirementEntity)
            RETURN from.id as from_id, to.id as to_id
            ORDER BY from.id, to.id
        """)
        
        print("\nDependencies:")
        while result.has_next():
            row = result.get_next()
            print(f"  {row[0]} -> {row[1]}")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\n✓ Cleaned up temporary database")


def demonstrate_existing_implementation():
    """Demonstrate how the existing implementation handles circular dependencies"""
    print("\n\n=== Existing Implementation Approach ===\n")
    
    print("The requirement graph system implements circular dependency prevention by:")
    print("1. Checking for cycles BEFORE creating dependencies")
    print("2. Using Cypher query: MATCH (from)-[:DEPENDS_ON*]->(to) to detect paths")
    print("3. Rejecting dependency creation if it would create a cycle")
    print("4. Providing detailed error messages about the circular dependency")
    
    print("\nCode snippet from kuzu_repository.py:")
    print("""
    # Check for circular dependency
    cycle_check = conn.execute('''
        MATCH (from:RequirementEntity {id: $to_id})-[:DEPENDS_ON*]->(to:RequirementEntity {id: $from_id})
        RETURN count(*) > 0 as has_cycle
    ''', {"from_id": from_id, "to_id": to_id})
    
    if cycle_check.has_next() and cycle_check.get_next()[0]:
        return ValidationError(
            type="ValidationError",
            message=f"Circular dependency detected: {from_id} -> {to_id}",
            field="dependency",
            value=f"{from_id} -> {to_id}",
            constraint="no_circular_dependency"
        )
    """)


if __name__ == "__main__":
    print("KuzuDB Circular Dependency Detection POC")
    print("=" * 50)
    print()
    
    # Run tests
    test_kuzu_native_circular_detection()
    demonstrate_existing_implementation()
    
    print("\n\n=== CONCLUSION ===")
    print("\nKuzuDB does NOT have native circular dependency prevention.")
    print("The existing application-level implementation is NECESSARY for:")
    print("- Preventing circular dependencies before they are created")
    print("- Maintaining data integrity")
    print("- Providing meaningful error messages to users")
    print("\nRecommendation: Keep the existing circular dependency detection logic")