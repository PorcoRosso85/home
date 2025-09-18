"""E2E tests for kuzu-migrate init command."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestE2EInitCommand:
    """Test the kuzu-migrate init command end-to-end."""

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

    def test_init_creates_directory_structure(self, temp_dir, kuzu_migrate_path):
        """Test that init command creates the expected directory structure."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Execute
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
        assert "Migration directory initialized successfully!" in result.stdout
        
        # Verify directory structure
        assert os.path.exists(ddl_dir), "DDL directory was not created"
        assert os.path.exists(os.path.join(ddl_dir, "migrations")), "migrations directory was not created"
        assert os.path.exists(os.path.join(ddl_dir, "snapshots")), "snapshots directory was not created"
        
        # Verify output messages
        assert "Created migrations directory" in result.stdout
        assert "Created snapshots directory" in result.stdout

    def test_init_creates_initial_migration_template(self, temp_dir, kuzu_migrate_path):
        """Test that init command creates the initial migration template."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Execute
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify initial migration template exists
        initial_migration = os.path.join(ddl_dir, "migrations", "000_initial.cypher")
        assert os.path.exists(initial_migration), "Initial migration template was not created"
        
        # Verify template content
        with open(initial_migration, 'r') as f:
            content = f.read()
        
        assert "Initial migration template" in content
        assert "CREATE NODE TABLE User" in content  # Example schema
        assert "CREATE REL TABLE Follows" in content  # Example relationship
        
        # Verify output message
        assert "Created initial migration template" in result.stdout

    def test_init_idempotent_behavior(self, temp_dir, kuzu_migrate_path):
        """Test that init command is idempotent when ddl directory already exists."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Run init first time
        result1 = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        assert result1.returncode == 0
        
        # Run init second time
        result2 = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result2.returncode == 0
        
        # Verify idempotent messages
        assert "DDL directory already exists" in result2.stdout
        assert "Migrations directory already exists" in result2.stdout
        assert "Snapshots directory already exists" in result2.stdout
        assert "Initial migration template already exists" in result2.stdout
        
        # Verify directory structure still exists
        assert os.path.exists(ddl_dir)
        assert os.path.exists(os.path.join(ddl_dir, "migrations"))
        assert os.path.exists(os.path.join(ddl_dir, "snapshots"))

    def test_init_preserves_existing_content(self, temp_dir, kuzu_migrate_path):
        """Test that init command preserves existing files when directory exists."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        migrations_dir = os.path.join(ddl_dir, "migrations")
        
        # Create directory with existing migration
        os.makedirs(migrations_dir)
        existing_migration = os.path.join(migrations_dir, "001_existing.cypher")
        with open(existing_migration, 'w') as f:
            f.write("-- Existing migration\nCREATE NODE TABLE Test (id STRING PRIMARY KEY);")
        
        # Execute
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify existing file is preserved
        assert os.path.exists(existing_migration)
        with open(existing_migration, 'r') as f:
            content = f.read()
        assert "Existing migration" in content
        assert "CREATE NODE TABLE Test" in content
        
        # Verify initial template was also created
        initial_migration = os.path.join(migrations_dir, "000_initial.cypher")
        assert os.path.exists(initial_migration)

    def test_init_with_custom_ddl_path(self, temp_dir, kuzu_migrate_path):
        """Test init command with custom DDL directory path."""
        # Setup
        custom_path = os.path.join(temp_dir, "custom", "path", "ddl")
        
        # Execute
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", custom_path, "init"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify directory structure at custom path
        assert os.path.exists(custom_path)
        assert os.path.exists(os.path.join(custom_path, "migrations"))
        assert os.path.exists(os.path.join(custom_path, "snapshots"))
        assert os.path.exists(os.path.join(custom_path, "migrations", "000_initial.cypher"))

    def test_init_with_environment_variable(self, temp_dir, kuzu_migrate_path):
        """Test init command using KUZU_DDL_DIR environment variable."""
        # Setup
        env_ddl_dir = os.path.join(temp_dir, "env_ddl")
        env = os.environ.copy()
        env['KUZU_DDL_DIR'] = env_ddl_dir
        
        # Execute without --ddl flag
        result = self.run_command(
            [kuzu_migrate_path, "init"],
            cwd=temp_dir,
            env=env
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify directory structure at environment-specified path
        assert os.path.exists(env_ddl_dir)
        assert os.path.exists(os.path.join(env_ddl_dir, "migrations"))
        assert os.path.exists(os.path.join(env_ddl_dir, "snapshots"))

    def test_init_output_format(self, temp_dir, kuzu_migrate_path):
        """Test that init command produces well-formatted output."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Execute
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Verify output structure
        output_lines = result.stdout.strip().split('\n')
        
        # Check for expected sections
        assert any("Creating new DDL directory" in line for line in output_lines)
        assert any("Directory structure:" in line for line in output_lines)
        assert any("├── migrations/" in line for line in output_lines)
        assert any("└── snapshots/" in line for line in output_lines)
        assert any("Next steps:" in line for line in output_lines)
        assert any("Ready to start managing your KuzuDB migrations!" in line for line in output_lines)

    def test_init_creates_valid_cypher_template(self, temp_dir, kuzu_migrate_path):
        """Test that the created migration template contains valid Cypher syntax."""
        # Setup
        ddl_dir = os.path.join(temp_dir, "ddl")
        
        # Execute
        result = self.run_command(
            [kuzu_migrate_path, "--ddl", ddl_dir, "init"],
            cwd=temp_dir
        )
        
        # Assert command succeeded
        assert result.returncode == 0
        
        # Read and verify template
        initial_migration = os.path.join(ddl_dir, "migrations", "000_initial.cypher")
        with open(initial_migration, 'r') as f:
            content = f.read()
        
        # Check for proper SQL/Cypher comment syntax
        assert content.startswith("--")
        
        # Check for naming convention documentation
        assert "Naming convention:" in content
        assert "NNN_description.cypher" in content
        
        # Check for example migrations
        assert "001_create_user_nodes.cypher" in content
        assert "002_add_friend_relationships.cypher" in content
        
        # Verify all example code is commented out
        lines = content.split('\n')
        for line in lines:
            if "CREATE" in line and not line.strip().startswith("--"):
                pytest.fail(f"Found uncommented CREATE statement: {line}")