"""Test filtering external diagnostics and files."""

import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from graph_docs.pyright_analyzer import PyrightAnalyzer


class TestFilterExternal(unittest.TestCase):
    """Test the filter_external parameter functionality."""
    
    def setUp(self):
        """Set up test workspace."""
        self.workspace_path = "/home/user/project"
        self.analyzer = PyrightAnalyzer(self.workspace_path)
    
    def test_filter_external_default_false(self):
        """Test that filter_external defaults to False."""
        # Mock subprocess.run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "generalDiagnostics": [],
            "summary": {}
        })
        
        with patch("subprocess.run", return_value=mock_result):
            # Call analyze without filter_external parameter
            result = self.analyzer.analyze()
            
        self.assertTrue(result["ok"])
    
    def test_filter_internal_diagnostics(self):
        """Test that diagnostics are filtered correctly."""
        diagnostics = [
            {"file": "/home/user/project/main.py", "severity": "error"},
            {"file": "/home/user/project/sub/module.py", "severity": "warning"},
            {"file": "/usr/lib/python3/site-packages/numpy/__init__.py", "severity": "error"},
            {"file": "/home/other/project/file.py", "severity": "error"},
            {"severity": "error"},  # No file path
        ]
        
        filtered = self.analyzer._filter_internal_diagnostics(diagnostics)
        
        # Should include files within workspace and diagnostics without file paths
        self.assertEqual(len(filtered), 3)
        
        # Check that external files are filtered out
        file_paths = [d.get("file", "") for d in filtered if d.get("file")]
        for path in file_paths:
            self.assertTrue(path.startswith("/home/user/project"))
    
    def test_analyze_with_filter(self):
        """Test full analyze with filtering enabled."""
        # Mock subprocess.run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "generalDiagnostics": [
                {"file": "/home/user/project/app.py", "severity": "error"},
                {"file": "/usr/lib/python3/typing.py", "severity": "warning"},
                {"file": "/home/user/project/tests/test_app.py", "severity": "information"},
            ],
            "summary": {"errorCount": 1, "warningCount": 1}
        })
        
        with patch("subprocess.run", return_value=mock_result):
            # Without filtering
            result_all = self.analyzer.analyze(filter_external=False)
            
            # With filtering
            result_filtered = self.analyzer.analyze(filter_external=True)
        
        # Check that filtering reduces the number of diagnostics
        self.assertEqual(len(result_all["diagnostics"]), 3)
        self.assertEqual(len(result_filtered["diagnostics"]), 2)
        
        # Check that filtering reduces the number of files
        self.assertEqual(len(result_all["files"]), 3)
        self.assertEqual(len(result_filtered["files"]), 2)
    
    def test_extract_files_info_with_filter(self):
        """Test _extract_files_info with filtering enabled."""
        output = {
            "generalDiagnostics": [
                {"file": "/home/user/project/main.py", "severity": "error"},
                {"file": "/home/user/project/main.py", "severity": "warning"},
                {"file": "/usr/lib/python3/os.py", "severity": "error"},
                {"file": "/home/user/project/utils.py", "severity": "information"},
            ]
        }
        
        # Without filtering
        files_all = self.analyzer._extract_files_info(output, filter_external=False)
        
        # With filtering  
        files_filtered = self.analyzer._extract_files_info(output, filter_external=True)
        
        # Should have 3 files without filtering, 2 with filtering
        self.assertEqual(len(files_all), 3)
        self.assertEqual(len(files_filtered), 2)
        
        # Check that external file is not in filtered results
        filtered_paths = [f["path"] for f in files_filtered]
        self.assertNotIn("/usr/lib/python3/os.py", filtered_paths)
        self.assertIn("/home/user/project/main.py", filtered_paths)
        self.assertIn("/home/user/project/utils.py", filtered_paths)


if __name__ == "__main__":
    unittest.main()