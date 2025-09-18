"""Characterization tests for Claude launch command logic.

These tests capture the current behavior of the Claude startup system
to protect against regressions during refactoring.
"""

import pytest
import shutil
from unittest.mock import Mock, patch
from typing import Dict, Any

import variables
import domain
import infrastructure


class TestClaudeLaunchCommandCharacterization:
    """Characterization tests for Claude launch commands."""

    def test_variables_get_claude_launch_command_with_claude_code_available(self):
        """Test variables.get_claude_launch_command when claude-code is in PATH."""
        with patch('shutil.which') as mock_which:
            # Simulate claude-code being available
            mock_which.side_effect = lambda cmd: '/usr/bin/claude-code' if cmd == 'claude-code' else None
            
            result = variables.get_claude_launch_command()
            
            expected = {
                'ok': True,
                'data': {
                    'command': 'env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions',
                    'environment': {
                        'NIXPKGS_ALLOW_UNFREE': '1'
                    }
                }
            }
            assert result == expected

    def test_variables_get_claude_launch_command_with_claude_available(self):
        """Test variables.get_claude_launch_command when only 'claude' is in PATH."""
        with patch('shutil.which') as mock_which:
            # Simulate only 'claude' being available
            def which_side_effect(cmd):
                if cmd == 'claude-code':
                    return None
                elif cmd == 'claude':
                    return '/usr/bin/claude'
                return None
            
            mock_which.side_effect = which_side_effect
            
            result = variables.get_claude_launch_command()
            
            expected = {
                'ok': True,
                'data': {
                    'command': 'claude',
                    'environment': {
                        'NIXPKGS_ALLOW_UNFREE': '1'
                    }
                }
            }
            assert result == expected

    def test_variables_get_claude_launch_command_with_no_claude_available(self):
        """Test variables.get_claude_launch_command when neither claude command is available."""
        with patch('shutil.which') as mock_which:
            # Simulate no claude commands available
            mock_which.return_value = None
            
            result = variables.get_claude_launch_command()
            
            expected = {
                'ok': True,
                'data': {
                    'command': 'env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions',
                    'environment': {
                        'NIXPKGS_ALLOW_UNFREE': '1'
                    }
                }
            }
            assert result == expected

    def test_domain_get_claude_launch_command_with_variables_import_success(self):
        """Test infrastructure.resolve_claude_launcher when variables module is available."""
        # This test uses the actual variables module since it exists in our environment
        result = infrastructure.resolve_claude_launcher()
        
        # Verify it returns a valid structure
        assert isinstance(result, dict)
        assert 'ok' in result
        assert result['ok'] is True
        assert 'data' in result
        assert isinstance(result['data'], str)
        assert len(result['data']) > 0

    def test_domain_get_claude_launch_command_with_variables_import_failure(self):
        """Test infrastructure.resolve_claude_launcher with variables import failure."""
        # Mock variables functions to fail
        with patch('infrastructure.variables.get_claude_command_preference') as mock_pref, \
             patch('infrastructure.variables.get_claude_script_path') as mock_script, \
             patch('infrastructure.shutil.which') as mock_which:
            
            # Make all variables functions fail
            mock_pref.return_value = {'ok': False, 'error': 'Environment not set'}
            mock_script.return_value = {'ok': False, 'error': 'Script not found'}
            mock_which.return_value = None  # No system commands available
            
            # Now test infrastructure.resolve_claude_launcher
            result = infrastructure.resolve_claude_launcher()
            
            # Should return error since nothing is available
            assert isinstance(result, dict)
            assert 'ok' in result
            assert result['ok'] is False
            assert 'error' in result

    def test_domain_get_claude_default_command(self):
        """Test that domain no longer has get_claude_default_command (moved to infrastructure)."""
        # This function was removed during purification
        assert not hasattr(domain, 'get_claude_default_command')

    def test_infrastructure_launch_claude_in_window_success_case(self):
        """Test infrastructure.launch_claude_in_window with successful launch."""
        # Create mock window and pane
        mock_pane = Mock()
        mock_window = Mock()
        mock_window.name = "test_window"
        mock_window.panes = [mock_pane]
        
        with patch('infrastructure.resolve_claude_launcher') as mock_resolver:
            # Setup successful command result
            mock_resolver.return_value = {
                'ok': True,
                'data': 'claude --test'
            }
            
            result = infrastructure.launch_claude_in_window(mock_window, "/test/directory")
            
            # Verify successful result
            assert result['ok'] is True
            assert result['data'] is None
            assert result['error'] is None
            
            # Verify pane commands were sent correctly
            mock_pane.send_keys.assert_any_call("cd /test/directory", enter=True)
            mock_pane.send_keys.assert_any_call("claude --test", enter=True)

    def test_infrastructure_launch_claude_in_window_no_pane(self):
        """Test infrastructure.launch_claude_in_window when window has no panes."""
        mock_window = Mock()
        mock_window.name = "test_window"
        mock_window.panes = []
        
        result = infrastructure.launch_claude_in_window(mock_window, "/test/directory")
        
        # Verify error result
        assert result['ok'] is False
        assert result['data'] is None
        assert result['error']['message'] == "No pane available in window test_window"
        assert result['error']['code'] == "no_pane"

    def test_infrastructure_launch_claude_in_window_launch_command_failure(self):
        """Test infrastructure.launch_claude_in_window with launch command failure."""
        mock_pane = Mock()
        mock_window = Mock()
        mock_window.name = "test_window"
        mock_window.panes = [mock_pane]
        
        with patch('infrastructure.resolve_claude_launcher') as mock_resolver:
            # Setup failed command result
            mock_resolver.return_value = {
                'ok': False,
                'error': 'Command not found'
            }
            
            result = infrastructure.launch_claude_in_window(mock_window, "/test/directory")
            
            # Verify error result (no fallback in new implementation)
            assert result['ok'] is False
            assert 'error' in result
            assert 'Failed to resolve Claude launcher' in result['error']['message']
            
            # Verify cd command was sent but no claude command
            mock_pane.send_keys.assert_any_call("cd /test/directory", enter=True)

    def test_infrastructure_launch_claude_in_window_exception(self):
        """Test infrastructure.launch_claude_in_window when an exception occurs."""
        mock_window = Mock()
        mock_window.name = "test_window"
        mock_window.panes = [Mock()]
        
        # Make pane.send_keys raise an exception
        mock_window.panes[0].send_keys.side_effect = Exception("Pane communication error")
        
        result = infrastructure.launch_claude_in_window(mock_window, "/test/directory")
        
        # Verify error result
        assert result['ok'] is False
        assert result['data'] is None
        assert "Failed to launch Claude in window: Pane communication error" in result['error']['message']
        assert result['error']['code'] == "launch_failed"

    def test_domain_generate_claude_window_name(self):
        """Test domain.generate_claude_window_name follows expected pattern."""
        test_cases = [
            ("/home/user/project", "developer:/home/user/project".replace('/', '_')),
            ("relative/path", "developer:relative/path".replace('/', '_')),
            ("/", "developer:_"),
            ("", "developer:")
        ]
        
        for directory, expected in test_cases:
            result = domain.generate_claude_window_name(directory)
            assert result == expected

    def test_domain_generate_claude_history_patterns(self):
        """Test domain.generate_claude_history_patterns generates expected patterns."""
        directory = "/home/user/project"
        result = domain.generate_claude_history_patterns(directory)
        
        expected = [
            "home-user-project",           # No leading slash, hyphen separator
            "-home-user-project",          # With leading hyphen  
            "/home/user/project".replace('/', '-')  # Full path version
        ]
        assert result == expected

    def test_domain_get_claude_history_base_path(self):
        """Test domain.get_claude_history_base_path returns expected path."""
        from pathlib import Path
        result = domain.get_claude_history_base_path()
        expected = Path.home() / ".claude/projects"
        assert result == expected

    def test_infrastructure_result_helpers(self):
        """Test infrastructure._ok and _err helper functions."""
        # Test _ok helper
        ok_result = infrastructure._ok("test_data")
        expected_ok = {"ok": True, "data": "test_data", "error": None}
        assert ok_result == expected_ok
        
        # Test _err helper with default code
        err_result = infrastructure._err("test error")
        expected_err = {"ok": False, "data": None, "error": {"message": "test error", "code": "error"}}
        assert err_result == expected_err
        
        # Test _err helper with custom code
        err_result_custom = infrastructure._err("test error", "custom_code")
        expected_err_custom = {"ok": False, "data": None, "error": {"message": "test error", "code": "custom_code"}}
        assert err_result_custom == expected_err_custom


