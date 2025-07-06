"""pytest configuration for KuzuDB JSON POC"""
import pytest
import sys
import gc


@pytest.fixture(autouse=True)
def cleanup_kuzu_state():
    """Cleanup KuzuDB state after each test"""
    yield
    # Force garbage collection after test
    gc.collect()