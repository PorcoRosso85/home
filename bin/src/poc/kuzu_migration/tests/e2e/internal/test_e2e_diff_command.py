"""E2E tests for kuzu-migrate diff command."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestE2EDiffCommand:
    """Test the kuzu-migrate diff command end-to-end."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test isolation."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def kuzu_migrate_path(self):
        """Path to the kuzu-migrate CLI script."""
        test_dir = Path(__file__).parent
        project_root = test_dir.parent.parent.parent
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

    def create_test_database(self, db_path, schema_content=None):
        """Create a test database with optional schema."""
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        
        # Create minimal database structure if kuzu is available
        if subprocess.run(["which", "kuzu"], capture_output=True).returncode == 0:
            if schema_content:
                try:
                    subprocess.run(
                        f'echo "{schema_content}" | kuzu "{db_path}"',
                        shell=True,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                except subprocess.CalledProcessError:
                    pass  # Ignore errors for test setup

    def test_diff_missing_kuzu_cli(self, temp_dir, kuzu_migrate_path):
        """Test diff command when kuzu CLI is not available."""
        # Setup
        db_path = os.path.join(temp_dir, "source.db")
        target_path = os.path.join(temp_dir, "target.db")
        
        # Create empty directories
        os.makedirs(db_path)
        os.makedirs(target_path)
        
        # Create environment without kuzu
        env = os.environ.copy()
        env['PATH'] = '/usr/bin:/bin'  # Minimal PATH without kuzu
        
        # Execute diff command
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff", "--target", target_path],
            cwd=temp_dir,
            env=env
        )
        
        # Assert command failed with proper error
        assert result.returncode != 0
        assert "command not found: kuzu" in result.stderr
        assert "check PATH" in result.stderr

    def test_diff_missing_target_option(self, temp_dir, kuzu_migrate_path):
        """Test diff command without --target option."""
        # Setup
        db_path = os.path.join(temp_dir, "source.db")
        os.makedirs(db_path)
        
        # Execute diff command without --target
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff"],
            cwd=temp_dir
        )
        
        # Assert command failed with proper error
        assert result.returncode != 0
        assert "Missing --target option for diff command" in result.stderr
        assert "specify target database path" in result.stderr

    def test_diff_source_database_not_found(self, temp_dir, kuzu_migrate_path):
        """Test diff command when source database doesn't exist."""
        # Setup
        db_path = os.path.join(temp_dir, "nonexistent.db")
        target_path = os.path.join(temp_dir, "target.db")
        os.makedirs(target_path)
        
        # Execute diff command
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff", "--target", target_path],
            cwd=temp_dir
        )
        
        # Assert command failed with proper error
        assert result.returncode != 0
        assert "Source database not found" in result.stderr
        assert db_path in result.stderr
        assert "check database path" in result.stderr

    def test_diff_target_database_not_found(self, temp_dir, kuzu_migrate_path):
        """Test diff command when target database doesn't exist."""
        # Setup
        db_path = os.path.join(temp_dir, "source.db")
        target_path = os.path.join(temp_dir, "nonexistent.db")
        os.makedirs(db_path)
        
        # Execute diff command
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff", "--target", target_path],
            cwd=temp_dir
        )
        
        # Assert command failed with proper error
        assert result.returncode != 0
        assert "Target database not found" in result.stderr
        assert target_path in result.stderr
        assert "check --target path" in result.stderr

    def test_diff_invalid_target_option_format(self, temp_dir, kuzu_migrate_path):
        """Test diff command with malformed --target option."""
        # Setup
        db_path = os.path.join(temp_dir, "source.db")
        os.makedirs(db_path)
        
        # Execute diff command with invalid option format
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff", "--target"],
            cwd=temp_dir
        )
        
        # Assert command failed with proper error
        assert result.returncode != 0
        # Should fail because --target has no value

    @pytest.mark.skipif(subprocess.run(["which", "kuzu"], capture_output=True).returncode != 0, 
                       reason="kuzu CLI not available")
    def test_diff_identical_databases(self, temp_dir, kuzu_migrate_path):
        """Test diff command comparing identical databases."""
        # Setup
        db_path = os.path.join(temp_dir, "source.db")
        target_path = os.path.join(temp_dir, "target.db")
        
        # Create identical databases
        schema = "CREATE NODE TABLE User(id INT64 PRIMARY KEY, name STRING);"
        self.create_test_database(db_path, schema)
        self.create_test_database(target_path, schema)
        
        # Execute diff command
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff", "--target", target_path],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        assert "=== Database Schema Comparison ===" in result.stdout
        assert f"Source: {db_path}" in result.stdout
        assert f"Target: {target_path}" in result.stdout
        assert "Schemas are identical" in result.stdout

    @pytest.mark.skipif(subprocess.run(["which", "kuzu"], capture_output=True).returncode != 0,
                       reason="kuzu CLI not available")
    def test_diff_different_databases(self, temp_dir, kuzu_migrate_path):
        """Test diff command comparing different databases."""
        # Setup
        db_path = os.path.join(temp_dir, "source.db")
        target_path = os.path.join(temp_dir, "target.db")
        
        # Create different databases
        source_schema = "CREATE NODE TABLE User(id INT64 PRIMARY KEY, name STRING);"
        target_schema = "CREATE NODE TABLE User(id INT64 PRIMARY KEY, name STRING, email STRING);"
        self.create_test_database(db_path, source_schema)
        self.create_test_database(target_path, target_schema)
        
        # Execute diff command
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff", "--target", target_path],
            cwd=temp_dir
        )
        
        # Assert command succeeded but found differences
        assert result.returncode == 0
        assert "=== Database Schema Comparison ===" in result.stdout
        assert "Schema Analysis:" in result.stdout
        assert "Source checksum:" in result.stdout
        assert "Target checksum:" in result.stdout
        assert "Schema Differences Found:" in result.stdout

    @pytest.mark.skipif(subprocess.run(["which", "kuzu"], capture_output=True).returncode != 0,
                       reason="kuzu CLI not available")
    def test_diff_shows_detailed_diff(self, temp_dir, kuzu_migrate_path):
        """Test diff command shows detailed differences when diff command is available."""
        # Setup
        db_path = os.path.join(temp_dir, "source.db")
        target_path = os.path.join(temp_dir, "target.db")
        
        # Create different databases
        source_schema = "CREATE NODE TABLE User(id INT64 PRIMARY KEY);"
        target_schema = "CREATE NODE TABLE Person(id INT64 PRIMARY KEY);"
        self.create_test_database(db_path, source_schema)
        self.create_test_database(target_path, target_schema)
        
        # Execute diff command
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff", "--target", target_path],
            cwd=temp_dir
        )
        
        # Assert command succeeded and shows diff
        assert result.returncode == 0
        
        if subprocess.run(["which", "diff"], capture_output=True).returncode == 0:
            assert "Detailed Schema Diff" in result.stdout
        else:
            assert "diff command not available" in result.stdout
            assert "showing file statistics" in result.stdout

    @pytest.mark.skipif(subprocess.run(["which", "kuzu"], capture_output=True).returncode != 0,
                       reason="kuzu CLI not available")
    def test_diff_database_connection_failure(self, temp_dir, kuzu_migrate_path):
        """Test diff command when database connection fails."""
        # Setup
        db_path = os.path.join(temp_dir, "source.db")
        target_path = os.path.join(temp_dir, "target.db")
        
        # Create directories but with corrupted/empty databases
        os.makedirs(db_path)
        os.makedirs(target_path)
        
        # Create a file that will cause kuzu to fail
        with open(os.path.join(db_path, "corrupted"), 'w') as f:
            f.write("not a valid database")
        
        # Execute diff command
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff", "--target", target_path],
            cwd=temp_dir
        )
        
        # Assert command failed with connection error
        assert result.returncode != 0
        # Should fail during connection test phase

    def test_diff_output_format_consistency(self, temp_dir, kuzu_migrate_path):
        """Test that diff command output is well-formatted and consistent."""
        # Setup with non-existent databases to test error formatting
        db_path = os.path.join(temp_dir, "source.db")
        target_path = os.path.join(temp_dir, "target.db")
        
        # Execute diff command (will fail)
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff", "--target", target_path],
            cwd=temp_dir
        )
        
        # Verify error output is well-formatted
        assert result.returncode != 0
        output = result.stderr
        
        # Check for consistent error formatting
        assert any(phrase in output for phrase in ["not found", "check", "error"])

    def test_diff_with_environment_variables(self, temp_dir, kuzu_migrate_path):
        """Test diff command using environment variables for database path."""
        # Setup
        db_path = os.path.join(temp_dir, "env_source.db")
        target_path = os.path.join(temp_dir, "target.db")
        os.makedirs(target_path)
        
        # Set environment variable
        env = os.environ.copy()
        env['KUZU_DB_PATH'] = db_path
        
        # Execute diff without explicit --db but with --target
        result = self.run_command(
            [kuzu_migrate_path, "diff", "--target", target_path],
            cwd=temp_dir,
            env=env
        )
        
        # Assert command processes the environment variable
        assert result.returncode != 0  # Will fail because source doesn't exist
        assert db_path in result.stderr  # Should use the env var path

    def test_diff_help_and_usage(self, temp_dir, kuzu_migrate_path):
        """Test diff command shows helpful usage information."""
        # Test with unknown option
        result = self.run_command(
            [kuzu_migrate_path, "diff", "--unknown-option"],
            cwd=temp_dir
        )
        
        # Assert helpful error message
        assert result.returncode != 0
        assert "Unknown diff option" in result.stderr
        assert "see --help" in result.stderr

    @pytest.mark.skipif(subprocess.run(["which", "kuzu"], capture_output=True).returncode != 0,
                       reason="kuzu CLI not available")
    def test_diff_temporary_files_cleanup_info(self, temp_dir, kuzu_migrate_path):
        """Test diff command provides information about temporary files."""
        # Setup
        db_path = os.path.join(temp_dir, "source.db")
        target_path = os.path.join(temp_dir, "target.db")
        
        # Create minimal databases
        self.create_test_database(db_path, "CREATE NODE TABLE Test(id INT64 PRIMARY KEY);")
        self.create_test_database(target_path, "CREATE NODE TABLE Test(id INT64 PRIMARY KEY);")
        
        # Execute diff command
        result = self.run_command(
            [kuzu_migrate_path, "--db", db_path, "diff", "--target", target_path],
            cwd=temp_dir
        )
        
        # Assert command succeeded and shows file location info
        assert result.returncode == 0
        assert "Schema File Locations" in result.stdout
        assert "Temporary schema exports saved at:" in result.stdout
        assert "Use 'cat' or your preferred editor" in result.stdout
        assert "Clean up temp files with:" in result.stdout