"""Investigate pytest environment differences"""
import os
import sys
import pytest

def test_environment_info():
    """Print environment info to understand pytest context"""
    print("\n=== Environment Info ===")
    print(f"Python: {sys.version}")
    print(f"Pytest: {pytest.__version__}")
    print(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'NOT SET')}")
    print(f"Process ID: {os.getpid()}")
    print(f"__name__: {__name__}")
    
    # Check if running under pytest
    print(f"\nRunning under pytest: {'pytest' in sys.modules}")
    
    # Check loaded modules
    kuzu_modules = [m for m in sys.modules if 'kuzu' in m]
    print(f"\nKuzu-related modules: {kuzu_modules}")
    
    # This test passes without using JSON extension
    assert True


def test_minimal_kuzu_import():
    """Test minimal kuzu import without JSON"""
    try:
        import kuzu
        print(f"\n✓ Kuzu imported successfully")
        print(f"Kuzu location: {kuzu.__file__}")
        print(f"Has Database: {hasattr(kuzu, 'Database')}")
    except Exception as e:
        print(f"\n✗ Failed to import kuzu: {e}")
        pytest.fail(f"Kuzu import failed: {e}")


@pytest.mark.skip(reason="JSON extension causes segfault")
def test_json_extension_skip():
    """This test is skipped to avoid segfault"""
    pass


if __name__ == "__main__":
    print("Direct execution:")
    test_environment_info()
    test_minimal_kuzu_import()