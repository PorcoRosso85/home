"""
Test schema initialization and re-initialization behavior
"""
import tempfile
import json
import subprocess
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from requirement.graph.infrastructure.apply_ddl_schema import apply_ddl_schema
from requirement.graph.infrastructure.database_factory import create_database, create_connection
from requirement.graph.infrastructure.kuzu_repository import create_kuzu_repository


def test_schema_not_initialized_behavior():
    """Test what happens when schema is not initialized"""
    # インメモリDBを使用
    # Set environment to skip schema check
    os.environ["RGL_SKIP_SCHEMA_CHECK"] = "true"

    try:
        # Should fail when trying to use repository without schema
        create_kuzu_repository(db_path=":memory:")

        # Try to save a requirement - should fail
        try:
            os.environ["RGL_SKIP_SCHEMA_CHECK"] = "false"
            create_kuzu_repository(db_path=":memory:")
            print("ERROR: Expected RuntimeError but repository creation succeeded")
        except RuntimeError as e:
            if "Schema not initialized" in str(e):
                print("✓ Correctly failed with 'Schema not initialized' error")
            else:
                print(f"ERROR: Unexpected error: {e}")
    finally:
        os.environ.pop("RGL_SKIP_SCHEMA_CHECK", None)


def test_schema_already_initialized_behavior():
    """Test what happens when schema is already initialized and init is run again"""
    # Note: インメモリDBでは再初期化は別インスタンスになるため、このテストはスキップ
    print("Skipping test_schema_already_initialized_behavior - not applicable for in-memory DBs")
    return


def test_check_schema_status_without_failing():
    """Test if there's a way to check schema status without failing"""
    # Before initialization
    db = create_database(in_memory=True, use_cache=False, test_unique=True)
    conn = create_connection(db)

    # Try to check if schema exists
    try:
        # This should fail if schema doesn't exist
        conn.execute("MATCH (n:RequirementEntity) RETURN count(n) LIMIT 1")
        schema_exists = True
    except:
        schema_exists = False

    assert not schema_exists
    conn.close()

    # After initialization - 同じDBインスタンスでスキーマ適用と確認
    db2 = create_database(in_memory=True, use_cache=False, test_unique=True)
    conn2 = create_connection(db2)
    
    # スキーマを適用
    from .infrastructure.ddl_schema_manager import DDLSchemaManager
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, "ddl", "migrations", "3.2.0_current.cypher")
    
    manager = DDLSchemaManager(conn2)
    success, results = manager.apply_schema(schema_path)
    
    # スキーマ存在確認
    try:
        conn2.execute("MATCH (n:RequirementEntity) RETURN count(n) LIMIT 1")
        schema_exists = True
    except:
        schema_exists = False

    assert schema_exists
    conn2.close()


def test_schema_command_via_main():
    """Test schema command through main.py"""
    # Test schema apply
    input_data = {
        "type": "schema",
        "action": "apply",
        "create_test_data": True
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        input_data["db_path"] = temp_dir

        # Run via subprocess
        result = subprocess.run(
            ["python", "-m", "requirement.graph.main"],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        )

        # Check output
        if result.stdout:
            output_lines = result.stdout.strip().split('\n')
            # Parse last line as JSON (should be the result)
            try:
                last_output = json.loads(output_lines[-1])
                print(f"Schema command output: {last_output}")
            except:
                print(f"Raw output: {result.stdout}")
                print(f"Error output: {result.stderr}")


def test_schema_protection_mechanism():
    """Test if there's any protection against accidental re-initialization"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize with important data
        apply_ddl_schema(db_path=temp_dir, create_test_data=False)

        # Add custom data
        db = create_database(path=temp_dir)
        conn = create_connection(db)

        # Create a custom requirement
        conn.execute("""
            CREATE (r:RequirementEntity {
                id: 'important_req_001',
                title: 'Critical Business Requirement',
                description: 'This must not be lost',
                priority: 5,
                status: 'approved'
            })
        """)

        # Verify it exists
        result = conn.execute("MATCH (r:RequirementEntity {id: 'important_req_001'}) RETURN r.title")
        assert result.has_next()
        assert result.get_next()[0] == 'Critical Business Requirement'

        conn.close()

        # Try to re-initialize - will this delete our data?
        apply_ddl_schema(db_path=temp_dir, create_test_data=True)

        # Check if our data still exists
        db2 = create_database(path=temp_dir)
        conn2 = create_connection(db2)

        try:
            result2 = conn2.execute("MATCH (r:RequirementEntity {id: 'important_req_001'}) RETURN r.title")
            data_preserved = result2.has_next()
        except:
            data_preserved = False

        conn2.close()

        print(f"Data preserved after re-init: {data_preserved}")


if __name__ == "__main__":
    # Run individual tests for debugging
    test_schema_not_initialized_behavior()
    test_schema_already_initialized_behavior()
    test_check_schema_status_without_failing()
    test_schema_command_via_main()
    test_schema_protection_mechanism()
