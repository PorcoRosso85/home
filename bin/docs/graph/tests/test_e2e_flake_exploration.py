"""End-to-end test for flake exploration functionality."""

from pathlib import Path
import tempfile

import pytest
import kuzu

from flake_graph.scanner import scan_flake_description
from flake_graph.models_functional import create_flake_info, get_flake_id


def test_can_explore_flake_responsibilities():
    """Test that we can scan flakes, store in graph, and search responsibilities."""
    # Create test flakes
    test_flakes = [
        {
            "path": "persistence/kuzu_py/flake.nix",
            "content": '''
{
  description = "KuzuDB thin wrapper for Python";
  inputs = { nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; };
  outputs = { self, nixpkgs }: { };
}
'''
        },
        {
            "path": "telemetry/log_py/flake.nix", 
            "content": '''
{
  description = "Python implementation of universal log API";
  inputs = { nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; };
  outputs = { self, nixpkgs }: { };
}
'''
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test flake files
        flake_infos = []
        for test_flake in test_flakes:
            flake_path = Path(tmpdir) / test_flake["path"]
            flake_path.parent.mkdir(parents=True, exist_ok=True)
            flake_path.write_text(test_flake["content"])
            
            # Scan description
            description = scan_flake_description(flake_path)
            assert description is not None
            
            # Create flake info
            info = create_flake_info(
                path=flake_path,
                description=description
            )
            flake_infos.append(info)
        
        # Create temporary KuzuDB
        db_path = Path(tmpdir) / "test.kuzu"
        db = kuzu.Database(str(db_path))
        conn = kuzu.Connection(db)
        
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
        
        # Search for KuzuDB-related flakes
        result = conn.execute("""
            MATCH (f:Flake)
            WHERE f.description CONTAINS 'KuzuDB'
            RETURN f.id as id, f.description as description
        """)
        
        rows = []
        while result.has_next():
            rows.append(result.get_next())
        
        assert len(rows) == 1
        assert rows[0][0] == "persistence/kuzu_py"  # id
        assert "KuzuDB" in rows[0][1]  # description
        
        # Search for log-related flakes
        result = conn.execute("""
            MATCH (f:Flake)
            WHERE f.description CONTAINS 'log'
            RETURN f.id as id, f.description as description
        """)
        
        rows = []
        while result.has_next():
            rows.append(result.get_next())
            
        assert len(rows) == 1
        assert rows[0][0] == "telemetry/log_py"  # id
        assert "log" in rows[0][1]  # description
        
        conn.close()
        db.close()