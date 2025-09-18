"""Pure unit tests for variables.py purified functions.

Tests for the purified variables module that only handles configuration value retrieval.
Uses Result pattern and follows prohibited_items.md constraints.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch
from typing import Dict, Any

import variables


class TestVariablesPureFunctions:
    """Test the purified configuration retrieval functions."""

    def test_get_claude_command_preference_with_env_set(self):
        """Test get_claude_command_preference when CLAUDE_LAUNCHER is set."""
        with patch.dict(os.environ, {'CLAUDE_LAUNCHER': 'custom-claude-cmd'}, clear=False):
            result = variables.get_claude_command_preference()
            
            expected = {'ok': True, 'data': 'custom-claude-cmd'}
            assert result == expected
            assert isinstance(result, dict)
            assert 'ok' in result
            assert result['ok'] is True

    def test_get_claude_command_preference_with_env_unset(self):
        """Test get_claude_command_preference when CLAUDE_LAUNCHER is not set."""
        # Temporarily remove CLAUDE_LAUNCHER if it exists
        original_value = os.environ.pop('CLAUDE_LAUNCHER', None)
        try:
            result = variables.get_claude_command_preference()
            
            expected = {'ok': False, 'error': 'CLAUDE_LAUNCHER not set'}
            assert result == expected
            assert isinstance(result, dict)
            assert 'ok' in result
            assert result['ok'] is False
            assert 'error' in result
        finally:
            # Restore original value if it existed
            if original_value is not None:
                os.environ['CLAUDE_LAUNCHER'] = original_value

    def test_get_claude_command_preference_with_empty_env(self):
        """Test get_claude_command_preference when CLAUDE_LAUNCHER is empty string."""
        with patch.dict(os.environ, {'CLAUDE_LAUNCHER': ''}, clear=False):
            result = variables.get_claude_command_preference()
            
            # Empty string is falsy, so should return error
            expected = {'ok': False, 'error': 'CLAUDE_LAUNCHER not set'}
            assert result == expected

    def test_get_claude_script_path_when_exists(self):
        """Test get_claude_script_path when claude-shell.sh exists."""
        # Mock Path.exists to return True
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            result = variables.get_claude_script_path()
            
            # Verify result structure
            assert isinstance(result, dict)
            assert 'ok' in result
            assert result['ok'] is True
            assert 'data' in result
            assert isinstance(result['data'], str)
            # Should contain the expected path structure
            assert 'claude/ui/claude-shell.sh' in result['data']

    def test_get_claude_script_path_when_missing(self):
        """Test get_claude_script_path when claude-shell.sh does not exist."""
        # Mock Path.exists to return False
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = variables.get_claude_script_path()
            
            expected = {'ok': False, 'error': 'claude-shell.sh not found'}
            assert result == expected
            assert isinstance(result, dict)
            assert result['ok'] is False

    def test_result_pattern_compliance(self):
        """Test that all functions follow Result pattern strictly."""
        # Test successful cases return dict with ok: True, data
        with patch.dict(os.environ, {'CLAUDE_LAUNCHER': 'test'}, clear=False):
            result = variables.get_claude_command_preference()
            assert set(result.keys()) == {'ok', 'data'}
            assert result['ok'] is True

        with patch('pathlib.Path.exists', return_value=True):
            result = variables.get_claude_script_path()
            assert set(result.keys()) == {'ok', 'data'}
            assert result['ok'] is True

    def test_no_exception_throwing(self):
        """Test that functions never throw exceptions."""
        # Test with missing environment variable
        original_value = os.environ.pop('CLAUDE_LAUNCHER', None)
        try:
            result = variables.get_claude_command_preference()
            assert isinstance(result, dict)  # Should not throw
        finally:
            if original_value is not None:
                os.environ['CLAUDE_LAUNCHER'] = original_value

        # Test with file operations
        with patch('pathlib.Path.exists', side_effect=PermissionError("Access denied")):
            # Even with filesystem errors, should not throw
            result = variables.get_claude_script_path()
            assert isinstance(result, dict)  # Should not throw

    def test_path_construction_correctness(self):
        """Test that claude-shell.sh path is constructed correctly."""
        with patch('pathlib.Path.exists', return_value=True):
            result = variables.get_claude_script_path()
            
            # Verify path construction
            path_str = result['data']
            path = Path(path_str)
            
            # Should end with claude/ui/claude-shell.sh
            assert path.name == 'claude-shell.sh'
            assert path.parent.name == 'ui'
            assert path.parent.parent.name == 'claude'