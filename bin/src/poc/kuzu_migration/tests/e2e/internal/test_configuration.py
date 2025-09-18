"""Test to verify pytest configuration."""

import pytest


def test_pytest_configuration():
    """Verify that pytest is properly configured and can discover tests."""
    assert True, "Basic test to verify pytest configuration"


@pytest.mark.internal
def test_internal_marker():
    """Test that the internal marker is available."""
    assert True, "Internal marker test"


class TestConfiguration:
    """Test class to verify class-based test discovery."""
    
    def test_class_based_discovery(self):
        """Verify that class-based tests are discovered."""
        assert True, "Class-based test discovery works"