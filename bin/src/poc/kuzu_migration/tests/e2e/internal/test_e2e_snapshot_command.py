"""End-to-end tests for kuzu-migrate snapshot command."""

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pytest


@pytest.mark.internal
class TestE2ESnapshotCommand:
    """E2E tests for the snapshot command functionality."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Set up paths
            workspace = Path(tmp_dir)
            ddl_dir = workspace / "ddl"
            db_path = workspace / "data" / "kuzu.db"
            kuzu_migrate = Path(__file__).parent.parent.parent.parent / "src" / "kuzu-migrate.sh"
            
            yield {
                "workspace": workspace,
                "ddl_dir": ddl_dir,
                "db_path": db_path,
                "kuzu_migrate": str(kuzu_migrate),
            }

    def run_kuzu_migrate(self, cmd_args, workspace_info, check=True):
        """Run the kuzu-migrate command with given arguments."""
        cmd = [
            "bash",
            workspace_info["kuzu_migrate"],
            "--ddl", str(workspace_info["ddl_dir"]),
            "--db", str(workspace_info["db_path"]),
        ] + cmd_args
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
        )
        return result

    def setup_test_database(self, workspace_info):
        """Initialize DDL directory and apply a sample migration."""
        # Initialize DDL directory
        self.run_kuzu_migrate(["init"], workspace_info)
        
        # Create a simple migration
        migrations_dir = workspace_info["ddl_dir"] / "migrations"
        migration_file = migrations_dir / "001_create_test_table.cypher"
        migration_file.write_text("""
-- Test migration for snapshot testing
CREATE NODE TABLE TestTable (
    id STRING PRIMARY KEY,
    name STRING NOT NULL,
    created_at TIMESTAMP DEFAULT now()
);

