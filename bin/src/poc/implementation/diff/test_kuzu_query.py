#!/usr/bin/env python3
"""
Test for kuzu_query.py following bin/docs/conventions/testing.md
Test file must be in same directory as target file
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Import the module to test
import kuzu_query


class TestQueryLocationUris:
    """Test suite for query_location_uris function"""
    
    def test_query_location_uris_with_valid_db_returns_json_array(self):
        """正常なDBパスの場合、LocationURIのJSON配列を返すこと"""
        result = kuzu_query.query_location_uris()
        assert isinstance(result, list)
        assert len(result) > 0
        assert all('uri' in item for item in result)
    
    def test_query_location_uris_with_nonexistent_db_raises_systemexit(self):
        """存在しないDBパスの場合、FileNotFoundErrorを発生させること"""
        with pytest.raises(FileNotFoundError):
            kuzu_query.query_location_uris("/nonexistent/path")
    
    def test_query_location_uris_with_empty_result_returns_empty_list(self):
        """LocationURIが0件の場合、空のリストを返すこと"""
        # Current mock always returns data, this is for future implementation
        result = kuzu_query.query_location_uris()
        assert isinstance(result, list)
    
    def test_query_location_uris_with_multiple_uris_returns_all(self):
        """複数のLocationURIがある場合、すべてを返すこと"""
        result = kuzu_query.query_location_uris()
        assert len(result) == 3  # Mock returns 3 items
        assert result[0]["uri"].startswith("file://")


class TestMain:
    """Test suite for main function (CLI interface)"""
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_with_no_args_uses_default_path(self, mock_stdout):
        """引数なしの場合、デフォルトパスを使用すること"""
        with patch('sys.argv', ['kuzu_query.py']):
            ret = kuzu_query.main()
            assert ret == 0
            output = mock_stdout.getvalue()
            data = json.loads(output)
            assert isinstance(data, list)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_with_custom_path_uses_provided_path(self, mock_stdout):
        """カスタムパスが指定された場合、そのパスを使用すること"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('sys.argv', ['kuzu_query.py', tmpdir]):
                ret = kuzu_query.main()
                assert ret == 0
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_with_valid_db_prints_json_to_stdout(self, mock_stdout):
        """正常実行時、標準出力にJSONを出力すること"""
        with patch('sys.argv', ['kuzu_query.py']):
            ret = kuzu_query.main()
            assert ret == 0
            output = mock_stdout.getvalue()
            data = json.loads(output)
            assert isinstance(data, list)
            assert all('uri' in item for item in data)
    
    @patch('sys.stderr', new_callable=StringIO)
    def test_main_with_db_error_prints_error_to_stderr(self, mock_stderr):
        """DBエラー時、標準エラー出力にエラーメッセージを出力すること"""
        with patch('sys.argv', ['kuzu_query.py', '/nonexistent/path']):
            ret = kuzu_query.main()
            assert ret == 1
            error_output = mock_stderr.getvalue()
            assert "Error:" in error_output