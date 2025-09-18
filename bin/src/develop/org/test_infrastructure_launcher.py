#!/usr/bin/env python3
"""
TDD RED: Test for infrastructure.py launcher integration
Testing resolve_claude_launcher() priority and fallback behavior
"""

import pytest
import os
import subprocess
from unittest.mock import patch, MagicMock
import infrastructure


class TestResolveClaude:
    """Test resolve_claude_launcher() priority system"""

    def test_priority_1_environment_variable_success(self):
        """Priority 1: CLAUDE_LAUNCHER environment variable should be highest priority"""
        with patch('infrastructure.variables.get_claude_command_preference') as mock_pref:
            mock_pref.return_value = {'ok': True, 'data': 'custom-claude-cmd'}
            
            result = infrastructure.resolve_claude_launcher()
            
            assert result['ok'] is True
            assert result['data'] == 'custom-claude-cmd'

    def test_priority_2_claude_shell_script(self):
        """Priority 2: claude-shell.sh proven script should be second priority"""
        with patch('infrastructure.variables.get_claude_command_preference') as mock_pref, \
             patch('infrastructure.variables.get_claude_script_path') as mock_script:
            
            # Environment variable fails
            mock_pref.return_value = {'ok': False, 'error': 'CLAUDE_LAUNCHER not set'}
            # Script exists
            mock_script.return_value = {'ok': True, 'data': '/path/to/claude-shell.sh'}
            
            result = infrastructure.resolve_claude_launcher()
            
            assert result['ok'] is True
            assert result['data'] == '/path/to/claude-shell.sh'

    def test_priority_3_system_commands(self):
        """Priority 3: System commands (claude-code, claude) should be third priority"""
        with patch('infrastructure.variables.get_claude_command_preference') as mock_pref, \
             patch('infrastructure.variables.get_claude_script_path') as mock_script, \
             patch('infrastructure.shutil.which') as mock_which:
            
            # Environment variable and script fail
            mock_pref.return_value = {'ok': False, 'error': 'CLAUDE_LAUNCHER not set'}
            mock_script.return_value = {'ok': False, 'error': 'claude-shell.sh not found'}
            
            # claude-code available
            mock_which.side_effect = lambda x: '/usr/bin/claude-code' if x == 'claude-code' else None
            
            result = infrastructure.resolve_claude_launcher()
            
            assert result['ok'] is True
            assert result['data'] == 'claude-code --dangerously-skip-permissions'

    def test_claude_fallback_when_claude_code_unavailable(self):
        """System command fallback: claude when claude-code unavailable"""
        with patch('infrastructure.variables.get_claude_command_preference') as mock_pref, \
             patch('infrastructure.variables.get_claude_script_path') as mock_script, \
             patch('infrastructure.shutil.which') as mock_which:
            
            # Environment variable and script fail
            mock_pref.return_value = {'ok': False, 'error': 'CLAUDE_LAUNCHER not set'}
            mock_script.return_value = {'ok': False, 'error': 'claude-shell.sh not found'}
            
            # claude-code unavailable, claude available
            def which_side_effect(cmd):
                if cmd == 'claude-code':
                    return None
                elif cmd == 'claude':
                    return '/usr/bin/claude'
                return None
            
            mock_which.side_effect = which_side_effect
            
            result = infrastructure.resolve_claude_launcher()
            
            assert result['ok'] is True
            assert result['data'] == 'claude'

    def test_no_fallback_error_aggregation(self):
        """Error handling: No fallback, return aggregated errors"""
        with patch('infrastructure.variables.get_claude_command_preference') as mock_pref, \
             patch('infrastructure.variables.get_claude_script_path') as mock_script, \
             patch('infrastructure.shutil.which') as mock_which:
            
            # All methods fail
            mock_pref.return_value = {'ok': False, 'error': 'CLAUDE_LAUNCHER not set'}
            mock_script.return_value = {'ok': False, 'error': 'claude-shell.sh not found'}
            mock_which.return_value = None  # No system commands available
            
            result = infrastructure.resolve_claude_launcher()
            
            assert result['ok'] is False
            assert 'CLAUDE_LAUNCHER not set' in result['error']
            assert 'claude-shell.sh not found' in result['error']
            assert 'Claude launcher not available' in result['error']

    def test_return_type_structure(self):
        """Ensure function returns proper Dict[str, Any] structure"""
        with patch('infrastructure.variables.get_claude_command_preference') as mock_pref:
            mock_pref.return_value = {'ok': True, 'data': 'test-cmd'}
            
            result = infrastructure.resolve_claude_launcher()
            
            assert isinstance(result, dict)
            assert 'ok' in result
            assert isinstance(result['ok'], bool)
            if result['ok']:
                assert 'data' in result
            else:
                assert 'error' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])