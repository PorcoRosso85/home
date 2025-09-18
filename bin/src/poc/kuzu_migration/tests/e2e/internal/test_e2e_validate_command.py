"""E2E tests for kuzu-migrate validate command."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestE2EValidateCommand:
    """Test the kuzu-migrate validate command end-to-end."""

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

    def test_validate_without_ddl_directory(self, temp_dir, kuzu_migrate_path):
        """Test validate command when DDL directory doesn't exist."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Execute validate command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "validate"],
            cwd=temp_dir
        )
        
        # Should fail with helpful error message
        assert result.returncode != 0
        assert "DDL directory not found" in result.stderr
        assert "run 'kuzu-migrate init'" in result.stderr

    def test_validate_with_no_migrations(self, temp_dir, kuzu_migrate_path):
        """Test validate command with empty migrations directory."""
        # Setup - initialize but no migrations
        ddl_dir = os.path.join(temp_dir, "ddl")
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Remove the initial migration template
        initial_migration = os.path.join(ddl_dir, "migrations", "000_initial.cypher")
        if os.path.exists(initial_migration):
            os.remove(initial_migration)
        
        # Execute validate command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "validate"],
            cwd=temp_dir
        )
        
        # Should succeed with message about no migrations
        assert result.returncode == 0
        assert "No migration files found" in result.stdout

    def test_validate_valid_migration_syntax(self, temp_dir, kuzu_migrate_path):
        """Test validate command with syntactically valid migrations."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Create valid migration
        migrations_dir = os.path.join(ddl_dir, "migrations")
        with open(os.path.join(migrations_dir, "001_create_users.cypher"), 'w') as f:
            f.write("""-- Create users table
CREATE NODE TABLE users (
    id INT64 PRIMARY KEY,
    name STRING NOT NULL,
    email STRING UNIQUE
);""")
        
        # Execute validate command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "validate"],
            cwd=temp_dir
        )
        
        # Should succeed and show validation results using EXPLAIN
        assert result.returncode == 0
        assert "✓ 001_create_users.cypher" in result.stdout
        assert "syntax validation passed" in result.stdout or "EXPLAIN" in result.stdout

    def test_validate_invalid_migration_syntax(self, temp_dir, kuzu_migrate_path):
        """Test validate command detects invalid Cypher syntax."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Create migration with syntax error
        migrations_dir = os.path.join(ddl_dir, "migrations")
        with open(os.path.join(migrations_dir, "001_invalid_syntax.cypher"), 'w') as f:
            f.write("""-- Invalid Cypher syntax
CREATE INVALID TABLE users (
    id WRONGTYPE,
    name STRING NOT NULL
    email STRING UNIQUE -- Missing comma
);""")
        
        # Execute validate command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "validate"],
            cwd=temp_dir
        )
        
        # Should fail with syntax error details
        assert result.returncode != 0
        assert "✗ 001_invalid_syntax.cypher" in result.stdout or "✗ 001_invalid_syntax.cypher" in result.stderr
        assert "syntax error" in result.stdout or "syntax error" in result.stderr

    def test_validate_mixed_valid_invalid_migrations(self, temp_dir, kuzu_migrate_path):
        """Test validate command with mixture of valid and invalid migrations."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        migrations_dir = os.path.join(ddl_dir, "migrations")
        
        # Create valid migration
        with open(os.path.join(migrations_dir, "001_valid.cypher"), 'w') as f:
            f.write("CREATE NODE TABLE users (id INT64 PRIMARY KEY);")
        
        # Create invalid migration  
        with open(os.path.join(migrations_dir, "002_invalid.cypher"), 'w') as f:
            f.write("CREATE BROKEN SYNTAX;")
        
        # Execute validate command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "validate"],
            cwd=temp_dir
        )
        
        # Should fail overall but show individual file results
        assert result.returncode != 0
        assert "✓ 001_valid.cypher" in result.stdout or "✓ 001_valid.cypher" in result.stderr
        assert "✗ 002_invalid.cypher" in result.stdout or "✗ 002_invalid.cypher" in result.stderr

    def test_validate_uses_explain_for_syntax_check(self, temp_dir, kuzu_migrate_path):
        """Test that validate command uses EXPLAIN for syntax validation."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Create migration
        migrations_dir = os.path.join(ddl_dir, "migrations")
        with open(os.path.join(migrations_dir, "001_test.cypher"), 'w') as f:
            f.write("CREATE NODE TABLE test_table (id INT64 PRIMARY KEY);")
        
        # Execute validate command with verbose output
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "validate", "--verbose"],
            cwd=temp_dir
        )
        
        # Should show that EXPLAIN is being used
        output = result.stdout + result.stderr
        assert "EXPLAIN" in output or "syntax validation" in output

    def test_validate_requires_kuzu_cli(self, temp_dir, kuzu_migrate_path):
        """Test validate command fails gracefully when kuzu CLI is not available."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Execute validate command with modified PATH that excludes kuzu
        env = os.environ.copy()
        env['PATH'] = '/usr/bin:/bin'  # Minimal PATH without kuzu
        
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "validate"],
            cwd=temp_dir,
            env=env
        )
        
        # Should fail with clear error message
        assert result.returncode != 0
        assert "kuzu" in result.stderr and ("not found" in result.stderr or "command not found" in result.stderr)

    def test_validate_output_format(self, temp_dir, kuzu_migrate_path):
        """Test validate command output is well-formatted."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        init_result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert init_result.returncode == 0
        
        # Execute validate command
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "validate"],
            cwd=temp_dir
        )
        
        # Verify consistent formatting with emoji indicators
        output = result.stdout + result.stderr
        
        # Check for section headers  
        assert "=== Migration Validation ===" in output or "Migration Validation" in output
        
        # Check for consistent status indicators
        assert any(symbol in output for symbol in ["✓", "✗", "ℹ"])