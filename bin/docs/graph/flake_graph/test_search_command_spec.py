"""Specification tests for flake search command functionality.

This module tests the BEHAVIOR and BUSINESS VALUE of the search command.
It verifies that the system meets the business requirement:
"Developers can quickly find relevant flakes using natural language queries"

Business Context:
- Current: Developers manually browse directories to find relevant flakes
- Target: Natural language search across flake descriptions and paths
- Impact: Faster discovery of reusable flakes, improved developer productivity

Technical Requirements:
- Search should work across both path names and descriptions
- Case-insensitive matching for user convenience
- Partial matching to handle typos and incomplete queries
- Ranked results by relevance (VSS similarity when available)
"""

import pytest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock
import argparse

# Import the CLI module to test search command
from flake_graph.cli import main


class TestSearchCommandBehavior:
    """Test search command behavior and business value."""
    
    def test_search_finds_flakes_by_description_keywords(self):
        """キーワードによる説明文検索でフレークが発見できる
        
        ビジネス価値:
        - 開発者が目的に応じてフレークを素早く発見
        - "python web server"のような自然言語クエリが可能
        - 既存のソリューションの再利用促進
        """
        # RED: This test will fail because search command doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'search', 'python web server', '--path', '/test/flakes']):
            with patch('sys.stdout.write') as mock_stdout:
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('pathlib.Path.rglob') as mock_rglob:
                        # Mock flake discovery
                        mock_flake_paths = [
                            Mock(parent=Path('/test/flakes/web/django')),
                            Mock(parent=Path('/test/flakes/api/fastapi')),
                            Mock(parent=Path('/test/flakes/data/postgres')),
                        ]
                        mock_rglob.return_value = mock_flake_paths
                        
                        # Mock flake descriptions
                        with patch('flake_graph.scanner.scan_flake_description') as mock_scan:
                            mock_scan.side_effect = [
                                "Python Django web application framework",
                                "FastAPI Python web server for APIs", 
                                "PostgreSQL database for data persistence"
                            ]
                            
                            with patch('flake_graph.scanner.scan_readme_content', return_value=""):
                                # Now the search command exists and should work
                                result = main()
                                
                                # Expected: search should succeed and show Django and FastAPI
                                # (not PostgreSQL because it doesn't match "python web server")
                                assert result == 0, "Search command should succeed"
                                
                                # Verify search results were written to stdout
                                stdout_calls = [str(call) for call in mock_stdout.call_args_list]
                                stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                                
                                # Should find Django (matches "Python Django web application")
                                # Should find FastAPI (matches "FastAPI Python web server")
                                # Should NOT find PostgreSQL (doesn't match "python web server")
                                assert "django" in stdout_output.lower()
                                assert "fastapi" in stdout_output.lower()
                                # PostgreSQL should not appear as it doesn't match "python"
                                assert "postgres" not in stdout_output.lower()
    
    def test_search_handles_case_insensitive_queries(self):
        """大文字小文字を区別しない検索が動作する
        
        ビジネス価値:
        - ユーザビリティの向上（入力の柔軟性）
        - タイポや大文字小文字の違いによる検索失敗を防止
        - より直感的な検索体験
        """
        # RED: This test will fail because search command doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'search', 'PYTHON', '--path', '/test/flakes']):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.rglob') as mock_rglob:
                    mock_flake_paths = [Mock(parent=Path('/test/flakes/python/django'))]
                    mock_rglob.return_value = mock_flake_paths
                    
                    with patch('flake_graph.scanner.scan_flake_description') as mock_scan:
                        mock_scan.return_value = "python web framework"
                        
                        with patch('flake_graph.scanner.scan_readme_content', return_value=""):
                            with patch('sys.stdout.write') as mock_stdout:
                                result = main()
                                
                                # Expected: Should find 'python' even when searching for 'PYTHON'
                                assert result == 0, "Case-insensitive search should work"
                                
                                # Verify case-insensitive matching worked
                                stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                                assert "django" in stdout_output.lower()
    
    def test_search_finds_flakes_by_path_patterns(self):
        """パスパターンによるフレーク検索が動作する
        
        ビジネス価値:
        - ディレクトリ構造に基づく論理的な検索
        - プロジェクト構造の理解を活用した検索
        - 関連するフレークのグループ発見
        """
        # RED: This test will fail because search command doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'search', 'web/frontend', '--path', '/test/flakes']):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.rglob') as mock_rglob:
                    mock_flake_paths = [
                        Mock(parent=Path('/test/flakes/web/frontend/react')),
                        Mock(parent=Path('/test/flakes/web/frontend/vue')),
                        Mock(parent=Path('/test/flakes/web/backend/django')),
                    ]
                    mock_rglob.return_value = mock_flake_paths
                    
                    with patch('flake_graph.scanner.scan_flake_description') as mock_scan:
                        mock_scan.side_effect = [
                            "React frontend application",
                            "Vue.js frontend framework",
                            "Django backend API"
                        ]
                        
                        with patch('flake_graph.scanner.scan_readme_content', return_value=""):
                            with patch('sys.stdout.write') as mock_stdout:
                                result = main()
                                
                                # Expected: Should find React and Vue (paths contain 'web/frontend')
                                assert result == 0, "Path pattern search should work"
                                
                                # Verify path matching worked
                                stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                                assert "react" in stdout_output.lower()
                                assert "vue" in stdout_output.lower()
                                # Backend should not match 'web/frontend' pattern
                                assert "django" not in stdout_output.lower()
    
    def test_search_handles_partial_matching(self):
        """部分一致検索が動作する
        
        ビジネス価値:
        - 不完全なクエリでも関連するフレークを発見
        - より柔軟で使いやすい検索体験
        - 探索的な検索をサポート
        """
        # RED: This test will fail because search command doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'search', 'postgre', '--path', '/test/flakes']):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.rglob') as mock_rglob:
                    mock_flake_paths = [
                        Mock(parent=Path('/test/flakes/db/postgres')),
                        Mock(parent=Path('/test/flakes/db/mysql')),
                    ]
                    mock_rglob.return_value = mock_flake_paths
                    
                    with patch('flake_graph.scanner.scan_flake_description') as mock_scan:
                        mock_scan.side_effect = [
                            "PostgreSQL database server",
                            "MySQL relational database"
                        ]
                        
                        with patch('flake_graph.scanner.scan_readme_content', return_value=""):
                            with patch('sys.stdout.write') as mock_stdout:
                                result = main()
                                
                                # Expected: Should find PostgreSQL when searching for 'postgre'
                                assert result == 0, "Partial matching search should work"
                                
                                # Verify partial matching worked  
                                stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                                assert "postgres" in stdout_output.lower()
                                # MySQL should not match 'postgre'
                                assert "mysql" not in stdout_output.lower()
    
    def test_search_returns_no_results_gracefully(self):
        """該当なしの場合の適切な応答
        
        ビジネス価値:
        - ユーザーに明確なフィードバック
        - 検索語の修正提案の基盤
        - 混乱のない検索体験
        """
        # RED: This test will fail because search command doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'search', 'nonexistent_technology', '--path', '/test/flakes']):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.rglob', return_value=[]):
                    with patch('sys.stdout.write') as mock_stdout:
                        result = main()
                        
                        # Expected: Should return 0 (success) with "No flakes found" message  
                        assert result == 0, "Search should handle no results gracefully"
                        
                        # Verify "no results" message
                        stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                        assert "no flakes found" in stdout_output.lower()
    
    def test_search_with_vss_enabled_ranks_by_similarity(self):
        """VSS有効時の類似度によるランキング
        
        ビジネス価値:
        - より関連性の高い結果を上位に表示
        - セマンティック検索による高品質な結果
        - 大規模なフレークコレクションでの効率的な検索
        """
        # RED: This test will fail because search command doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'search', 'machine learning', '--path', '/test/flakes', '--use-vss']):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.rglob') as mock_rglob:
                    mock_flake_paths = [
                        Mock(parent=Path('/test/flakes/ai/tensorflow')),
                        Mock(parent=Path('/test/flakes/ai/pytorch')),
                        Mock(parent=Path('/test/flakes/web/django')),
                    ]
                    mock_rglob.return_value = mock_flake_paths
                    
                    with patch('flake_graph.scanner.scan_flake_description') as mock_scan:
                        mock_scan.side_effect = [
                            "TensorFlow machine learning framework",
                            "PyTorch deep learning library", 
                            "Django web application framework"
                        ]
                        
                        with patch('flake_graph.scanner.scan_readme_content', return_value=""):
                            # Mock VSS search to return similarity scores
                            with patch('flake_graph.vss_adapter.search_similar_flakes') as mock_vss:
                                mock_vss.return_value = {
                                    "results": [
                                        {"id": "ai/tensorflow", "score": 0.95, "content": "TensorFlow..."},
                                        {"id": "ai/pytorch", "score": 0.92, "content": "PyTorch..."},
                                        {"id": "web/django", "score": 0.25, "content": "Django..."}
                                    ]
                                }
                                
                                with patch('sys.stdout.write') as mock_stdout:
                                    result = main()
                                    
                                    # Expected: TensorFlow and PyTorch should rank higher than Django
                                    assert result == 0, "VSS search should work"
                                    
                                    # Verify VSS was called and results include similarity scores
                                    mock_vss.assert_called_once()
                                    stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                                    assert "tensorflow" in stdout_output.lower()
                                    assert "pytorch" in stdout_output.lower()
    
    def test_search_with_json_output_format(self):
        """JSON形式での検索結果出力
        
        ビジネス価値:
        - 他ツールとの連携可能性
        - 自動化されたワークフローでの利用
        - プログラマティックな検索結果処理
        """
        # RED: This test will fail because search command doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'search', 'python', '--path', '/test/flakes', '--json']):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.rglob') as mock_rglob:
                    mock_flake_paths = [Mock(parent=Path('/test/flakes/python/django'))]
                    mock_rglob.return_value = mock_flake_paths
                    
                    with patch('flake_graph.scanner.scan_flake_description') as mock_scan:
                        mock_scan.return_value = "Python Django web framework"
                        
                        with patch('flake_graph.scanner.scan_readme_content', return_value=""):
                            with patch('sys.stdout.write') as mock_stdout:
                                result = main()
                                
                                # Expected: Should output JSON formatted results
                                assert result == 0, "JSON output search should work"
                                
                                # Verify JSON output
                                stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                                
                                # Should be valid JSON containing our results
                                import json
                                try:
                                    json_data = json.loads(stdout_output)
                                    assert isinstance(json_data, list), "Should output JSON array"
                                    if json_data:  # If there are results
                                        assert "path" in json_data[0], "Should have path field"
                                except json.JSONDecodeError:
                                    assert False, f"Output should be valid JSON, got: {stdout_output}"


