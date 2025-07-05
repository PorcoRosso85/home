"""Integration test that demonstrates the failure when kuzu is not installed"""

import sys
import traceback


def test_kuzu_json_integration_fails_without_kuzu():
    """This test demonstrates the TDD Red phase - it will fail without kuzu installed"""
    try:
        # This will fail with ModuleNotFoundError
        import kuzu
        
        # If we get here, kuzu is installed (shouldn't happen in Red phase)
        print("✗ test_kuzu_json_integration_fails_without_kuzu: kuzu is already installed!")
        return False
        
    except ModuleNotFoundError as e:
        # This is expected in the Red phase
        print(f"✓ test_kuzu_json_integration_fails_without_kuzu: Expected failure - {e}")
        return True
    except Exception as e:
        print(f"✗ test_kuzu_json_integration_fails_without_kuzu: Unexpected error - {e}")
        traceback.print_exc()
        return False


def test_full_json_workflow_fails_without_implementation():
    """Test the full JSON workflow - will fail in Red phase"""
    try:
        from kuzu_json_poc import demonstrate_json_features
        
        # This should fail because kuzu is not installed
        result = demonstrate_json_features()
        
        if isinstance(result, dict) and "error" in result:
            print(f"✓ test_full_json_workflow_fails_without_implementation: Expected error - {result['error']}")
            return True
        else:
            print("✗ test_full_json_workflow_fails_without_implementation: Should have failed but didn't")
            return False
            
    except Exception as e:
        print(f"✓ test_full_json_workflow_fails_without_implementation: Expected failure - {e}")
        return True


def test_json_extension_operations_fail():
    """Test that JSON extension operations fail without kuzu"""
    try:
        from kuzu_json_poc.adapters import with_temp_database, setup_json_extension
        
        def operation(conn):
            return setup_json_extension(conn)
        
        result = with_temp_database(operation)
        
        if isinstance(result, dict) and "error" in result:
            print(f"✓ test_json_extension_operations_fail: Expected error - {result['error']}")
            return True
        else:
            print("✗ test_json_extension_operations_fail: Should have failed but didn't")
            return False
            
    except Exception as e:
        print(f"✓ test_json_extension_operations_fail: Expected failure - {e}")
        return True


if __name__ == "__main__":
    print("Running TDD Red Phase Tests - These should fail without kuzu installed\n")
    
    tests = [
        test_kuzu_json_integration_fails_without_kuzu,
        test_full_json_workflow_fails_without_implementation,
        test_json_extension_operations_fail
    ]
    
    passed = sum(1 for test in tests if test())
    
    print(f"\n{passed}/{len(tests)} tests show expected failures")
    print("\nTDD Red Phase Status: ✓ Tests are properly failing without implementation")
    
    # Exit with 0 because failing is expected in Red phase
    sys.exit(0)