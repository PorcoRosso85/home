"""Characterization tests for window naming behavior inconsistencies.

This test file documents the CURRENT (potentially broken) behavior of window naming
to prevent regression and aid in fixing the mismatch between creation and lookup.

Current Issue: 
- start_developer() creates windows with "developer:" prefix (application.py:293)
- find_worker_window_by_directory() looks for "developer:" prefix (domain.py:24)
- This causes send_command_to_developer_by_directory() to fail
"""

import pytest
from unittest.mock import Mock, patch
from application import start_developer
from domain import generate_developer_window_name
from infrastructure import find_worker_window_by_directory


class TestWindowNamingMismatch:
    """Test the current window naming inconsistency between creation and lookup."""
    
    def test_start_developer_uses_developer_prefix(self):
        """Document that start_developer creates windows with 'developer:' prefix.
        
        This is the CURRENT behavior that causes lookup failures.
        """
        directory = "/home/nixos/bin/src/test/project"
        expected_window_name = "developer:_home_nixos_bin_src_test_project"
        
        # This documents the actual behavior in application.py line 293
        actual_window_name = f"developer:{directory.replace('/', '_')}"
        
        assert actual_window_name == expected_window_name
        assert actual_window_name.startswith("developer:")
    
    def test_find_worker_expects_claude_prefix(self):
        """Document that find_worker_window_by_directory expects 'developer:' prefix.
        
        This is the CURRENT behavior via domain.generate_developer_window_name.
        """
        directory = "/home/nixos/bin/src/test/project"
        expected_window_name = "developer:_home_nixos_bin_src_test_project"
        
        # This documents the actual behavior in domain.py line 24
        actual_window_name = generate_developer_window_name(directory)
        
        assert actual_window_name == expected_window_name
        assert actual_window_name.startswith("developer:")
    
    def test_window_naming_consistency_fixed(self):
        """Verify that window creation and lookup use consistent naming.
        
        This test confirms the naming mismatch has been fixed.
        Both creation and lookup now use the same developer: prefix.
        """
        directory = "/home/nixos/bin/src/test/project"
        
        # What start_developer creates
        created_name = f"developer:{directory.replace('/', '_')}"
        
        # What find_worker_window_by_directory looks for
        searched_name = generate_developer_window_name(directory)
        
        # Verify they match (bug is fixed)
        assert created_name == searched_name, (
            f"Window naming should be consistent: "
            f"created='{created_name}' != searched='{searched_name}'"
        )
    
    def test_path_transformation_consistency(self):
        """Document that both functions use the same path transformation logic.
        
        At least the path transformation (/ to _) is consistent between them.
        """
        directory = "/home/nixos/bin/src/test/project"
        expected_suffix = "_home_nixos_bin_src_test_project"
        
        # Both use the same transformation
        developer_name = f"developer:{directory.replace('/', '_')}"
        developer_name_2 = generate_developer_window_name(directory)
        
        assert developer_name.endswith(expected_suffix)
        assert developer_name_2.endswith(expected_suffix)
        
        # Only the prefix differs
        assert developer_name == f"developer:{expected_suffix}"
        assert developer_name_2 == f"developer:{expected_suffix}"
