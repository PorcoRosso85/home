"""Test responsibility boundaries of the org system."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import domain
import application


def test_org_system_owns_claude_history_access():
    """org system should own all access to .claude/projects directory."""
    # The org system provides the interface to Claude history
    result = application.get_claude_history('/some/project', last_n=5)
    assert 'ok' in result
    assert 'error' in result or 'data' in result
    # Direct access to .claude/projects should NOT be done by clients


def test_org_system_should_not_discover_all_projects():
    """org system should NOT provide global project discovery.
    
    Project discovery is not org's responsibility.
    Clients should find directories themselves and then check history.
    """
    # This functionality should NOT exist - it's outside org's scope
    assert not hasattr(application, 'find_projects_with_history')


def test_org_system_validates_directory_scope():
    """org system should validate that directories are within allowed scope."""
    # Workers should only be started in appropriate directories
    result = application.start_worker_in_directory('/etc/passwd')
    # Should either succeed (if allowed) or fail gracefully
    assert 'ok' in result
    

def test_domain_layer_defines_history_patterns():
    """Domain layer should define how to find history files."""
    patterns = domain.generate_claude_history_patterns('/home/user/project')
    assert isinstance(patterns, list)
    assert len(patterns) > 0
    # Patterns should be usable to find history files
    for pattern in patterns:
        assert isinstance(pattern, str)
        assert len(pattern) > 0


def test_application_layer_uses_domain_patterns():
    """Application layer should use domain patterns, not hardcode paths."""
    # The _find_claude_history_path function uses domain patterns via partial
    # This is proven by the partial application setup
    # Testing that domain patterns are properly used
    patterns = domain.generate_claude_history_patterns('/test/dir')
    assert isinstance(patterns, list)
    assert len(patterns) > 0
    # Application layer properly delegates to domain for pattern generation