class TestSearchCommandIntegration:
    """Integration tests for search command with actual CLI parsing."""
    
    def test_search_command_argument_parsing(self):
        """検索コマンドの引数解析
        
        ビジネス価値:
        - 直感的なコマンドライン操作
        - 標準的なCLIツールとしての使いやすさ
        - 開発者の学習コストを最小化
        """
        # Now the search subparser exists and should show help
        with patch('sys.argv', ['flake-graph', 'search', '--help']):
            with patch('sys.stdout.write') as mock_stdout:
                with patch('sys.stderr.write'):
                    # This should show help for search command
                    try:
                        result = main()
                        # argparse calls sys.exit(0) for --help
                        assert False, "main() should raise SystemExit for --help"
                    except SystemExit as e:
                        # argparse calls sys.exit(0) when showing help
                        assert e.code == 0, "Help should exit with code 0"
                        
                        # Verify help was shown
                        stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                        assert "search" in stdout_output.lower()
    
    def test_search_command_requires_query_argument(self):
        """検索にはクエリ引数が必須
        
        ビジネス価値:
        - 明確なエラーメッセージによる使いやすさ
        - 不正な使用方法の早期検出
        - コマンドライン操作の一貫性
        """
        # Search command exists but requires query argument
        with patch('sys.argv', ['flake-graph', 'search']):  # Missing query
            with patch('sys.stderr.write') as mock_stderr:
                try:
                    result = main()
                    assert False, "Should have failed due to missing query argument"
                except SystemExit as e:
                    # argparse calls sys.exit(2) for missing required arguments
                    assert e.code == 2, "Should exit with code 2 for missing required argument"
                    
                    # Verify error message about missing argument
                    stderr_output = ''.join([call[0][0] for call in mock_stderr.call_args_list])
                    assert "required" in stderr_output.lower() or "argument" in stderr_output.lower()