"""Migration snapshot specification tests."""

import pytest
import tempfile
import subprocess
from pathlib import Path
import shutil


def test_can_create_snapshot_after_migration():
    """Test that we can create a snapshot of the migrated database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ddl_dir = Path(tmpdir) / "ddl"
        db_dir = Path(tmpdir) / "db"
        
        # Initialize DDL directory using kuzu-migrate
        result = subprocess.run(
            ["kuzu-migrate", "--ddl", str(ddl_dir), "init"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to init: {result.stderr}"
        
        # Copy our migrations
        src_migrations = Path(__file__).parent / "ddl" / "migrations"
        dst_migrations = ddl_dir / "migrations"
        
        # Copy 000_initial.cypher
        shutil.copy2(
            src_migrations / "000_initial.cypher",
            dst_migrations / "000_initial.cypher"
        )
        
        # Apply migrations
        result = subprocess.run(
            ["kuzu-migrate", "--ddl", str(ddl_dir), "--db", str(db_dir), "apply"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to apply migrations: {result.stderr}"
        
        # Create snapshot
        result = subprocess.run(
            ["kuzu-migrate", 
             "--ddl", str(ddl_dir), 
             "--db", str(db_dir),
             "snapshot", 
             "--version", "v1.0.0"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to create snapshot: {result.stderr}"
        
        # Verify snapshot was created
        snapshots_dir = ddl_dir / "snapshots"
        assert snapshots_dir.exists(), "Snapshots directory not created"
        
        snapshot_files = list(snapshots_dir.glob("*v1.0.0*"))
        assert len(snapshot_files) > 0, "No snapshot files created for v1.0.0"


def test_snapshot_contains_schema_state():
    """Test that snapshot contains the current schema state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Similar setup as above but verify snapshot content
        pass  # Will implement after basic snapshot works