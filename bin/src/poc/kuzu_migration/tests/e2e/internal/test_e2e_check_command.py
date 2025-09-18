"""E2E tests for kuzu-migrate check command."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestE2ECheckCommand:
    """Test the kuzu-migrate check command end-to-end."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test isolation."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def kuzu_migrate_path(self):
        """Path to the kuzu-migrate CLI script."""
        # Get the path relative to this test file
        test_dir = Path(__file__).parent
        project_root = test_dir.parent.parent.parent  # Navigate up to project root
        return str(project_root / "src" / "kuzu-migrate.sh")

    def run_command(self, args, cwd=None, env=None):
        """Run a command and return the result."""
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env
        )
        return result

    def test_check_without_ddl_directory(self, temp_dir, kuzu_migrate_path):
        """Test check command when DDL directory doesn't exist."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Execute check command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "check"],
            cwd=temp_dir
        )
        
        # Assert command succeeded (check should not fail, just report)
        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        
        # Verify output contains expected sections
        assert "=== Migration System Check ===" in result.stdout
        assert "📁 DDL Directory:" in result.stdout
        assert "✗ Not found:" in result.stdout
        assert "→ run 'kuzu-migrate init' to create" in result.stdout
        
        # Verify environment section
        assert "🔧 Environment:" in result.stdout
        
        # Verify summary
        assert "📊 Summary:" in result.stdout
        assert "⚠ DDL directory not initialized" in result.stdout

    def test_check_with_initialized_ddl(self, temp_dir, kuzu_migrate_path):
        """Test check command with properly initialized DDL directory."""
        # Setup - first initialize
        ddl_dir = os.path.join(temp_dir, "ddl")
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Execute check command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "check"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify DDL directory status
        assert "✓ Exists:" in result.stdout
        assert "✓ Migrations directory: 1 file(s)" in result.stdout  # Should have 000_initial.cypher
        assert "✓ Snapshots directory: 0 snapshot(s)" in result.stdout
        
        # Verify migration files section
        assert "📄 Migration Files:" in result.stdout
        assert "✓ 000_initial.cypher" in result.stdout

    def test_check_environment_information(self, temp_dir, kuzu_migrate_path):
        """Test that check command shows environment information."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        db_path = os.path.join(temp_dir, "test.db")
        
        # Execute check command with custom db path
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "--db", db_path, "check"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify environment section
        assert "🔧 Environment:" in result.stdout
        assert "Database path:" in result.stdout
        assert db_path in result.stdout
        
        # Check for kuzu CLI availability
        if subprocess.run(["which", "kuzu"], capture_output=True).returncode == 0:
            assert "✓ KuzuDB CLI: available" in result.stdout
        else:
            assert "✗ KuzuDB CLI: not found in PATH" in result.stdout
            assert "→ ensure 'kuzu' is installed and in PATH" in result.stdout

    def test_check_with_multiple_migrations(self, temp_dir, kuzu_migrate_path):
        """Test check command when multiple migration files exist."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Initialize
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Add more migration files
        migrations_dir = os.path.join(ddl_dir, "migrations")
        
        # Create properly named migration
        with open(os.path.join(migrations_dir, "001_add_users.cypher"), 'w') as f:
            f.write("-- Add users table\nCREATE NODE TABLE users (id INT64 PRIMARY KEY);")
        
        # Create improperly named migration
        with open(os.path.join(migrations_dir, "bad_naming.cypher"), 'w') as f:
            f.write("-- Badly named migration")
        
        # Execute check command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "check"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify migration count
        assert "✓ Migrations directory: 3 file(s)" in result.stdout
        
        # Verify migration files section
        assert "📄 Migration Files:" in result.stdout
        assert "✓ 000_initial.cypher" in result.stdout
        assert "✓ 001_add_users.cypher" in result.stdout
        assert "⚠ bad_naming.cypher" in result.stdout
        assert "→ use format: NNN_description.cypher" in result.stdout

    def test_check_with_existing_database(self, temp_dir, kuzu_migrate_path):
        """Test check command when database already exists."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        db_path = os.path.join(temp_dir, "test.db")
        
        # Initialize DDL
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Create database by running apply
        apply_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "--db", db_path, "apply"],
            cwd=temp_dir
        )
        # Apply might fail if kuzu is not available, that's ok for this test
        
        # Execute check command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "--db", db_path, "check"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify database status
        if os.path.exists(db_path):
            assert "✓ Database exists" in result.stdout
            
            # If kuzu is available, check connection status
            if subprocess.run(["which", "kuzu"], capture_output=True).returncode == 0:
                if apply_result.returncode == 0:
                    assert "✓ Database connection: OK" in result.stdout
                    assert "✓ Migration tracking: initialized" in result.stdout
        else:
            assert "ℹ Database not created yet" in result.stdout
            assert "→ will be created on first 'apply'" in result.stdout

    def test_check_with_snapshots(self, temp_dir, kuzu_migrate_path):
        """Test check command when snapshots exist."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Initialize
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Create snapshot directories manually
        snapshots_dir = os.path.join(ddl_dir, "snapshots")
        os.makedirs(os.path.join(snapshots_dir, "snapshot_20240101_120000"))
        os.makedirs(os.path.join(snapshots_dir, "v1.0.0"))
        
        # Execute check command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "check"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify snapshot count
        assert "✓ Snapshots directory: 2 snapshot(s)" in result.stdout

    def test_check_partial_initialization(self, temp_dir, kuzu_migrate_path):
        """Test check command when DDL directory is partially initialized."""
        # Setup - create DDL dir but no subdirectories
        ddl_dir = os.path.join(temp_dir, "ddl")
        os.makedirs(ddl_dir)
        
        # Execute check command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "check"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify output shows missing subdirectories
        assert "✓ Exists:" in result.stdout
        assert "✗ Migrations directory: not found" in result.stdout
        assert "→ run 'kuzu-migrate init' to create" in result.stdout
        assert "✗ Snapshots directory: not found" in result.stdout

    def test_check_summary_all_ok(self, temp_dir, kuzu_migrate_path):
        """Test check command summary when everything is properly set up."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Initialize
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Execute check command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "check"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify summary
        assert "📊 Summary:" in result.stdout
        if subprocess.run(["which", "kuzu"], capture_output=True).returncode == 0:
            assert "✅ System ready for migrations" in result.stdout
        else:
            # Without kuzu CLI, there should be a warning
            assert "⚠ KuzuDB CLI not available" in result.stdout
            assert "issue(s) found" in result.stdout

    def test_check_output_format(self, temp_dir, kuzu_migrate_path):
        """Test that check command output is well-formatted and consistent."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Execute check command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "check"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify consistent formatting with emoji indicators
        output = result.stdout
        
        # Check for consistent section headers
        assert "=== Migration System Check ===" in output
        assert "📁 DDL Directory:" in output
        assert "🔧 Environment:" in output
        assert "📊 Summary:" in output
        
        # Check for consistent status indicators
        # Should have at least one ✓ (checkmark), ✗ (cross), or ℹ (info) symbol
        assert any(symbol in output for symbol in ["✓", "✗", "ℹ", "⚠"])
        
        # Check for helpful hints (arrow indicators)
        if "✗" in output:  # If there are any failures
            assert "→" in output  # Should have hints on how to fix

    def test_check_with_environment_variable(self, temp_dir, kuzu_migrate_path):
        """Test check command using environment variables."""
        # Setup
        env_ddl_dir = os.path.join(temp_dir, "env_ddl")
        env_db_path = os.path.join(temp_dir, "env_db", "kuzu.db")
        
        env = os.environ.copy()
        env['KUZU_DDL_DIR'] = env_ddl_dir
        env['KUZU_DB_PATH'] = env_db_path
        
        # Execute check without explicit paths
        result = self.run_command(
            [kuzu_migrate_path, "check"],
            cwd=temp_dir,
            env=env
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify it's checking the environment-specified paths
        assert env_ddl_dir in result.stdout
        assert env_db_path in result.stdout