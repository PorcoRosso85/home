"""Test to verify pytest configuration for external tests."""

import pytest


def test_external_configuration():
    """Verify that external tests are properly discovered."""
    assert True, "External test discovery works"


@pytest.mark.external
def test_external_marker():
    """Test that the external marker is available."""
    assert True, "External marker test"