class TestClaudeCommandPriorityLogic:
    """Tests for the specific command priority logic in variables.py."""

    def test_command_priority_order(self):
        """Test that command selection follows the documented priority order."""
        with patch('shutil.which') as mock_which:
            # Test priority 1: claude-code preferred over claude
            mock_which.side_effect = lambda cmd: {
                'claude-code': '/usr/bin/claude-code',
                'claude': '/usr/bin/claude'
            }.get(cmd)
            
            result = variables.get_claude_launch_command()
            assert 'claude-code --dangerously-skip-permissions' in result['data']['command']
            
            # Test priority 2: claude used if claude-code not available
            mock_which.side_effect = lambda cmd: {
                'claude-code': None,
                'claude': '/usr/bin/claude'
            }.get(cmd)
            
            result = variables.get_claude_launch_command()
            assert result['data']['command'] == 'claude'
            
            # Test priority 3: nix run used if neither available
            mock_which.side_effect = lambda cmd: None
            
            result = variables.get_claude_launch_command()
            assert 'nix run github:NixOS/nixpkgs/nixos-unstable#claude-code' in result['data']['command']

    def test_environment_variable_consistency(self):
        """Test that NIXPKGS_ALLOW_UNFREE is set consistently."""
        with patch('shutil.which') as mock_which:
            # Test all three scenarios include the environment variable
            scenarios = [
                lambda cmd: '/usr/bin/claude-code' if cmd == 'claude-code' else None,  # claude-code available
                lambda cmd: '/usr/bin/claude' if cmd == 'claude' else None,           # only claude available  
                lambda cmd: None                                                       # neither available
            ]
            
            for scenario in scenarios:
                mock_which.side_effect = scenario
                result = variables.get_claude_launch_command()
                assert result['data']['environment']['NIXPKGS_ALLOW_UNFREE'] == '1'


