"""Basic E2E test for core workflow integration."""

from pathlib import Path
import tempfile
import pytest
from kuzu_py import Database, Connection

from flake_graph.scanner import scan_flake_description
from flake_graph.models_functional import create_flake_info
from flake_graph.duplicate_detector import find_duplicate_flakes
from flake_graph.readme_checker import check_missing_readmes


def test_basic_workflow_integration():
    """Test basic workflow without VSS: scan -> duplicate detection -> README check."""
    # Test flakes with various characteristics
    test_flakes = [
        {
            "path": "persistence/kuzu_py/flake.nix",
            "content": '''
{
  description = "KuzuDB thin wrapper for Python - provides graph database functionality";
  inputs = { nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; };
  outputs = { self, nixpkgs }: { };
}
''',
            "has_readme": True,
            "readme_content": "# KuzuDB Python Wrapper\n\nProvides Python bindings for KuzuDB graph database."
        },
        {
            "path": "persistence/kuzu_ts/flake.nix", 
            "content": '''
{
  description = "KuzuDB thin wrapper for Python - provides graph database functionality";
  inputs = { nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; };
  outputs = { self, nixpkgs }: { };
}
''',
            "has_readme": False
        },
        {
            "path": "telemetry/log_py/flake.nix",
            "content": '''
{
  description = "Python implementation of universal log API";
  inputs = { nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; };
  outputs = { self, nixpkgs }: { };
}
''',
            "has_readme": True,
            "readme_content": "# Log API for Python\n\nUniversal logging interface."
        },
        {
            "path": "search/vss_graph/flake.nix",
            "content": '''
{
  description = "Vector Similarity Search for graph exploration";
  inputs = { nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; };
  outputs = { self, nixpkgs }: { };
}
''',
            "has_readme": True,
            "readme_content": "# VSS Graph Search\n\nVector similarity search for graph databases."
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Create test environment with flakes and READMEs
        flake_infos = []
        for test_flake in test_flakes:
            flake_path = Path(tmpdir) / test_flake["path"]
            flake_path.parent.mkdir(parents=True, exist_ok=True)
            flake_path.write_text(test_flake["content"])
            
            # Create README if specified
            if test_flake.get("has_readme"):
                readme_path = flake_path.parent / "README.md"
                readme_path.write_text(test_flake["readme_content"])
            
            # Scan flake description
            description = scan_flake_description(flake_path)
            assert description is not None, f"Failed to scan {flake_path}"
            
            info = create_flake_info(
                path=flake_path,
                description=description
            )
            flake_infos.append(info)
        
        # Step 2: Setup KuzuDB and store flakes
        db_path = Path(tmpdir) / "test.kuzu"
        db = Database(str(db_path))
        conn = Connection(db)
        
        # Create schema
        conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Flake(
                id STRING PRIMARY KEY,
                description STRING
            )
        """)
        
        # Insert flakes
        for info in flake_infos:
            flake_id = str(info["path"].relative_to(tmpdir).parent)
            conn.execute("""
                MERGE (f:Flake {id: $id})
                SET f.description = $description
            """, {
                "id": flake_id,
                "description": info["description"]
            })
        
        # Step 3: Basic search - find KuzuDB flakes
        result = conn.execute("""
            MATCH (f:Flake)
            WHERE f.description CONTAINS 'KuzuDB'
            RETURN f.id as id, f.description as description
        """)
        
        kuzu_flakes = []
        while result.has_next():
            row = result.get_next()
            kuzu_flakes.append({"id": row[0], "description": row[1]})
        
        assert len(kuzu_flakes) == 2, "Should find exactly 2 KuzuDB flakes"
        kuzu_ids = [f["id"] for f in kuzu_flakes]
        assert "persistence/kuzu_py" in kuzu_ids
        assert "persistence/kuzu_ts" in kuzu_ids
        
        # Step 4: Duplicate Detection (without VSS)
        duplicates = find_duplicate_flakes(flakes=flake_infos, use_vss=False)
        
        # Should find duplicate KuzuDB descriptions
        assert len(duplicates) > 0, "Should find at least one duplicate group"
        
        # Check that KuzuDB flakes are in the same duplicate group
        kuzu_duplicate_found = False
        for group in duplicates:
            flake_paths = [str(f["path"].relative_to(tmpdir).parent) for f in group["flakes"]]
            if "persistence/kuzu_py" in flake_paths and "persistence/kuzu_ts" in flake_paths:
                kuzu_duplicate_found = True
                break
        assert kuzu_duplicate_found, "Should detect KuzuDB wrappers as duplicates"
        
        # Step 5: README Checker
        missing_readmes = check_missing_readmes(Path(tmpdir))
        
        # Verify README detection - only kuzu_ts should be missing README
        assert len(missing_readmes) == 1
        missing_readme_paths = [str(p.relative_to(tmpdir)) for p in missing_readmes]
        assert "persistence/kuzu_ts" in missing_readme_paths
        
        # Step 6: Integration Summary
        # Count total projects, duplicates, and missing docs
        total_projects = len(flake_infos)
        duplicate_groups = len(duplicates)
        missing_docs = len(missing_readmes)
        doc_coverage = (total_projects - missing_docs) / total_projects * 100
        
        # Verify summary metrics
        assert total_projects == 4
        assert duplicate_groups >= 1
        assert missing_docs == 1
        assert doc_coverage == 75.0
        
        # Final workflow validation
        print(f"\nWorkflow Summary:")
        print(f"- Total projects scanned: {total_projects}")
        print(f"- Duplicate groups found: {duplicate_groups}")
        print(f"- Projects missing README: {missing_docs}")
        print(f"- Documentation coverage: {doc_coverage:.1f}%")
        
        conn.close()
        db.close()


if __name__ == "__main__":
    test_basic_workflow_integration()
    print("\nBasic E2E test passed!")