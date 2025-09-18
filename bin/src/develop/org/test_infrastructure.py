"""Test infrastructure for org project - tmux connection functionality.

Following TDD principles: these tests are written first to describe desired behavior.
They should fail initially and guide implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import libtmux

from infrastructure import TmuxConnection, TmuxConnectionError


class TestTmuxConnection:
    """Test suite for TmuxConnection class."""

    def test_tmux_connection_initializes_with_session_name(self):
        """Test that TmuxConnection can be initialized with a session name."""
        # This test should fail initially - TmuxConnection doesn't exist yet
        session_name = "test_session"
        connection = TmuxConnection(session_name)
        assert connection.session_name == session_name

    def test_tmux_connection_handles_invalid_session_name(self):
        """Test that TmuxConnection handles invalid session name without raising."""
        # Should not raise exception, but should be in error state
        conn_none = TmuxConnection(None)
        assert not conn_none.is_valid()
        assert conn_none.get_init_error() is not None
        
        conn_empty = TmuxConnection("")
        assert not conn_empty.is_valid() 
        assert conn_empty.get_init_error() is not None

    @patch('infrastructure.libtmux.Server')
    def test_connect_creates_tmux_server_instance(self, mock_server):
        """Test that connect() creates a libtmux Server instance."""
        mock_server_instance = Mock()
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("test_session")
        result = connection.connect()
        
        mock_server.assert_called_once()
        assert result is True

    @patch('infrastructure.libtmux.Server')
    def test_connect_handles_tmux_unavailable(self, mock_server):
        """Test that connect() handles cases where tmux is not available."""
        mock_server.side_effect = Exception("tmux not found")
        
        connection = TmuxConnection("test_session")
        
        with pytest.raises(TmuxConnectionError, match="Failed to connect to tmux"):
            connection.connect()

    @patch('infrastructure.libtmux.Server')
    def test_get_or_create_session_returns_existing_session(self, mock_server):
        """Test that get_or_create_session returns existing session if found."""
        mock_session = Mock()
        mock_server_instance = Mock()
        mock_server_instance.find_where.return_value = mock_session
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("existing_session")
        connection.connect()
        
        session = connection.get_or_create_session()
        
        mock_server_instance.find_where.assert_called_once_with({"session_name": "existing_session"})
        assert session == mock_session

    @patch('infrastructure.libtmux.Server')
    def test_get_or_create_session_creates_new_session_if_not_found(self, mock_server):
        """Test that get_or_create_session creates new session if not found."""
        mock_session = Mock()
        mock_server_instance = Mock()
        mock_server_instance.find_where.return_value = None
        mock_server_instance.new_session.return_value = mock_session
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("new_session")
        connection.connect()
        
        session = connection.get_or_create_session()
        
        mock_server_instance.find_where.assert_called_once_with({"session_name": "new_session"})
        mock_server_instance.new_session.assert_called_once_with("new_session")
        assert session == mock_session

    def test_send_command_requires_connection(self):
        """Test that send_command raises error if not connected."""
        connection = TmuxConnection("test_session")
        
        with pytest.raises(TmuxConnectionError, match="Not connected to tmux"):
            connection.send_command("echo hello", "window_name", "pane_name")

    @patch('infrastructure.libtmux.Server')
    def test_send_command_sends_to_specified_pane(self, mock_server):
        """Test that send_command sends command to specified window and pane."""
        mock_pane = Mock()
        mock_window = Mock()
        mock_window.find_where.return_value = mock_pane
        mock_session = Mock()
        mock_session.find_where.return_value = mock_window
        
        mock_server_instance = Mock()
        mock_server_instance.find_where.return_value = mock_session
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("test_session")
        connection.connect()
        
        connection.send_command("echo hello", "window1", "pane1")
        
        mock_session.find_where.assert_called_once_with({"window_name": "window1"})
        mock_window.find_where.assert_called_once_with({"pane_name": "pane1"})
        mock_pane.send_keys.assert_called_once_with("echo hello")

    def test_is_connected_returns_false_initially(self):
        """Test that is_connected returns False before connection."""
        connection = TmuxConnection("test_session")
        assert connection.is_connected() is False

    @patch('infrastructure.libtmux.Server')
    def test_is_connected_returns_true_after_successful_connection(self, mock_server):
        """Test that is_connected returns True after successful connection."""
        mock_server_instance = Mock()
        mock_server.return_value = mock_server_instance
        
        connection = TmuxConnection("test_session")
        connection.connect()
        
        assert connection.is_connected() is True


class TestTmuxConnectionError:
    """Test suite for TmuxConnectionError exception."""

    def test_tmux_connection_error_is_exception(self):
        """Test that TmuxConnectionError is a proper exception."""
        error = TmuxConnectionError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"