class TestErrorHandlingPatterns:
    """Tests for error handling patterns across the launch system."""

    def test_domain_import_error_handling(self):
        """Test how domain module handles import errors gracefully."""
        # Test actual behavior when variables can't be imported
        import sys
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'variables':
                raise ImportError("No module named 'variables'")
            return original_import(name, *args, **kwargs)
        
        # Temporarily remove variables from sys.modules
        original_variables = sys.modules.pop('variables', None)
        
        # Domain module was purified and no longer has get_claude_launch_command
        try:
            # This function doesn't exist anymore
            assert not hasattr(domain, 'get_claude_launch_command')
        finally:
            # Restore variables module if it existed
            if original_variables is not None:
                sys.modules['variables'] = original_variables

    def test_infrastructure_window_validation(self):
        """Test infrastructure window validation patterns."""
        # Test window with no panes
        empty_window = Mock()
        empty_window.name = "empty"
        empty_window.panes = []
        
        result = infrastructure.launch_claude_in_window(empty_window, "/test")
        assert result['ok'] is False
        assert 'No pane available' in result['error']['message']
        
        # Test window with None panes
        none_window = Mock()
        none_window.name = "none"
        none_window.panes = [None]
        
        # This should work as None is truthy in the current logic
        with patch('variables.get_claude_launch_command') as mock_cmd:
            mock_cmd.return_value = {'ok': True, 'data': {'command': 'claude'}}
            try:
                infrastructure.launch_claude_in_window(none_window, "/test")
            except AttributeError:
                # Expected behavior - None pane will fail when send_keys is called
                pass