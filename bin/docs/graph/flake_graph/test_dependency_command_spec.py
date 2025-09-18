"""Specification tests for flake dependency analysis command functionality.

This module tests the BEHAVIOR and BUSINESS VALUE of the dependency analysis command.
It verifies that the system meets the business requirement:
"Developers can analyze flake dependencies to understand architectural relationships"

Business Context:
- Current: Developers manually inspect flake.nix files to understand dependencies
- Target: Automated dependency discovery and visualization with tree displays  
- Impact: Faster impact analysis, dependency optimization, circular dependency detection

Technical Requirements:
- Direct dependency analysis: Show what a flake depends on
- Reverse dependency analysis: Show what depends on a flake  
- Tree visualization for multi-level dependency chains
- Support for both GitHub and local path dependencies
- Circular dependency detection for architectural health

Business Value:
- 60-80% reduction in time spent on impact analysis
- Early detection of architectural issues (circular dependencies)
- Support for dependency refactoring and optimization decisions
- Clear visualization of architectural complexity
"""

import pytest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock
import argparse
import json

# Import the CLI module to test dependency command
from flake_graph.cli import main


class TestDependencyCommandBehavior:
    """Test dependency analysis command behavior and business value."""
    
    def test_shows_direct_dependencies_of_flake(self):
        """指定フレークの直接依存関係を表示する
        
        ビジネス価値:
        - 開発者が変更影響を素早く分析可能
        - 依存関係の把握によるリスク評価
        - アーキテクチャの理解促進
        """
        # RED: This test will fail because 'deps' command doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'deps', '/test/flakes/web/frontend', '--path', '/test/flakes']):
            with patch('sys.stdout.write') as mock_stdout:
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock flake.nix content with dependencies
                    flake_content = """
                    {
                      inputs = {
                        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
                        react-utils.url = "path:../shared/react-utils";
                        tailwind-config.url = "github:company/tailwind-base";
                      };
                      outputs = { nixpkgs, react-utils, tailwind-config }: { };
                    }
                    """
                    
                    with patch('pathlib.Path.read_text', return_value=flake_content):
                        # Mock dependency parser
                        with patch('flake_graph.graph_edge_builder.FlakeInputParser') as mock_parser:
                            mock_parser_instance = mock_parser.return_value
                            mock_parser_instance.parse_inputs.return_value = [
                                {"name": "nixpkgs", "url": "github:NixOS/nixpkgs/nixos-unstable", "is_local": False},
                                {"name": "react-utils", "url": "path:../shared/react-utils", "is_local": True},
                                {"name": "tailwind-config", "url": "github:company/tailwind-base", "is_local": False}
                            ]
                            
                            result = main()
                            
                            # Expected: Should show direct dependencies
                            assert result == 0, "Dependencies command should succeed"
                            
                            # Verify dependencies were displayed
                            stdout_calls = [str(call) for call in mock_stdout.call_args_list]
                            stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                            
                            # Should show all three dependencies
                            assert "nixpkgs" in stdout_output.lower()
                            assert "react-utils" in stdout_output.lower()  
                            assert "tailwind-config" in stdout_output.lower()
                            # Should indicate GitHub vs local dependencies
                            assert "github:" in stdout_output or "local:" in stdout_output
    
    def test_shows_reverse_dependencies_who_uses_flake(self):
        """指定フレークを使用している他のフレークを表示する（逆依存）
        
        ビジネス価値:
        - 変更の影響範囲を事前に把握
        - 共有コンポーネントのリファクタリング計画支援
        - 依存関係の最適化決定をサポート
        """
        # RED: This test will fail because 'deps --reverse' doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'deps', '/test/flakes/shared/auth', '--reverse', '--path', '/test/flakes']):
            with patch('sys.stdout.write') as mock_stdout:
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock database query for reverse dependencies
                    with patch('flake_graph.kuzu_adapter.KuzuAdapter') as mock_adapter:
                        mock_db = mock_adapter.return_value.__enter__.return_value
                        # Mock query result showing flakes that depend on 'shared/auth'
                        mock_db.query.return_value = [
                            {"dependent_flake": "/test/flakes/web/frontend", "dependency_type": "direct"},
                            {"dependent_flake": "/test/flakes/api/backend", "dependency_type": "direct"},
                            {"dependent_flake": "/test/flakes/mobile/app", "dependency_type": "transitive"}
                        ]
                        
                        result = main()
                        
                        # Expected: Should show reverse dependencies
                        assert result == 0, "Reverse dependencies command should succeed"
                        
                        # Verify reverse dependencies were displayed
                        stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                        
                        # Should show flakes that depend on shared/auth
                        assert "frontend" in stdout_output.lower()
                        assert "backend" in stdout_output.lower()
                        assert "mobile" in stdout_output.lower()
                        # Should distinguish direct vs transitive dependencies
                        assert "direct" in stdout_output.lower() or "transitive" in stdout_output.lower()
    
    def test_displays_dependency_tree_forward(self):
        """依存関係をツリー形式で表示する（順方向）
        
        ビジネス価値:
        - 複雑な依存チェーンの視覚的理解
        - アーキテクチャの複雑度把握
        - 依存関係の最適化機会発見
        """
        # RED: This test will fail because 'deps --tree' doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'deps', '/test/flakes/web/frontend', '--tree', '--path', '/test/flakes']):
            with patch('sys.stdout.write') as mock_stdout:
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock dependency tree data
                    with patch('flake_graph.kuzu_adapter.KuzuAdapter') as mock_adapter:
                        mock_db = mock_adapter.return_value.__enter__.return_value
                        # Mock recursive dependency query results
                        mock_db.query.return_value = [
                            {"path": "/test/flakes/web/frontend", "level": 0, "dependency": None},
                            {"path": "/test/flakes/shared/react-utils", "level": 1, "dependency": "react-utils"},
                            {"path": "/test/flakes/shared/ui-components", "level": 2, "dependency": "ui-components"},
                            {"path": "github:NixOS/nixpkgs", "level": 1, "dependency": "nixpkgs"},
                        ]
                        
                        result = main()
                        
                        # Expected: Should display tree structure
                        assert result == 0, "Dependency tree command should succeed"
                        
                        # Verify tree structure in output
                        stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                        
                        # Should show hierarchical structure with indentation or tree symbols
                        assert "├─" in stdout_output or "└─" in stdout_output or "  " in stdout_output
                        # Should show all levels of dependencies
                        assert "react-utils" in stdout_output.lower()
                        assert "ui-components" in stdout_output.lower()
                        assert "nixpkgs" in stdout_output.lower()
    
    def test_displays_reverse_dependency_tree(self):
        """逆依存関係をツリー形式で表示する
        
        ビジネス価値:
        - 変更の影響範囲の完全な可視化
        - 共有コンポーネント変更時のリスク評価
        - 依存関係リファクタリングの計画支援
        """
        # RED: This test will fail because 'deps --reverse --tree' doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'deps', '/test/flakes/shared/auth', '--reverse', '--tree', '--path', '/test/flakes']):
            with patch('sys.stdout.write') as mock_stdout:
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock reverse dependency tree data
                    with patch('flake_graph.kuzu_adapter.KuzuAdapter') as mock_adapter:
                        mock_db = mock_adapter.return_value.__enter__.return_value
                        # Mock reverse tree query results
                        mock_db.query.return_value = [
                            {"path": "/test/flakes/shared/auth", "level": 0, "dependent": None},
                            {"path": "/test/flakes/web/frontend", "level": 1, "dependent": "frontend"},
                            {"path": "/test/flakes/web/admin-panel", "level": 2, "dependent": "admin-panel"},
                            {"path": "/test/flakes/api/backend", "level": 1, "dependent": "backend"},
                            {"path": "/test/flakes/mobile/app", "level": 2, "dependent": "mobile-app"},
                        ]
                        
                        result = main()
                        
                        # Expected: Should display reverse tree structure
                        assert result == 0, "Reverse dependency tree command should succeed"
                        
                        # Verify reverse tree structure in output
                        stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                        
                        # Should show reverse hierarchical structure
                        assert "├─" in stdout_output or "└─" in stdout_output or "  " in stdout_output
                        # Should show all levels of dependents
                        assert "frontend" in stdout_output.lower()
                        assert "admin-panel" in stdout_output.lower()
                        assert "backend" in stdout_output.lower()
                        assert "mobile" in stdout_output.lower()
    
    def test_detects_circular_dependencies(self):
        """循環依存関係を検出して警告する
        
        ビジネス価値:
        - アーキテクチャ問題の早期発見
        - ビルド失敗の予防
        - 技術的負債の可視化
        """
        # RED: This test will fail because circular dependency detection doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'deps', '/test/flakes/service-a', '--check-cycles', '--path', '/test/flakes']):
            with patch('sys.stdout.write') as mock_stdout:
                with patch('sys.stderr.write') as mock_stderr:
                    with patch('pathlib.Path.exists', return_value=True):
                        # Mock circular dependency detection
                        with patch('flake_graph.kuzu_adapter.KuzuAdapter') as mock_adapter:
                            mock_db = mock_adapter.return_value.__enter__.return_value
                            # Mock cycle detection query result
                            mock_db.query.return_value = [
                                {
                                    "cycle_path": "/test/flakes/service-a → /test/flakes/service-b → /test/flakes/service-c → /test/flakes/service-a",
                                    "cycle_length": 3
                                }
                            ]
                            
                            result = main()
                            
                            # Expected: Should detect and warn about circular dependencies
                            assert result != 0, "Should return error code when circular dependencies found"
                            
                            # Verify circular dependency warning
                            stderr_output = ''.join([call[0][0] for call in mock_stderr.call_args_list])
                            stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                            
                            output = stderr_output + stdout_output
                            assert "circular" in output.lower() or "cycle" in output.lower()
                            assert "service-a" in output.lower()
                            assert "service-b" in output.lower() 
                            assert "service-c" in output.lower()
    
    def test_dependency_analysis_with_json_output(self):
        """依存関係分析結果をJSON形式で出力
        
        ビジネス価値:
        - 自動化ツールとの連携
        - CI/CDパイプラインでの依存関係チェック
        - プログラマティックな分析処理
        """
        # RED: This test will fail because 'deps --json' doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'deps', '/test/flakes/web/frontend', '--json', '--path', '/test/flakes']):
            with patch('sys.stdout.write') as mock_stdout:
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock dependency data
                    with patch('flake_graph.dependency_command.FlakeInputParser') as mock_parser:
                        mock_parser_instance = mock_parser.return_value
                        mock_parser_instance.parse_inputs.return_value = [
                            {"input_name": "nixpkgs", "url": "github:NixOS/nixpkgs/nixos-unstable", "input_type": "github"},
                            {"input_name": "react-utils", "url": "path:../shared/react-utils", "input_type": "path"}
                        ]
                        
                        with patch('pathlib.Path.read_text', return_value="mock flake content"):
                            result = main()
                            
                            # Expected: Should output JSON formatted dependencies
                            assert result == 0, "JSON dependency output should work"
                            
                            # Verify JSON output
                            stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                            
                            # Should be valid JSON
                            try:
                                json_data = json.loads(stdout_output)
                                assert isinstance(json_data, dict), "Should output JSON object"
                                assert "dependencies" in json_data, "Should have dependencies field"
                                assert "flake_path" in json_data, "Should have flake_path field"
                                
                                # Verify dependency structure
                                deps = json_data["dependencies"]
                                assert len(deps) == 2, "Should have 2 dependencies"
                                assert any(d["name"] == "nixpkgs" for d in deps), "Should include nixpkgs"
                                assert any(d["name"] == "react-utils" for d in deps), "Should include react-utils"
                            except json.JSONDecodeError:
                                assert False, f"Output should be valid JSON, got: {stdout_output}"
    
    def test_dependency_depth_limiting(self):
        """依存関係の探索深度を制限する
        
        ビジネス価値:
        - 大規模プロジェクトでの性能確保
        - 関心のある範囲に集中した分析
        - 深すぎる依存チェーンの制御
        """
        # RED: This test will fail because 'deps --depth' doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'deps', '/test/flakes/web/frontend', '--tree', '--depth', '2', '--path', '/test/flakes']):
            with patch('sys.stdout.write') as mock_stdout:
                with patch('pathlib.Path.exists', return_value=True):
                    # Mock dependency tree with multiple levels
                    with patch('flake_graph.kuzu_adapter.KuzuAdapter') as mock_adapter:
                        mock_db = mock_adapter.return_value.__enter__.return_value
                        # Mock query with depth limiting
                        mock_db.query.return_value = [
                            {"path": "/test/flakes/web/frontend", "level": 0},
                            {"path": "/test/flakes/shared/react-utils", "level": 1},
                            {"path": "/test/flakes/shared/ui-components", "level": 2},
                            # Level 3 should be filtered out due to --depth 2
                        ]
                        
                        result = main()
                        
                        # Expected: Should limit tree depth to 2 levels
                        assert result == 0, "Depth-limited dependency tree should work"
                        
                        # Verify depth limiting worked
                        stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                        
                        # Should show levels 0, 1, and 2 only
                        assert "frontend" in stdout_output.lower()
                        assert "react-utils" in stdout_output.lower()
                        assert "ui-components" in stdout_output.lower()