-- Add some test data
CREATE (:TestTable {id: 'test1', name: 'Test Entity 1'});
CREATE (:TestTable {id: 'test2', name: 'Test Entity 2'});
""")
        
        # Apply migrations
        self.run_kuzu_migrate(["apply"], workspace_info)

    def test_snapshot_creation_with_version_parameter(self, temp_workspace):
        """Test creating a snapshot with a specific version parameter."""
        # Setup
        self.setup_test_database(temp_workspace)
        
        # Create snapshot with version
        version = "v1.0.0"
        result = self.run_kuzu_migrate(["snapshot", "--version", version], temp_workspace)
        
        # Assertions
        assert result.returncode == 0
        assert f"Creating snapshot: {version}" in result.stdout
        assert "Database exported successfully!" in result.stdout
        assert "Snapshot completed successfully!" in result.stdout
        
        # Verify snapshot directory exists
        snapshot_dir = temp_workspace["ddl_dir"] / "snapshots" / version
        assert snapshot_dir.exists()
        assert snapshot_dir.is_dir()

    def test_snapshot_directory_structure_creation(self, temp_workspace):
        """Test that snapshot creates the correct directory structure."""
        # Setup
        self.setup_test_database(temp_workspace)
        
        # Create snapshot with timestamp
        result = self.run_kuzu_migrate(["snapshot"], temp_workspace)
        
        # Extract snapshot name from output
        output_lines = result.stdout.split('\n')
        snapshot_line = [line for line in output_lines if "Creating snapshot:" in line][0]
        snapshot_name = snapshot_line.split("Creating snapshot:")[1].strip()
        
        # Verify directory structure
        snapshot_dir = temp_workspace["ddl_dir"] / "snapshots" / snapshot_name
        assert snapshot_dir.exists()
        
        # Check for expected files/directories in snapshot
        # KuzuDB exports create schema.cypher and table directories
        expected_items = ["schema.cypher", "snapshot_metadata.json"]
        for item in expected_items:
            item_path = snapshot_dir / item
            assert item_path.exists(), f"Expected {item} in snapshot directory"
        
        # Verify metadata file content
        metadata_path = snapshot_dir / "snapshot_metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata["snapshot_name"] == snapshot_name
        assert "created_at" in metadata
        assert metadata["database_path"] == str(temp_workspace["db_path"])
        assert metadata["last_migration"] == "001_create_test_table.cypher"

    def test_export_database_functionality(self, temp_workspace):
        """Test that EXPORT DATABASE command works correctly."""
        # Setup
        self.setup_test_database(temp_workspace)
        
        # Create snapshot
        version = "v1.0.1"
        result = self.run_kuzu_migrate(["snapshot", "--version", version], temp_workspace)
        
        assert result.returncode == 0
        
        # Verify exported content
        snapshot_dir = temp_workspace["ddl_dir"] / "snapshots" / version
        
        # Check schema.cypher exists and contains expected content
        schema_file = snapshot_dir / "schema.cypher"
        assert schema_file.exists()
        schema_content = schema_file.read_text()
        assert "CREATE NODE TABLE" in schema_content or "TestTable" in schema_content
        
        # Check for table data export
        # KuzuDB exports table data in subdirectories
        # The exact structure depends on KuzuDB version, but there should be some data files
        snapshot_contents = list(snapshot_dir.iterdir())
        assert len(snapshot_contents) >= 2  # At least schema.cypher and metadata.json

    def test_error_handling_for_existing_snapshots(self, temp_workspace):
        """Test error handling when trying to create a snapshot that already exists."""
        # Setup
        self.setup_test_database(temp_workspace)
        
        # Create first snapshot
        version = "v1.0.2"
        result1 = self.run_kuzu_migrate(["snapshot", "--version", version], temp_workspace)
        assert result1.returncode == 0
        
        # Try to create the same snapshot again
        result2 = self.run_kuzu_migrate(
            ["snapshot", "--version", version], 
            temp_workspace,
            check=False
        )
        
        # Should fail with appropriate error message
        assert result2.returncode != 0
        assert "Snapshot already exists" in result2.stderr
        assert version in result2.stderr
        assert "Choose a different version" in result2.stderr

    def test_snapshot_without_version_uses_timestamp(self, temp_workspace):
        """Test that snapshot without version parameter uses timestamp-based naming."""
        # Setup
        self.setup_test_database(temp_workspace)
        
        # Create snapshot without version
        before_time = datetime.now()
        result = self.run_kuzu_migrate(["snapshot"], temp_workspace)
        after_time = datetime.now()
        
        assert result.returncode == 0
        
        # Extract snapshot name and verify it's timestamp-based
        output_lines = result.stdout.split('\n')
        snapshot_line = [line for line in output_lines if "Creating snapshot:" in line][0]
        snapshot_name = snapshot_line.split("Creating snapshot:")[1].strip()
        
        assert snapshot_name.startswith("snapshot_")
        assert len(snapshot_name) > len("snapshot_")  # Has timestamp suffix
        
        # Verify timestamp format (YYYYMMDD_HHMMSS)
        timestamp_part = snapshot_name.replace("snapshot_", "")
        assert len(timestamp_part) == 15  # 8 + 1 + 6
        assert timestamp_part[8] == "_"
        
        # Parse and validate timestamp is within expected range
        date_part = timestamp_part[:8]
        time_part = timestamp_part[9:]
        snapshot_datetime = datetime.strptime(f"{date_part}{time_part}", "%Y%m%d%H%M%S")
        assert before_time <= snapshot_datetime <= after_time

    def test_snapshot_with_invalid_version_format(self, temp_workspace):
        """Test error handling for invalid version format."""
        # Setup
        self.setup_test_database(temp_workspace)
        
        # Test various invalid version formats
        invalid_versions = [
            "1.0.0",        # Missing 'v' prefix
            "v1.0",         # Missing patch version
            "v1.0.0.0",     # Too many parts
            "v1.a.0",       # Non-numeric
            "version1",     # Wrong format entirely
            "v1_0_0",       # Wrong separator
        ]
        
        for invalid_version in invalid_versions:
            result = self.run_kuzu_migrate(
                ["snapshot", "--version", invalid_version], 
                temp_workspace,
                check=False
            )
            
            assert result.returncode != 0
            assert "Invalid version format" in result.stderr
            assert "should be in format vX.Y.Z" in result.stderr

    def test_snapshot_without_database(self, temp_workspace):
        """Test error handling when trying to snapshot non-existent database."""
        # Only initialize DDL directory without creating database
        self.run_kuzu_migrate(["init"], temp_workspace)
        
        # Try to create snapshot without database
        result = self.run_kuzu_migrate(["snapshot"], temp_workspace, check=False)
        
        assert result.returncode != 0
        assert "Database not found" in result.stderr
        assert "Run 'kuzu-migrate apply' first" in result.stderr

    def test_snapshot_without_ddl_directory(self, temp_workspace):
        """Test error handling when DDL directory doesn't exist."""
        # Try to create snapshot without initialization
        result = self.run_kuzu_migrate(["snapshot"], temp_workspace, check=False)
        
        assert result.returncode != 0
        assert "DDL directory not found" in result.stderr
        assert "Run 'kuzu-migrate init' first" in result.stderr

    def test_snapshot_shows_restore_instructions(self, temp_workspace):
        """Test that snapshot command shows how to restore."""
        # Setup
        self.setup_test_database(temp_workspace)
        
        # Create snapshot
        version = "v2.0.0"
        result = self.run_kuzu_migrate(["snapshot", "--version", version], temp_workspace)
        
        assert result.returncode == 0
        assert "To restore from this snapshot:" in result.stdout
        assert f"kuzu-migrate rollback --snapshot {version}" in result.stdout

    def test_snapshot_metadata_contains_all_fields(self, temp_workspace):
        """Test that snapshot metadata JSON contains all required fields."""
        # Setup
        self.setup_test_database(temp_workspace)
        
        # Create snapshot
        version = "v1.2.3"
        self.run_kuzu_migrate(["snapshot", "--version", version], temp_workspace)
        
        # Read and verify metadata
        metadata_path = temp_workspace["ddl_dir"] / "snapshots" / version / "snapshot_metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Verify all required fields
        required_fields = [
            "snapshot_name",
            "created_at",
            "database_path",
            "last_migration",
            "kuzu_version"
        ]
        
        for field in required_fields:
            assert field in metadata, f"Missing required field: {field}"
        
        # Verify field values
        assert metadata["snapshot_name"] == version
        assert metadata["database_path"] == str(temp_workspace["db_path"])
        assert metadata["last_migration"] == "001_create_test_table.cypher"
        
        # Verify created_at is valid ISO format
        try:
            datetime.fromisoformat(metadata["created_at"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid created_at timestamp format: {metadata['created_at']}")