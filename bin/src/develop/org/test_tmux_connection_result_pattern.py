#!/usr/bin/env python3
"""Test module for TmuxConnection Result pattern compliance.

This test ensures that TmuxConnection class methods return Result objects
instead of throwing exceptions, in compliance with error_handling.md.
"""
import pytest
from unittest.mock import Mock, patch
from infrastructure import TmuxConnection


class TestTmuxConnectionResultPattern:
    """Test TmuxConnection Result pattern compliance."""
    
    def test_init_should_return_error_result_not_raise_exception(self):
        """Test that __init__ returns error result instead of raising ValueError."""
        # Mock create_tmux_connection to return failure
        with patch('infrastructure.create_tmux_connection') as mock_create:
            mock_create.return_value = {
                "ok": False,
                "error": {"message": "Session not found"}
            }
            
            # This should not raise an exception - instead __init__ should handle it
            # and provide a way to check if initialization failed
            conn = TmuxConnection("nonexistent")
            # Verify the connection is in error state  
            assert not conn.is_valid()
            assert conn.get_init_error() is not None
    
    def test_connect_should_return_error_result_not_raise_exception(self):
        """Test that connect returns error result instead of raising TmuxConnectionError."""
        with patch('infrastructure.create_tmux_connection') as mock_create:
            mock_create.return_value = {"ok": True, "data": {"session_name": "test"}}
            
            with patch('infrastructure.connect_to_tmux_server') as mock_connect:
                mock_connect.return_value = {
                    "ok": False,
                    "error": {"message": "Connect failed"}
                }
                
                conn = TmuxConnection("test")
                
                # This should return Result object, not raise exception
                result = conn.connect()
                
                # Verify it's a proper Result object
                assert isinstance(result, dict)
                assert "ok" in result
                assert result["ok"] is False
                assert "error" in result
    
    def test_send_command_should_return_error_result_not_raise_exception(self):
        """Test that send_command returns error result instead of raising TmuxConnectionError."""
        with patch('infrastructure.create_tmux_connection') as mock_create:
            mock_create.return_value = {"ok": True, "data": {"session_name": "test"}}
            
            with patch('infrastructure.send_command_to_pane') as mock_send:
                mock_send.return_value = {
                    "ok": False,
                    "error": {"message": "Send failed"}
                }
                
                conn = TmuxConnection("test")
                
                # This should return Result object, not raise exception
                result = conn.send_command("test_command", "invalid_window", "invalid_pane")
                
                # Verify it's a proper Result object
                assert isinstance(result, dict)
                assert "ok" in result
                assert result["ok"] is False
                assert "error" in result
    
    def test_get_or_create_session_should_return_error_result_not_raise_exception(self):
        """Test that get_or_create_session returns error result instead of raising TmuxConnectionError."""
        with patch('infrastructure.create_tmux_connection') as mock_create:
            mock_create.return_value = {"ok": True, "data": {"session_name": "test"}}
            
            with patch('infrastructure.get_or_create_tmux_session') as mock_session:
                mock_session.return_value = {
                    "ok": False,
                    "error": {"message": "Session failed"}
                }
                
                conn = TmuxConnection("test")
                
                # This should return Result object, not raise exception
                result = conn.get_or_create_session()
                
                # Verify it's a proper Result object
                assert isinstance(result, dict)
                assert "ok" in result
                assert result["ok"] is False
                assert "error" in result

    def test_create_worker_window_should_return_error_result_not_raise_exception(self):
        """Test that create_worker_window returns error result instead of raising TmuxConnectionError."""
        with patch('infrastructure.create_tmux_connection') as mock_create:
            mock_create.return_value = {"ok": True, "data": {"session_name": "test"}}
            
            with patch('infrastructure.create_worker_window_for_directory') as mock_window:
                mock_window.return_value = {
                    "ok": False,
                    "error": {"message": "Create window failed"}
                }
                
                conn = TmuxConnection("test")
                
                # This should return Result object, not raise exception
                result = conn.create_worker_window("/invalid/path")
                
                # Verify it's a proper Result object
                assert isinstance(result, dict)
                assert "ok" in result
                assert result["ok"] is False
                assert "error" in result

    def test_list_all_worker_windows_should_return_error_result_not_raise_exception(self):
        """Test that list_all_worker_windows returns error result instead of raising TmuxConnectionError."""
        with patch('infrastructure.create_tmux_connection') as mock_create:
            mock_create.return_value = {"ok": True, "data": {"session_name": "test"}}
            
            with patch('infrastructure.list_all_worker_windows') as mock_list:
                mock_list.return_value = {
                    "ok": False,
                    "error": {"message": "List windows failed"}
                }
                
                conn = TmuxConnection("test")
                
                # This should return Result object, not raise exception
                result = conn.list_all_worker_windows()
                
                # Verify it's a proper Result object
                assert isinstance(result, dict)
                assert "ok" in result
                assert result["ok"] is False
                assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])