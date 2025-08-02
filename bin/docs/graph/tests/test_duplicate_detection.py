"""Test duplicate flake detection functionality."""

import tempfile
from pathlib import Path

from flake_graph.duplicate_detector import find_duplicate_flakes
from flake_graph.scanner import scan_flake_description


def test_detect_exact_duplicate_descriptions():
    """同一のdescriptionを持つflakeを検出できる"""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        
        # Create flakes with identical descriptions
        flake1_dir = base_dir / "service1"
        flake1_dir.mkdir()
        (flake1_dir / "flake.nix").write_text('''
{
  description = "User authentication service";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };
  
  outputs = { self, nixpkgs }: {
    # Implementation
  };
}
''')
        
        flake2_dir = base_dir / "service2"
        flake2_dir.mkdir()
        (flake2_dir / "flake.nix").write_text('''
{
  description = "User authentication service";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };
  
  outputs = { self, nixpkgs }: {
    # Different implementation
  };
}
''')
        
        # Scan flakes
        flakes = []
        for flake_dir in [flake1_dir, flake2_dir]:
            flake_nix_path = flake_dir / "flake.nix"
            description = scan_flake_description(flake_nix_path)
            if description:
                flakes.append({
                    "path": flake_dir,
                    "description": description
                })
        
        # Find duplicates
        duplicates = find_duplicate_flakes(flakes)
        
        assert len(duplicates) == 1
        assert duplicates[0]["description"] == "User authentication service"
        assert len(duplicates[0]["flakes"]) == 2
        assert set(f["path"].name for f in duplicates[0]["flakes"]) == {"service1", "service2"}


def test_no_duplicates_when_all_unique():
    """すべてのflakeが異なるdescriptionを持つ場合、重複なし"""
    flakes = [
        {"path": Path("/src/auth"), "description": "Authentication service"},
        {"path": Path("/src/payment"), "description": "Payment processing"},
        {"path": Path("/src/notification"), "description": "Notification system"}
    ]
    
    duplicates = find_duplicate_flakes(flakes)
    
    assert len(duplicates) == 0


def test_multiple_duplicate_groups():
    """複数の重複グループを検出できる"""
    flakes = [
        {"path": Path("/src/auth1"), "description": "User authentication"},
        {"path": Path("/src/auth2"), "description": "User authentication"},
        {"path": Path("/src/log1"), "description": "Logging service"},
        {"path": Path("/src/log2"), "description": "Logging service"},
        {"path": Path("/src/unique"), "description": "Unique service"}
    ]
    
    duplicates = find_duplicate_flakes(flakes)
    
    assert len(duplicates) == 2
    
    # Check first duplicate group
    auth_group = next(d for d in duplicates if d["description"] == "User authentication")
    assert len(auth_group["flakes"]) == 2
    
    # Check second duplicate group
    log_group = next(d for d in duplicates if d["description"] == "Logging service")
    assert len(log_group["flakes"]) == 2


def test_detect_similar_descriptions_with_vss():
    """VSSを使用して類似したdescriptionを検出できる"""
    flakes = [
        {"path": Path("/src/auth1"), "description": "ユーザー認証機能を提供するサービス"},
        {"path": Path("/src/auth2"), "description": "ユーザーの認証を行うシステム"},
        {"path": Path("/src/payment"), "description": "決済処理を行うサービス"}
    ]
    
    # Find similar flakes using VSS
    similar_groups = find_duplicate_flakes(flakes, use_vss=True, similarity_threshold=0.8)
    
    # Auth services should be detected as similar
    assert len(similar_groups) >= 1
    auth_group = similar_groups[0]
    assert len(auth_group["flakes"]) == 2
    assert auth_group["similarity_score"] >= 0.8