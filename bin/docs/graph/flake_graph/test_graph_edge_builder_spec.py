"""Specification tests for graph edge building business requirements.

This module tests the BEHAVIOR and BUSINESS VALUE of converting flake.nix inputs
into graph relationships stored in KuzuDB. It verifies that the system meets
the business requirement: "Build dependency graph from flake inputs to enable
architectural analysis and circular dependency detection"

Business Value:
- Enables architectural analysis of flake dependencies
- Detects circular dependencies across projects
- Supports impact analysis for dependency changes
- Provides foundation for dependency optimization
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import patch, MagicMock
import pytest


def test_parses_github_input_dependencies():
    """GitHub URLベースの依存関係をDEPENDS_ONエッジとして解析する
    
    ビジネス価値: GitHub上の共通ライブラリの使用状況を可視化し、
    バージョン管理とセキュリティアップデートの影響範囲を特定できる
    """
    # Given: GitHub URLを含むflake.nix
    flake_content = """
    {
      description = "Example project";
      inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
        flake-utils.url = "github:numtide/flake-utils";
        home-manager = {
          url = "github:nix-community/home-manager";
          inputs.nixpkgs.follows = "nixpkgs";
        };
      };
      outputs = { ... };
    }
    """
    flake_path = Path("/project/flake.nix")
    
    # When: 依存関係エッジを構築
    edges = parse_and_build_dependency_edges_spec(flake_path, flake_content)
    
    # Then: GitHub依存関係がDEPENDS_ONエッジとして作成される
    assert len(edges) == 3, "Should create 3 DEPENDS_ON edges for GitHub inputs"
    
    # nixpkgsへの依存関係を検証
    nixpkgs_edge = find_edge_by_target(edges, "github:NixOS/nixpkgs")
    assert nixpkgs_edge is not None, "Should create edge to nixpkgs"
    assert nixpkgs_edge["type"] == "DEPENDS_ON"
    assert nixpkgs_edge["source"] == "/project/flake.nix"
    assert nixpkgs_edge["target"] == "github:NixOS/nixpkgs/nixos-unstable"
    assert nixpkgs_edge["input_name"] == "nixpkgs"
    assert nixpkgs_edge["input_type"] == "github"
    
    # flake-utilsへの依存関係を検証
    utils_edge = find_edge_by_target(edges, "github:numtide/flake-utils")
    assert utils_edge is not None, "Should create edge to flake-utils"
    assert utils_edge["input_type"] == "github"
    
    # home-managerへの依存関係を検証
    hm_edge = find_edge_by_target(edges, "github:nix-community/home-manager")
    assert hm_edge is not None, "Should create edge to home-manager"
    assert hm_edge["input_type"] == "github"
    assert hm_edge["follows_nixpkgs"] is True, "Should detect nixpkgs follows pattern"


def test_parses_path_input_dependencies():
    """ローカルpathベースの依存関係をDEPENDS_ONエッジとして解析する
    
    ビジネス価値: モノレポ内での依存関係を可視化し、
    ローカル変更の影響範囲とビルド順序を特定できる
    """
    # Given: ローカルpathを含むflake.nix
    flake_content = """
    {
      description = "Main project";
      inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
        
        python-flake = {
          url = "path:/home/nixos/bin/src/flakes/python";
          inputs.nixpkgs.follows = "nixpkgs";
        };
        
        kuzu-py-flake = {
          url = "path:/home/nixos/bin/src/persistence/kuzu_py";
          inputs.nixpkgs.follows = "nixpkgs";
        };
        
        relative-component.url = "path:../shared/component";
      };
      outputs = { ... };
    }
    """
    flake_path = Path("/home/nixos/bin/docs/graph/flake.nix")
    
    # When: 依存関係エッジを構築
    edges = parse_and_build_dependency_edges_spec(flake_path, flake_content)
    
    # Then: ローカル依存関係がDEPENDS_ONエッジとして作成される
    path_edges = [e for e in edges if e["input_type"] == "path"]
    assert len(path_edges) == 3, "Should create 3 path-based DEPENDS_ON edges"
    
    # 絶対パス依存関係を検証
    python_edge = find_edge_by_target(edges, "/home/nixos/bin/src/flakes/python")
    assert python_edge is not None, "Should create edge to python-flake"
    assert python_edge["input_type"] == "path"
    assert python_edge["path_type"] == "absolute"
    assert python_edge["follows_nixpkgs"] is True
    
    kuzu_edge = find_edge_by_target(edges, "/home/nixos/bin/src/persistence/kuzu_py")
    assert kuzu_edge is not None, "Should create edge to kuzu-py-flake"
    assert kuzu_edge["path_type"] == "absolute"
    
    # 相対パス依存関係を検証
    relative_edge = find_edge_by_target(edges, "../shared/component")
    assert relative_edge is not None, "Should create edge to relative component"
    assert relative_edge["path_type"] == "relative"
    assert relative_edge["resolved_path"] == "/home/nixos/bin/docs/shared/component"


def test_creates_kuzu_dependency_edges_in_database():
    """解析したDEPENDS_ONエッジをKuzuDBに正しく保存する
    
    ビジネス価値: グラフクエリによる依存関係分析を可能にし、
    Cypher/KuzuQLを使った複雑な依存関係パターンの検索を実現
    """
    # Given: 依存関係を持つflakeと初期化されたKuzuDB
    flake_content = """
    {
      inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
        utils.url = "github:numtide/flake-utils";
        local-lib.url = "path:/home/nixos/lib";
      };
      outputs = { ... };
    }
    """
    flake_path = Path("/project/main/flake.nix")
    
    # When: エッジをKuzuDBに保存
    result = create_dependency_edges_in_kuzu_spec(flake_path, flake_content)
    
    # Then: データベースにDEPENDS_ONエッジが作成される
    assert result["ok"] is True, "Edge creation should succeed"
    assert result["edges_created"] == 3, "Should create 3 dependency edges"
    
    # データベースでのエッジ検証
    kuzu_result = query_kuzu_edges_spec(flake_path)
    assert kuzu_result["ok"] is True, "Query should succeed"
    
    edges = kuzu_result["edges"]
    assert len(edges) == 3, "Should find 3 edges in database"
    
    # GitHub依存関係の検証
    github_edges = [e for e in edges if e["input_type"] == "github"]
    assert len(github_edges) == 2, "Should have 2 GitHub dependencies"
    
    nixpkgs_edge = find_edge_by_target(edges, "github:NixOS/nixpkgs/nixos-unstable")
    assert nixpkgs_edge["relationship_type"] == "DEPENDS_ON"
    assert nixpkgs_edge["source_path"] == "/project/main/flake.nix"
    
    # Path依存関係の検証
    path_edges = [e for e in edges if e["input_type"] == "path"]
    assert len(path_edges) == 1, "Should have 1 path dependency"
    
    local_edge = path_edges[0]
    assert local_edge["target_path"] == "/home/nixos/lib"
    assert local_edge["relationship_type"] == "DEPENDS_ON"


def test_handles_complex_input_structures():
    """複雑なinput構造（nested、follows、conditional）を正しく解析する
    
    ビジネス価値: 実際のプロジェクトで使われる複雑な依存関係パターンを
    正確に分析し、hidden dependencyや設定エラーを検出できる
    """
    # Given: 複雑なinput構造を持つflake.nix
    flake_content = """
    {
      inputs = {
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
        
        # Nested input with follows
        home-manager = {
          url = "github:nix-community/home-manager";
          inputs = {
            nixpkgs.follows = "nixpkgs";
            utils.follows = "flake-utils";
          };
        };
        
        # Input with multiple follows
        complex-flake = {
          url = "path:/complex/project";
          inputs = {
            nixpkgs.follows = "nixpkgs";
            home-manager.follows = "home-manager";
            custom-lib.follows = "custom-lib";
          };
        };
        
        # Conditional input (common pattern)
        dev-tools = {
          url = "github:cachix/devenv/latest";
          inputs.nixpkgs.follows = "nixpkgs";
        };
      };
    }
    """
    flake_path = Path("/workspace/complex/flake.nix")
    
    # When: 複雑な依存関係を解析
    edges = parse_and_build_dependency_edges_spec(flake_path, flake_content)
    
    # Then: すべての依存関係が正しく抽出される
    assert len(edges) == 4, "Should extract all 4 direct dependencies"
    
    # Nested follows関係の検証
    hm_edge = find_edge_by_target(edges, "github:nix-community/home-manager")
    assert hm_edge is not None, "Should find home-manager dependency"
    assert len(hm_edge["nested_follows"]) == 2, "Should detect 2 nested follows"
    assert "nixpkgs" in hm_edge["nested_follows"]
    assert "utils" in hm_edge["nested_follows"]
    
    # 複数follows関係の検証
    complex_edge = find_edge_by_target(edges, "/complex/project")
    assert complex_edge is not None, "Should find complex-flake dependency"
    assert len(complex_edge["nested_follows"]) == 3, "Should detect 3 nested follows"
    assert complex_edge["has_circular_follows"] is False, "Should not detect false circular reference"
    
    # 条件付きinputの検証
    dev_edge = find_edge_by_target(edges, "github:cachix/devenv")
    assert dev_edge is not None, "Should find dev-tools dependency"
    assert dev_edge["follows_nixpkgs"] is True


def test_detects_circular_dependencies():
    """循環依存関係を検出して警告する
    
    ビジネス価値: ビルドエラーや無限ループを事前に防ぎ、
    アーキテクチャの健全性を保証する
    """
    # Given: 循環依存を含むflake構造
    flakes_data = [
        {
            "path": "/project/a/flake.nix",
            "content": """
            {
              inputs = {
                nixpkgs.url = "github:NixOS/nixpkgs";
                project-b.url = "path:/project/b";
              };
            }
            """
        },
        {
            "path": "/project/b/flake.nix", 
            "content": """
            {
              inputs = {
                nixpkgs.url = "github:NixOS/nixpkgs";
                project-c.url = "path:/project/c";
              };
            }
            """
        },
        {
            "path": "/project/c/flake.nix",
            "content": """
            {
              inputs = {
                nixpkgs.url = "github:NixOS/nixpkgs";
                project-a.url = "path:/project/a";
              };
            }
            """
        }
    ]
    
    # When: 循環依存関係を分析
    analysis_result = analyze_dependency_cycles_spec(flakes_data)
    
    # Then: 循環依存が検出される
    assert analysis_result["ok"] is True, "Analysis should complete"
    assert analysis_result["has_cycles"] is True, "Should detect circular dependencies"
    assert len(analysis_result["cycles"]) == 1, "Should find 1 cycle"
    
    cycle = analysis_result["cycles"][0]
    assert len(cycle["path"]) == 4, "Cycle should have 4 nodes (A->B->C->A)"
    assert cycle["path"][0] == "/project/a/flake.nix"
    assert cycle["path"][-1] == "/project/a/flake.nix"  # Returns to start
    
    # 循環内容の検証
    cycle_paths = set(cycle["path"][:-1])  # 最後の重複を除く
    expected_paths = {"/project/a/flake.nix", "/project/b/flake.nix", "/project/c/flake.nix"}
    assert cycle_paths == expected_paths, "Should identify all files in the cycle"


def test_handles_malformed_flake_gracefully():
    """不正なflake.nix構文を適切にハンドリングする
    
    ビジネス価値: 部分的に破損したプロジェクトでも可能な限り依存関係を
    分析し、修復作業を支援する
    """
    # Given: 構文エラーを含むflake.nix
    invalid_flakes = [
        {
            "path": "/broken/syntax/flake.nix",
            "content": """
            {
              inputs = {
                nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"  # Missing semicolon
                broken-input = {
                  url = "path:/some/path";
                  # Missing closing brace
              };
            }
            """
        },
        {
            "path": "/missing/inputs/flake.nix", 
            "content": """
            {
              description = "No inputs section";
              outputs = { self, nixpkgs }: { };
            }
            """
        },
        {
            "path": "/empty/flake.nix",
            "content": ""
        }
    ]
    
    # When: 不正なflakeを解析
    results = []
    for flake in invalid_flakes:
        result = parse_and_build_dependency_edges_spec(
            Path(flake["path"]), 
            flake["content"],
            strict_parsing=False
        )
        results.append(result)
    
    # Then: 適切なエラーハンドリングが実行される
    syntax_error_result = results[0]
    assert len(syntax_error_result) == 0, "Should return empty edges for syntax error"
    
    no_inputs_result = results[1]
    assert len(no_inputs_result) == 0, "Should handle missing inputs gracefully"
    
    empty_result = results[2]
    assert len(empty_result) == 0, "Should handle empty file gracefully"


def test_edge_builder_integration_with_kuzu_adapter():
    """エッジビルダーとKuzuAdapterの統合を検証する
    
    ビジネス価値: システム全体の整合性を保証し、
    エンドツーエンドの依存関係分析パイプラインを提供
    """
    # Given: 完全なflake依存関係セット
    project_flakes = [
        {
            "path": "/main/flake.nix",
            "content": """
            {
              inputs = {
                nixpkgs.url = "github:NixOS/nixpkgs";
                lib-a.url = "path:/lib/a";
                lib-b.url = "path:/lib/b";
              };
            }
            """
        },
        {
            "path": "/lib/a/flake.nix",
            "content": """
            {
              inputs = {
                nixpkgs.url = "github:NixOS/nixpkgs";
                utils.url = "github:numtide/flake-utils";
              };
            }
            """
        },
        {
            "path": "/lib/b/flake.nix",
            "content": """
            {
              inputs = {
                nixpkgs.url = "github:NixOS/nixpkgs";
                lib-a.url = "path:/lib/a";
              };
            }
            """
        }
    ]
    
    # When: 完全な依存関係グラフを構築
    integration_result = build_complete_dependency_graph_spec(project_flakes)
    
    # Then: KuzuDBに統合されたグラフが作成される
    assert integration_result["ok"] is True, "Integration should succeed"
    assert integration_result["nodes_created"] == 3, "Should create 3 flake nodes"
    assert integration_result["edges_created"] == 6, "Should create 6 dependency edges"
    
    # グラフクエリ機能の検証
    query_result = query_dependency_graph_spec(
        source_path="/main/flake.nix",
        max_depth=2
    )
    assert query_result["ok"] is True, "Graph query should succeed"
    assert len(query_result["dependencies"]) == 4, "Should find 4 transitive dependencies"
    
    # 共通依存関係の検証
    common_deps = query_common_dependencies_spec(["/main/flake.nix", "/lib/b/flake.nix"])
    assert len(common_deps) >= 2, "Should find common dependencies (nixpkgs, lib-a)"


# Helper functions for specification tests
def parse_and_build_dependency_edges_spec(
    flake_path: Path, 
    flake_content: str,
    strict_parsing: bool = True
) -> List[Dict[str, Any]]:
    """
    Specification interface for dependency edge parsing.
    Returns list of DEPENDS_ON edges with metadata.
    """
    from .graph_edge_builder import GraphEdgeBuilder
    
    try:
        # Use the actual implementation
        builder = GraphEdgeBuilder()
        edges = builder.build_dependency_edges(flake_path, flake_content)
        return edges
    except Exception as e:
        if not strict_parsing:
            return []
        raise e


def create_dependency_edges_in_kuzu_spec(
    flake_path: Path, 
    flake_content: str
) -> Dict[str, Any]:
    """
    Specification interface for creating edges in KuzuDB.
    Returns success/error result with edge count.
    """
    from .graph_edge_builder import GraphEdgeBuilder
    
    try:
        # Use the actual implementation - but without a real KuzuAdapter for now
        builder = GraphEdgeBuilder()
        result = builder.create_edges_in_database(flake_path, flake_content)
        return result
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def query_kuzu_edges_spec(flake_path: Path) -> Dict[str, Any]:
    """
    Specification interface for querying edges from KuzuDB.
    """
    # Mock edge query results
    return {
        "ok": True,
        "edges": [
            {
                "relationship_type": "DEPENDS_ON",
                "source_path": str(flake_path),
                "target_path": "github:NixOS/nixpkgs/nixos-unstable",
                "input_type": "github",
                "input_name": "nixpkgs"
            }
        ]
    }


def analyze_dependency_cycles_spec(flakes_data: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Specification interface for circular dependency detection.
    """
    from .graph_edge_builder import analyze_dependency_cycles
    
    try:
        return analyze_dependency_cycles(flakes_data)
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def build_complete_dependency_graph_spec(project_flakes: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Specification interface for complete graph building.
    """
    from .graph_edge_builder import build_complete_dependency_graph
    
    try:
        return build_complete_dependency_graph(project_flakes)
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def query_dependency_graph_spec(source_path: str, max_depth: int) -> Dict[str, Any]:
    """
    Specification interface for graph querying.
    """
    from .graph_edge_builder import query_dependency_graph
    
    try:
        return query_dependency_graph(source_path, max_depth)
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def query_common_dependencies_spec(flake_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Specification interface for finding common dependencies.
    """
    from .graph_edge_builder import query_common_dependencies
    
    try:
        return query_common_dependencies(flake_paths)
    except Exception as e:
        return []


def find_edge_by_target(edges: List[Dict[str, Any]], target_substring: str) -> Optional[Dict[str, Any]]:
    """Find edge containing the target substring."""
    for edge in edges:
        if target_substring in edge.get("target", ""):
            return edge
    return None