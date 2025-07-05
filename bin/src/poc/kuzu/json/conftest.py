"""
pytest configuration for KuzuDB JSON POC
Based on patterns from bin/src/requirement/graph
"""
import os
import sys
import pytest

# Ensure proper environment setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup and cleanup for each test"""
    # Import and clear cache before test
    from kuzu_json_poc.database_factory import clear_database_cache, reload_kuzu_module
    
    # Clear cache and reload module before test
    clear_database_cache()
    reload_kuzu_module()
    
    yield
    
    # Clear cache after test
    clear_database_cache()
    
    # Reload kuzu module if it exists
    if 'kuzu' in sys.modules:
        try:
            import importlib
            importlib.reload(sys.modules['kuzu'])
        except:
            pass


# Custom markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


# Skip slow tests by default
def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    if not config.getoption("--run-slow", default=False):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom options"""
    parser.addoption(
        "--run-slow", 
        action="store_true", 
        default=False, 
        help="run slow tests"
    )