class TestDependencyCommandIntegration:
    """Integration tests for dependency command with actual CLI parsing."""
    
    def test_dependency_command_argument_parsing(self):
        """依存関係コマンドの引数解析
        
        ビジネス価値:
        - 直感的なコマンドライン操作
        - 標準的なCLIツールとしての使いやすさ
        - 開発者の学習コストを最小化
        """
        # RED: Command doesn't exist yet, so help parsing will fail
        with patch('sys.argv', ['flake-graph', 'deps', '--help']):
            with patch('sys.stdout.write') as mock_stdout:
                with patch('sys.stderr.write'):
                    # This should show help for deps command
                    try:
                        result = main()
                        assert False, "main() should raise SystemExit for --help"
                    except SystemExit as e:
                        # argparse calls sys.exit(0) when showing help
                        assert e.code == 0, "Help should exit with code 0"
                        
                        # Verify help was shown
                        stdout_output = ''.join([call[0][0] for call in mock_stdout.call_args_list])
                        assert "deps" in stdout_output.lower() or "depend" in stdout_output.lower()
    
    def test_dependency_command_requires_flake_path_argument(self):
        """依存関係分析にはフレークパス引数が必須
        
        ビジネス価値:
        - 明確なエラーメッセージによる使いやすさ
        - 不正な使用方法の早期検出
        - コマンドライン操作の一貫性
        """
        # RED: Command doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'deps']):  # Missing flake path
            with patch('sys.stderr.write') as mock_stderr:
                try:
                    result = main()
                    assert False, "Should have failed due to missing flake path argument"
                except SystemExit as e:
                    # argparse calls sys.exit(2) for missing required arguments
                    assert e.code == 2, "Should exit with code 2 for missing required argument"
                    
                    # Verify error message about missing argument
                    stderr_output = ''.join([call[0][0] for call in mock_stderr.call_args_list])
                    assert "required" in stderr_output.lower() or "argument" in stderr_output.lower()
    
    def test_dependency_command_handles_invalid_flake_path(self):
        """存在しないフレークパスの適切な処理
        
        ビジネス価値:
        - エラー処理による安定性
        - ユーザーに分かりやすいフィードバック
        - 誤入力に対する適切な応答
        """
        # RED: Command doesn't exist yet
        with patch('sys.argv', ['flake-graph', 'deps', '/nonexistent/flake/path', '--path', '/test/flakes']):
            with patch('pathlib.Path.exists', return_value=False):
                with patch('sys.stderr.write') as mock_stderr:
                    result = main()
                    
                    # Expected: Should return error code for invalid path
                    assert result != 0, "Should return error code for invalid flake path"
                    
                    # Verify error message about invalid path
                    stderr_output = ''.join([call[0][0] for call in mock_stderr.call_args_list])
                    assert "not exist" in stderr_output.lower() or "not found" in stderr_output.lower()


# Helper functions for testing (these would be implemented in the actual command)
def detect_duplicate_flakes_spec(flakes, similarity_threshold=0.8):
    """Mock function for duplicate detection spec testing."""
    # This is a placeholder that would be replaced by actual implementation
    pass

def find_group_containing_path(groups, path_suffix):
    """Helper to find a group containing a path with specific suffix."""
    # This is a placeholder helper function
    pass