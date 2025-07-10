#!/usr/bin/env python3
"""
Test schema initialization behavior to identify issues
"""
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from requirement.graph.infrastructure.apply_ddl_schema import apply_ddl_schema
from requirement.graph.infrastructure.database_factory import create_database, create_connection


def test_schema_re_initialization():
    """Test what happens when schema is initialized twice"""
    print("\n=== Testing Schema Re-initialization ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")

        # First initialization
        print("\n1. First initialization:")
        success1 = apply_ddl_schema(db_path=temp_dir, create_test_data=True)
        print(f"   Result: {'SUCCESS' if success1 else 'FAILED'}")

        if success1:
            # Check what was created
            db = create_database(path=temp_dir)
            conn = create_connection(db)

            try:
                # Count nodes
                result = conn.execute("MATCH (r:RequirementEntity) RETURN count(r) as cnt")
                if result.has_next():
                    count1 = result.get_next()[0]
                    print(f"   RequirementEntity count: {count1}")

                # Add custom data
                print("\n2. Adding custom requirement...")
                conn.execute("""
                    CREATE (r:RequirementEntity {
                        id: 'custom_req_001',
                        title: 'Important Custom Requirement',
                        description: 'This should not be lost',
                        priority: 5,
                        status: 'approved'
                    })
                """)
                print("   Custom requirement added")

            except Exception as e:
                print(f"   Error during first check: {e}")
            finally:
                conn.close()

            # Second initialization - this is the problem area
            print("\n3. Second initialization (re-init):")
            try:
                success2 = apply_ddl_schema(db_path=temp_dir, create_test_data=True)
                print(f"   Result: {'SUCCESS' if success2 else 'FAILED'}")

                # Check if custom data survived
                db2 = create_database(path=temp_dir)
                conn2 = create_connection(db2)

                try:
                    # Check custom requirement
                    result = conn2.execute("MATCH (r:RequirementEntity {id: 'custom_req_001'}) RETURN r.title")
                    if result.has_next():
                        print("   ✓ Custom data PRESERVED after re-init")
                    else:
                        print("   ✗ Custom data LOST after re-init!")

                    # Count all requirements
                    result = conn2.execute("MATCH (r:RequirementEntity) RETURN count(r) as cnt")
                    if result.has_next():
                        count2 = result.get_next()[0]
                        print(f"   Total RequirementEntity count: {count2}")

                except Exception as e:
                    print(f"   Error checking after re-init: {e}")
                finally:
                    conn2.close()

            except Exception as e:
                print(f"   Re-initialization failed with: {e}")


def test_schema_check_without_init():
    """Test repository behavior without schema initialization"""
    print("\n=== Testing Schema Check Without Init ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")

        # Try to check if schema exists
        db = create_database(path=temp_dir)
        conn = create_connection(db)

        print("\n1. Checking if schema exists (before init):")
        try:
            conn.execute("MATCH (n:RequirementEntity) RETURN count(n) LIMIT 1")
            print("   Schema check succeeded - schema exists")
        except Exception as e:
            print(f"   Schema check failed - schema does not exist: {e}")

        conn.close()

        # Now try to create repository without schema
        print("\n2. Creating repository without schema:")
        try:
            os.environ["RGL_SKIP_SCHEMA_CHECK"] = "false"
            from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository
            create_kuzu_repository(db_path=temp_dir)
            print("   ERROR: Repository creation should have failed!")
        except Exception as e:
            print(f"   ✓ Repository creation correctly failed: {e}")
        finally:
            os.environ.pop("RGL_SKIP_SCHEMA_CHECK", None)


def test_schema_status_check():
    """Test different ways to check schema status"""
    print("\n=== Testing Schema Status Check Methods ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        db = create_database(path=temp_dir)
        conn = create_connection(db)

        # Method 1: Try to query a table
        print("\n1. Query table method:")
        try:
            conn.execute("MATCH (n:RequirementEntity) RETURN count(n) LIMIT 1")
            print("   Schema exists")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg.lower() or "table" in error_msg.lower():
                print("   Schema does not exist (table not found)")
            else:
                print(f"   Unexpected error: {e}")

        # Method 2: Check for specific tables
        print("\n2. Check table catalog (if available):")
        try:
            # KuzuDB might have a way to list tables
            result = conn.execute("CALL show_tables() RETURN *")
            print("   Available tables:")
            while result.has_next():
                print(f"   - {result.get_next()}")
        except Exception as e:
            print(f"   Table catalog not available: {e}")

        conn.close()


if __name__ == "__main__":
    test_schema_re_initialization()
    test_schema_check_without_init()
    test_schema_status_check()
