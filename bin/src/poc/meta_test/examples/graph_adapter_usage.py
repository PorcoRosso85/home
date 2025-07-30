#!/usr/bin/env python3
"""Example usage of the updated GraphAdapter with real KuzuDB."""

import tempfile
from pathlib import Path

from infrastructure.graph_adapter import GraphAdapter


def main():
    """Demonstrate GraphAdapter usage."""
    print("GraphAdapter Usage Example")
    print("=" * 50)

    # Example 1: In-memory database
    print("\n1. Using in-memory database:")
    with GraphAdapter(":memory:") as adapter:
        # Create some test data
        adapter._conn.execute("""
            CREATE (r1:RequirementEntity {
                id: 'REQ-001',
                title: 'User Authentication',
                description: 'Users must be able to authenticate',
                status: 'active'
            })
        """)

        adapter._conn.execute("""
            CREATE (r2:RequirementEntity {
                id: 'REQ-002',
                title: 'Password Reset',
                description: 'Users must be able to reset passwords',
                status: 'active'
            })
        """)

        # Create test specifications
        adapter._conn.execute("""
            CREATE (t1:TestSpecification {
                id: 'TEST-001',
                test_type: 'unit'
            })
        """)

        adapter._conn.execute("""
            CREATE (t2:TestSpecification {
                id: 'TEST-002',
                test_type: 'integration'
            })
        """)

        # Create relationships
        adapter._conn.execute("""
            MATCH (r:RequirementEntity {id: 'REQ-001'})
            MATCH (t:TestSpecification {id: 'TEST-001'})
            CREATE (r)-[:VERIFIED_BY]->(t)
        """)

        adapter._conn.execute("""
            MATCH (r:RequirementEntity {id: 'REQ-001'})
            MATCH (t:TestSpecification {id: 'TEST-002'})
            CREATE (r)-[:VERIFIED_BY]->(t)
        """)

        # Query data
        req = adapter.get_requirement('REQ-001')
        print(f"  Found requirement: {req['title']}")

        tests = adapter.get_tests_for_requirement('REQ-001')
        print(f"  Tests verifying REQ-001: {len(tests)} tests")
        for test in tests:
            print(f"    - {test['id']} ({test['test_type']})")

        # Save metrics
        adapter.save_metric_result('REQ-001', 'coverage', {'value': 0.85})
        adapter.save_metric_result('REQ-001', 'complexity', {'value': 0.3})

        history = adapter.get_metric_history('REQ-001', 'coverage')
        print(f"  Coverage metric history: {history}")

    # Example 2: Persistent database
    print("\n2. Using persistent database:")
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "example_db"

        # First session - create data
        with GraphAdapter(str(db_path)) as adapter:
            adapter._conn.execute("""
                CREATE (r:RequirementEntity {
                    id: 'REQ-003',
                    title: 'Data Persistence',
                    description: 'Data must persist between sessions',
                    status: 'active'
                })
            """)
            print(f"  Created requirement in {db_path}")

        # Second session - verify persistence
        with GraphAdapter(str(db_path)) as adapter:
            req = adapter.get_requirement('REQ-003')
            print(f"  Verified persistence: {req['title']}")

    # Example 3: Cypher export
    print("\n3. Exporting to Cypher:")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cypher', delete=False) as f:
        export_file = f.name

    try:
        with GraphAdapter(":memory:") as adapter:
            # Add some data
            adapter._conn.execute("""
                CREATE (r:RequirementEntity {
                    id: 'REQ-EXPORT',
                    title: 'Export Test',
                    description: 'Testing export functionality',
                    status: 'active'
                })
            """)

            # Export
            adapter.export_to_cypher(export_file)
            print(f"  Exported to: {export_file}")

            # Show first few lines
            content = Path(export_file).read_text()
            lines = content.split('\n')[:3]
            for line in lines:
                if line:
                    print(f"    {line}")
    finally:
        Path(export_file).unlink(missing_ok=True)

    print("\n" + "=" * 50)
    print("Example completed successfully!")


if __name__ == "__main__":
    main()
