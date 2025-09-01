"""Test domain layer - Business rules and domain services.

Tests for all business logic and domain knowledge functions.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock

import domain


class TestClaudeBusinessRules:
    """Test Claude-specific business rules."""
    
    def test_generate_claude_window_name_simple_path(self):
        """Test window name generation for simple path."""
        result = domain.generate_claude_window_name("/home/user/project")
        assert result == "claude:_home_user_project"
    
    def test_generate_claude_window_name_complex_path(self):
        """Test window name generation for complex path."""
        result = domain.generate_claude_window_name("/home/user/my-project/src")
        assert result == "claude:_home_user_my-project_src"
    
    def test_generate_claude_history_patterns(self):
        """Test history pattern generation returns multiple patterns."""
        patterns = domain.generate_claude_history_patterns("/home/user/project")
        
        assert len(patterns) == 3
        assert "home-user-project" in patterns
        assert "-home-user-project" in patterns
        assert "-home-user-project" in patterns or "/home-user-project" in patterns
    
    def test_get_claude_default_command(self):
        """Test getting Claude default command."""
        result = domain.get_claude_default_command()
        
        assert result == "claude"
    
    
    def test_get_claude_history_base_path(self):
        """Test Claude history base path generation."""
        path = domain.get_claude_history_base_path()
        assert str(path).endswith(".claude/projects")
        assert isinstance(path, Path)


class TestGenericWorkerRules:
    """Test generic worker business rules."""
    
    def test_extract_directory_from_window_name_claude(self):
        """Test extracting directory from Claude window name."""
        result = domain.extract_directory_from_window_name("claude:_home_user_project")
        assert result == "/home/user/project"
    
    def test_extract_directory_from_window_name_no_prefix(self):
        """Test extracting directory from window without prefix."""
        result = domain.extract_directory_from_window_name("random_window")
        assert result == ""
    
    def test_extract_directory_with_custom_prefix(self):
        """Test extracting directory with custom tool prefix."""
        result = domain.extract_directory_from_window_name(
            "codex:_var_lib_app", 
            tool_prefix="codex:"
        )
        assert result == "/var/lib/app"
    
    def test_is_worker_window_claude(self):
        """Test identifying Claude worker window."""
        assert domain.is_worker_window("claude:_home_user") is True
        assert domain.is_worker_window("vim") is False
        assert domain.is_worker_window("main") is False
    
    def test_is_worker_window_custom_prefix(self):
        """Test identifying worker window with custom prefix."""
        assert domain.is_worker_window("gemini:_test", tool_prefix="gemini:") is True
        assert domain.is_worker_window("claude:_test", tool_prefix="gemini:") is False
    


class TestWorkerStateRules:
    """Test worker state business rules."""
    
    def test_determine_worker_status_alive(self):
        """Test determining alive worker status."""
        status = domain.determine_worker_status(True, "%123", is_pane_alive=True)
        assert status == "alive"
    
    def test_determine_worker_status_dead_pane(self):
        """Test determining dead worker status when pane is dead."""
        status = domain.determine_worker_status(True, "%123", is_pane_alive=False)
        assert status == "dead"
    
    def test_determine_worker_status_no_pane(self):
        """Test determining dead worker status when no pane."""
        status = domain.determine_worker_status(False, None)
        assert status == "dead"
        
        status = domain.determine_worker_status(True, None)
        assert status == "dead"


class TestHistoryManagementRules:
    """Test history management business rules."""
    
    def test_find_history_directory_found(self, tmp_path):
        """Test finding history directory when it exists."""
        # Create test directory structure
        base = tmp_path / "projects"
        base.mkdir()
        history_dir = base / "test-pattern"
        history_dir.mkdir()
        
        result = domain.find_history_directory(
            "/test/dir",
            ["test-pattern", "other-pattern"],
            base
        )
        
        assert result == history_dir
    
    def test_find_history_directory_not_found(self, tmp_path):
        """Test finding history directory when none exist."""
        base = tmp_path / "projects"
        base.mkdir()
        
        result = domain.find_history_directory(
            "/test/dir",
            ["missing-pattern"],
            base
        )
        
        assert result is None
    
    def test_find_history_directory_base_missing(self, tmp_path):
        """Test finding history when base path doesn't exist."""
        base = tmp_path / "nonexistent"
        
        result = domain.find_history_directory(
            "/test/dir",
            ["pattern"],
            base
        )
        
        assert result is None
    
    def test_validate_history_content_with_files(self, tmp_path):
        """Test validating history with jsonl files."""
        history_path = tmp_path / "history"
        history_path.mkdir()
        
        # Create test jsonl files
        (history_path / "session1.jsonl").touch()
        (history_path / "session2.jsonl").touch()
        
        result = domain.validate_history_content(history_path)
        
        assert result["has_history"] is True
        assert result["file_count"] == 2
        assert result["latest_file"] == "session2.jsonl"
    
    def test_validate_history_content_empty(self, tmp_path):
        """Test validating empty history directory."""
        history_path = tmp_path / "history"
        history_path.mkdir()
        
        result = domain.validate_history_content(history_path)
        
        assert result["has_history"] is False
        assert result["file_count"] == 0
        assert result["latest_file"] is None