"""Integration tests for Claude launcher system after normalization.

These tests verify that the normalized components work together correctly
in real-world usage scenarios through application.py.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import application
import infrastructure
import variables
import domain


class TestClaudeLauncherIntegration:
    """Integration tests for the complete Claude launcher pipeline."""

    def test_start_designer_integration_flow(self):
        """Test complete start_designer flow using normalized components."""
        designer_id = 'x'
        
        with patch('libtmux.Server') as mock_server_class:
            # Setup mock tmux environment
            mock_server = Mock()
            mock_session = Mock()
            mock_session.name = "test_session"
            mock_session.attached_window = Mock()
            mock_session.new_window.return_value = Mock()
            
            mock_server_class.return_value = mock_server
            mock_server.sessions = [mock_session]
            
            # Test the integration
            result = application.start_designer(designer_id)
            
            # Verify integration worked
            assert isinstance(result, dict)
            assert 'ok' in result
            
    def test_resolve_claude_launcher_priority_system(self):
        """Test the complete Claude launcher resolution priority system."""
        # Test Priority 1: Environment variable
        with patch.dict('os.environ', {'CLAUDE_LAUNCHER': 'custom-claude'}):
            result = infrastructure.resolve_claude_launcher()
            assert result['ok'] is True
            assert result['data'] == 'custom-claude'
        
        # Test Priority 2: claude-shell.sh script (when env var not set)
        with patch('variables.get_claude_command_preference') as mock_pref, \
             patch('variables.get_claude_script_path') as mock_script:
            
            mock_pref.return_value = {'ok': False, 'error': 'Not set'}
            mock_script.return_value = {'ok': True, 'data': '/path/to/claude-shell.sh'}
            
            result = infrastructure.resolve_claude_launcher()
            assert result['ok'] is True
            assert result['data'] == '/path/to/claude-shell.sh'
    
    def test_launch_claude_end_to_end(self):
        """Test end-to-end Claude launching through infrastructure."""
        # Create mock window and pane
        mock_pane = Mock()
        mock_window = Mock()
        mock_window.panes = [mock_pane]
        
        # Mock the resolver to return a command
        with patch('infrastructure.resolve_claude_launcher') as mock_resolver:
            mock_resolver.return_value = {'ok': True, 'data': 'test-claude-command'}
            
            result = infrastructure.launch_claude_in_window(mock_window, "/test/dir")
            
            # Verify successful launch
            assert result['ok'] is True
            
            # Verify commands were sent in correct order
            calls = mock_pane.send_keys.call_args_list
            assert len(calls) == 2
            assert calls[0][0] == ("cd /test/dir",)
            assert calls[1][0] == ("test-claude-command",)

    def test_domain_business_rules_integration(self):
        """Test that domain business rules work correctly with infrastructure."""
        # Test window name generation
        directory = "/home/nixos/bin/src/project"
        window_name = domain.generate_claude_window_name(directory)
        expected = "developer:_home_nixos_bin_src_project"
        assert window_name == expected
        
        # Test reverse extraction
        extracted = domain.extract_directory_from_window_name(window_name)
        assert extracted == directory
        
        # Test history patterns
        patterns = domain.generate_claude_history_patterns(directory)
        assert len(patterns) >= 3
        assert all(isinstance(p, str) for p in patterns)

    def test_variables_configuration_retrieval(self):
        """Test variables module configuration retrieval patterns."""
        # Test environment preference
        with patch.dict('os.environ', {'CLAUDE_LAUNCHER': 'test-command'}):
            result = variables.get_claude_command_preference()
            assert result['ok'] is True
            assert result['data'] == 'test-command'
        
        # Test script path detection
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            result = variables.get_claude_script_path()
            assert result['ok'] is True
            assert 'claude-shell.sh' in result['data']
        
        # Test launch command fallback logic
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/claude-code'
            result = variables.get_claude_launch_command()
            assert result['ok'] is True
            assert 'claude-code' in result['data']['command']


class TestNormalizationVerification:
    """Verify that normalization goals were achieved."""
    
    def test_functional_separation_verification(self):
        """Verify that each module has distinct responsibilities."""
        # Variables: Only configuration retrieval
        variables_functions = [f for f in dir(variables) if not f.startswith('_')]
        expected_variables = ['get_claude_command_preference', 'get_claude_script_path', 'get_claude_launch_command']
        assert all(f in variables_functions for f in expected_variables)
        
        # Domain: Only business rules
        domain_functions = [f for f in dir(domain) if not f.startswith('_') and callable(getattr(domain, f))]
        business_rule_functions = [
            'generate_claude_window_name',
            'generate_claude_history_patterns', 
            'get_claude_history_base_path',
            'extract_directory_from_window_name',
            'is_worker_window',
            'should_check_pane_alive'
        ]
        assert all(f in domain_functions for f in business_rule_functions)
        
        # Infrastructure: Integration and external system interaction
        infra_functions = [f for f in dir(infrastructure) if not f.startswith('_') and callable(getattr(infrastructure, f))]
        expected_infra = ['resolve_claude_launcher', 'launch_claude_in_window']
        assert all(f in infra_functions for f in expected_infra)
        
    def test_dependency_flow_verification(self):
        """Verify proper dependency flow: variables <- domain <- infrastructure."""
        # Variables should have no internal dependencies (pure configuration)
        # Domain should only use basic Python types (no external deps)
        # Infrastructure should depend on variables and domain
        
        # Test that infrastructure uses variables
        with patch('infrastructure.variables.get_claude_command_preference') as mock_var:
            mock_var.return_value = {'ok': False, 'error': 'test'}
            result = infrastructure.resolve_claude_launcher()
            mock_var.assert_called_once()
        
        # Test that application.py can use all layers
        assert hasattr(application, 'start_designer')
        assert hasattr(application, 'start_developer')

    def test_error_handling_consistency(self):
        """Verify consistent error handling across all modules."""
        # All functions should return Result-style dictionaries
        
        # Test variables error handling
        with patch('os.getenv', return_value=None):
            result = variables.get_claude_command_preference()
            assert 'ok' in result
            assert result['ok'] is False
            assert 'error' in result
        
        # Test infrastructure error handling
        mock_window = Mock()
        mock_window.panes = []  # No panes
        result = infrastructure.launch_claude_in_window(mock_window, "/test")
        assert 'ok' in result
        assert result['ok'] is False
        assert 'error' in result