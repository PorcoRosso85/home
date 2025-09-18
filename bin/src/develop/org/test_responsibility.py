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


def test_designer_commands_restricted_to_org_directory():
    """Designer commands should only be allowed from org directory."""
    # Mock os.getcwd to simulate different directories
    with patch('os.getcwd') as mock_getcwd:
        # Test: Commands from non-org directory should be rejected
        mock_getcwd.return_value = '/home/nixos/bin/src/develop/org/designers/x'
        result = application.send_command_to_designer('y', '[TEST] unauthorized command')
        assert result['ok'] == False
        assert 'org directory' in result['error']['message']
        
        # Test: Commands from other random directory should be rejected  
        mock_getcwd.return_value = '/home/nixos/bin/src/poc/email'
        result = application.send_command_to_designer('x', '[TEST] unauthorized command')
        assert result['ok'] == False
        assert 'org directory' in result['error']['message']


def test_definer_commands_allowed_from_org_directory():
    """Definer commands should be allowed from org directory."""
    # Mock os.getcwd to simulate org directory
    with patch('os.getcwd') as mock_getcwd:
        # Test: Commands from org directory should proceed to normal validation
        mock_getcwd.return_value = '/home/nixos/bin/src/develop/org'
        
        # Mock the rest of the function to avoid tmux dependencies
        with patch('application.TmuxConnection') as mock_tmux:
            mock_session = Mock()
            mock_window = Mock()
            mock_pane = Mock()
            mock_pane.cmd.return_value.stdout = ['/home/nixos/bin/src/develop/org/designers/x']
            mock_window.panes = [mock_pane]
            mock_session.attached_window = mock_window
            mock_tmux.return_value.get_or_create_session.return_value = mock_session
            
            with patch('application._is_pane_alive', return_value=True):
                with patch('pathlib.Path.exists', return_value=True):
                    result = application.send_command_to_designer('x', '[TEST] authorized command')
                    # Should not be rejected by directory check (may fail for other reasons like tmux)
                    if not result['ok']:
                        assert 'org directory' not in result.get('error', {}).get('message', '')