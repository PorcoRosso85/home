"""Test domain.py purity - ensure only business rules remain.

This test verifies that technical implementation details have been removed
from domain.py, keeping only pure business rules.
"""

import unittest
import domain


class TestDomainPurity(unittest.TestCase):
    """Test that domain.py contains only business rules, no technical details."""
    
    def test_technical_implementation_functions_removed(self):
        """Test that technical implementation details have been completely removed."""
        # These functions should NOT exist in pure domain layer
        with self.assertRaises(AttributeError):
            domain.get_claude_launch_command()
            
        with self.assertRaises(AttributeError):
            domain.get_claude_default_command()
    
    def test_business_rule_functions_preserved(self):
        """Test that pure business rule functions are preserved."""
        # These are pure business rules and should remain
        self.assertTrue(hasattr(domain, 'generate_claude_window_name'))
        self.assertTrue(hasattr(domain, 'generate_claude_history_patterns'))
        self.assertTrue(hasattr(domain, 'get_claude_history_base_path'))
        self.assertTrue(hasattr(domain, 'extract_directory_from_window_name'))
        self.assertTrue(hasattr(domain, 'is_worker_window'))
        self.assertTrue(hasattr(domain, 'should_check_pane_alive'))
        self.assertTrue(hasattr(domain, 'determine_worker_status'))
        self.assertTrue(hasattr(domain, 'find_history_directory'))
        self.assertTrue(hasattr(domain, 'validate_history_content'))
    
    def test_no_variables_module_dependency(self):
        """Test that domain.py has no dependency on variables module."""
        # Domain layer should not import or depend on technical modules
        import inspect
        source = inspect.getsource(domain)
        
        # Should not import variables module
        self.assertNotIn('import variables', source)
        self.assertNotIn('from variables', source)
        
        # Should not have fallback/try-except for technical concerns
        self.assertNotIn('ImportError', source)
    
    def test_pure_business_rules_work_correctly(self):
        """Test that remaining business rules function correctly."""
        # Test window name generation (pure business rule)
        window_name = domain.generate_claude_window_name('/home/user/project')
        self.assertEqual(window_name, 'developer:_home_user_project')
        
        # Test history patterns generation (pure business rule)
        patterns = domain.generate_claude_history_patterns('/home/user/project')
        expected_patterns = [
            'home-user-project',
            '-home-user-project', 
            '-home-user-project'
        ]
        self.assertEqual(patterns, expected_patterns)
        
        # Test history base path (pure business rule)
        from pathlib import Path
        base_path = domain.get_claude_history_base_path()
        self.assertEqual(base_path, Path.home() / ".claude/projects")


if __name__ == '__main__':
    unittest.main()