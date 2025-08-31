"""Test infrastructure for window management functionality.

Tests for the new window management functions:
- create_worker_window
- find_worker_window_by_directory
- list_all_worker_windows
- launch_claude_in_window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import libtmux

from infrastructure import TmuxConnection, TmuxConnectionError


class TestWindowManagement:
    """Test suite for window management functions."""

    @patch('infrastructure.libtmux.Server')
    def test_create_worker_window_creates_window_with_correct_naming(self, mock_server):
        """Test that create_worker_window creates windows with correct naming convention."""
        # Setup mocks
        mock_window = Mock()
        mock_session = Mock()
        mock_session.new_window.return_value = mock_window
        mock_server_instance = Mock()
        mock_server_instance.find_where.return_value = mock_session
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("test_session")
        connection.connect()
        
        # Test directory path to window name conversion
        directory = "/home/user/project"
        result = connection.create_worker_window(directory)
        
        # Verify window name follows claude: prefix with directory conversion
        expected_name = "claude:_home_user_project"
        mock_session.new_window.assert_called_once_with(window_name=expected_name)
        assert result == mock_window

    @patch('infrastructure.libtmux.Server')
    def test_create_worker_window_handles_complex_directory_paths(self, mock_server):
        """Test window naming with complex directory paths."""
        mock_window = Mock()
        mock_session = Mock()
        mock_session.new_window.return_value = mock_window
        mock_server_instance = Mock()
        mock_server_instance.find_where.return_value = mock_session
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("test_session")
        connection.connect()
        
        # Test with complex path
        directory = "/home/user/projects/my-app/src"
        connection.create_worker_window(directory)
        
        expected_name = "claude:_home_user_projects_my-app_src"
        mock_session.new_window.assert_called_once_with(window_name=expected_name)

    def test_create_worker_window_requires_connection(self):
        """Test that create_worker_window raises error if not connected."""
        connection = TmuxConnection("test_session")
        
        with pytest.raises(TmuxConnectionError, match="Not connected to tmux"):
            connection.create_worker_window("/home/user")

    @patch('infrastructure.libtmux.Server')
    def test_find_worker_window_by_directory_finds_existing_window(self, mock_server):
        """Test that find_worker_window_by_directory finds existing windows."""
        mock_window = Mock()
        mock_session = Mock()
        mock_session.find_where.return_value = mock_window
        mock_server_instance = Mock()
        mock_server_instance.find_where.return_value = mock_session
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("test_session")
        connection.connect()
        
        directory = "/home/user/project"
        result = connection.find_worker_window_by_directory(directory)
        
        expected_name = "claude:_home_user_project"
        mock_session.find_where.assert_called_with({"window_name": expected_name})
        assert result == mock_window

    @patch('infrastructure.libtmux.Server')
    def test_find_worker_window_by_directory_returns_none_when_not_found(self, mock_server):
        """Test that find_worker_window_by_directory returns None when window not found."""
        mock_session = Mock()
        mock_session.find_where.return_value = None
        mock_server_instance = Mock()
        mock_server_instance.find_where.return_value = mock_session
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("test_session")
        connection.connect()
        
        result = connection.find_worker_window_by_directory("/nonexistent/path")
        assert result is None

    def test_find_worker_window_by_directory_requires_connection(self):
        """Test that find_worker_window_by_directory raises error if not connected."""
        connection = TmuxConnection("test_session")
        
        with pytest.raises(TmuxConnectionError, match="Not connected to tmux"):
            connection.find_worker_window_by_directory("/home/user")

    @patch('infrastructure.libtmux.Server')
    def test_list_all_worker_windows_filters_correctly(self, mock_server):
        """Test that list_all_worker_windows filters windows with claude: prefix."""
        # Create mock windows - some with claude: prefix, some without
        claude_window1 = Mock()
        claude_window1.name = "claude:_home_user_project1"
        claude_window2 = Mock()
        claude_window2.name = "claude:_home_user_project2"
        regular_window = Mock()
        regular_window.name = "main"
        other_window = Mock()
        other_window.name = "vim"
        
        mock_session = Mock()
        mock_session.windows = [claude_window1, regular_window, claude_window2, other_window]
        mock_server_instance = Mock()
        mock_server_instance.find_where.return_value = mock_session
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("test_session")
        connection.connect()
        
        result = connection.list_all_worker_windows()
        
        # Should only return windows with claude: prefix
        assert len(result) == 2
        assert claude_window1 in result
        assert claude_window2 in result
        assert regular_window not in result
        assert other_window not in result

    @patch('infrastructure.libtmux.Server')
    def test_list_all_worker_windows_returns_empty_when_no_claude_windows(self, mock_server):
        """Test that list_all_worker_windows returns empty list when no claude windows exist."""
        regular_window = Mock()
        regular_window.name = "main"
        other_window = Mock()
        other_window.name = "vim"
        
        mock_session = Mock()
        mock_session.windows = [regular_window, other_window]
        mock_server_instance = Mock()
        mock_server_instance.find_where.return_value = mock_session
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("test_session")
        connection.connect()
        
        result = connection.list_all_worker_windows()
        assert result == []

    def test_list_all_worker_windows_requires_connection(self):
        """Test that list_all_worker_windows raises error if not connected."""
        connection = TmuxConnection("test_session")
        
        with pytest.raises(TmuxConnectionError, match="Not connected to tmux"):
            connection.list_all_worker_windows()

    def test_launch_claude_in_window_sends_correct_commands(self):
        """Test that launch_claude_in_window sends correct commands to pane."""
        # Create mock pane and window
        mock_pane = Mock()
        mock_window = Mock()
        mock_window.panes = [mock_pane]
        mock_window.name = "test_window"
        
        connection = TmuxConnection("test_session")
        directory = "/home/user/project"
        
        connection.launch_claude_in_window(mock_window, directory)
        
        # Verify commands were sent in correct order
        expected_calls = [
            (f"cd {directory}",),
            ("claude",)
        ]
        actual_calls = [call[0] for call in mock_pane.send_keys.call_args_list]
        assert actual_calls == expected_calls

    def test_launch_claude_in_window_handles_no_panes(self):
        """Test that launch_claude_in_window handles windows with no panes."""
        mock_window = Mock()
        mock_window.panes = []
        mock_window.name = "empty_window"
        
        connection = TmuxConnection("test_session")
        
        with pytest.raises(TmuxConnectionError, match="No pane available in window empty_window"):
            connection.launch_claude_in_window(mock_window, "/home/user")

    def test_launch_claude_in_window_handles_pane_errors(self):
        """Test that launch_claude_in_window handles pane operation errors."""
        mock_pane = Mock()
        mock_pane.send_keys.side_effect = Exception("Pane error")
        mock_window = Mock()
        mock_window.panes = [mock_pane]
        
        connection = TmuxConnection("test_session")
        
        with pytest.raises(TmuxConnectionError, match="Failed to launch Claude in window"):
            connection.launch_claude_in_window(mock_window, "/home/user")