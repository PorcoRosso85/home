"""
E2E tests for kuzu-migrate status command.

Tests the status command functionality including:
- Status output with pending and applied migrations
- Correct formatting of status table
- Status when no migrations exist
- Status after partial migration application
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestStatusCommand:
    """Test suite for kuzu-migrate status command."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.ddl_dir = Path(self.test_dir) / "ddl"
        self.db_path = Path(self.test_dir) / "test.db"
        self.kuzu_migrate = Path(__file__).parent.parent.parent.parent / "src" / "kuzu-migrate.sh"
        
        # Ensure kuzu-migrate.sh is executable
        os.chmod(self.kuzu_migrate, 0o755)
        
    def teardown_method(self):
        """Clean up test environment after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def run_command(self, *args):
        """Run kuzu-migrate command and return result."""
        cmd = [str(self.kuzu_migrate), f"--ddl={self.ddl_dir}", f"--db={self.db_path}"] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result
    
    def create_migration(self, filename, content):
        """Create a migration file in the migrations directory."""
        migrations_dir = self.ddl_dir / "migrations"
        migrations_dir.mkdir(parents=True, exist_ok=True)
        migration_file = migrations_dir / filename
        migration_file.write_text(content)
        return migration_file
    
    @pytest.mark.internal
    def test_status_no_migrations_exist(self):
        """Test status command when no migrations exist."""
        # Initialize DDL directory
        result = self.run_command("init")
        assert result.returncode == 0
        
        # Remove the default initial migration
        initial_migration = self.ddl_dir / "migrations" / "000_initial.cypher"
        if initial_migration.exists():
            initial_migration.unlink()
        
        # Run status command
        result = self.run_command("status")
        assert result.returncode == 0
        
        # Check output
        output = result.stdout
        assert "Migration Status" in output
        assert "Database not found" in output or "No migrations have been applied yet" in output
    
    @pytest.mark.internal
    def test_status_with_pending_migrations(self):
        """Test status output shows pending migrations."""
        # Initialize DDL directory
        result = self.run_command("init")
        assert result.returncode == 0
        
        # Create some migrations
        self.create_migration("001_create_users.cypher", """
-- Create users table
CREATE NODE TABLE User (
    id STRING PRIMARY KEY,
    name STRING NOT NULL,
    email STRING UNIQUE
);
""")
        
        self.create_migration("002_create_posts.cypher", """
-- Create posts table  
CREATE NODE TABLE Post (
    id STRING PRIMARY KEY,
    title STRING NOT NULL,
    content STRING
);
""")
        
        # Run status command
        result = self.run_command("status")
        assert result.returncode == 0
        
        # Check output shows pending migrations
        output = result.stdout
        assert "Migration Status" in output
        assert "Available migrations (not yet applied)" in output or "Pending migrations" in output
        assert "000_initial.cypher" in output
        assert "001_create_users.cypher" in output
        assert "002_create_posts.cypher" in output
    
    @pytest.mark.internal
    def test_status_with_applied_migrations(self):
        """Test status output shows applied migrations."""
        # Skip if kuzu CLI is not available
        if shutil.which("kuzu") is None:
            pytest.skip("KuzuDB CLI not available")
        
        # Initialize DDL directory
        result = self.run_command("init")
        assert result.returncode == 0
        
        # Create a simple migration
        self.create_migration("001_create_users.cypher", """
CREATE NODE TABLE User (
    id STRING PRIMARY KEY,
    name STRING NOT NULL
);
""")
        
        # Apply migrations
        result = self.run_command("apply")
        assert result.returncode == 0
        
        # Run status command
        result = self.run_command("status")
        assert result.returncode == 0
        
        # Check output shows applied migrations
        output = result.stdout
        assert "Migration Status" in output
        assert "Applied migrations" in output
        assert "000_initial.cypher" in output or "001_create_users.cypher" in output
        assert "applied:" in output
        assert "took:" in output
    
    @pytest.mark.internal
    def test_status_formatting(self):
        """Test correct formatting of status table."""
        # Initialize DDL directory
        result = self.run_command("init")
        assert result.returncode == 0
        
        # Run status command
        result = self.run_command("status")
        assert result.returncode == 0
        
        # Check formatting elements
        output = result.stdout
        assert "===" in output  # Header separator
        assert "Migration Status" in output
        
        # Check for consistent formatting symbols
        if "Applied migrations" in output:
            assert "✅" in output or "✓" in output  # Success markers
        
        if "Pending migrations" in output or "Available migrations" in output:
            assert "📄" in output or "📁" in output or "-" in output  # File/pending markers
        
        if "Failed migrations" in output:
            assert "❌" in output or "✗" in output  # Failure markers
    
    @pytest.mark.internal
    def test_status_after_partial_migration(self):
        """Test status after partial migration application."""
        # Skip if kuzu CLI is not available
        if shutil.which("kuzu") is None:
            pytest.skip("KuzuDB CLI not available")
        
        # Initialize DDL directory
        result = self.run_command("init")
        assert result.returncode == 0
        
        # Create migrations - one valid, one invalid
        self.create_migration("001_create_users.cypher", """
CREATE NODE TABLE User (
    id STRING PRIMARY KEY,
    name STRING NOT NULL
);
""")
        
        self.create_migration("002_invalid_syntax.cypher", """
-- This will fail
CREATE TABLE INVALID SYNTAX HERE;
""")
        
        self.create_migration("003_create_posts.cypher", """
CREATE NODE TABLE Post (
    id STRING PRIMARY KEY,
    title STRING NOT NULL
);
""")
        
        # Apply migrations (will fail on 002)
        result = self.run_command("apply")
        # Command should fail due to invalid migration
        assert result.returncode != 0
        
        # Run status command
        result = self.run_command("status")
        assert result.returncode == 0
        
        # Check output shows mixed state
        output = result.stdout
        assert "Migration Status" in output
        
        # Should show applied migrations
        assert "Applied migrations" in output
        assert "000_initial.cypher" in output or "001_create_users.cypher" in output
        
        # Should show failed migration
        assert "Failed migrations" in output or "002_invalid_syntax.cypher" in output
        
        # Should show pending migrations
        assert "Pending migrations" in output or "003_create_posts.cypher" in output
    
    @pytest.mark.internal
    def test_status_shows_current_version(self):
        """Test that status shows the current database version."""
        # Skip if kuzu CLI is not available
        if shutil.which("kuzu") is None:
            pytest.skip("KuzuDB CLI not available")
        
        # Initialize DDL directory
        result = self.run_command("init")
        assert result.returncode == 0
        
        # Create and apply a migration
        self.create_migration("001_create_users.cypher", """
CREATE NODE TABLE User (
    id STRING PRIMARY KEY,
    name STRING NOT NULL
);
""")
        
        # Apply migrations
        result = self.run_command("apply")
        assert result.returncode == 0
        
        # Run status command
        result = self.run_command("status")
        assert result.returncode == 0
        
        # Check output shows current version
        output = result.stdout
        assert "Current database version" in output or "Database version" in output
        assert "001_create_users.cypher" in output or "000_initial.cypher" in output