"""E2E tests for improved error messages with actionable hints in kuzu-migrate."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestKuzuMigrateErrorHints:
    """Test suite for error messages with actionable hints (not just facts)."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment before each test and clean up after."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp(prefix="kuzu_migrate_error_hints_test_")
        self.ddl_dir = Path(self.temp_dir) / "ddl"
        self.db_path = Path(self.temp_dir) / "test.db"
        self.migrations_dir = self.ddl_dir / "migrations"
        
        # Path to kuzu-migrate script
        self.kuzu_migrate = Path(__file__).parent.parent.parent.parent / "src" / "kuzu-migrate.sh"
        assert self.kuzu_migrate.exists(), f"kuzu-migrate.sh not found at {self.kuzu_migrate}"
        
        yield
        
        # Clean up
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def run_kuzu_migrate(self, *args, check=False, omit_ddl=False, omit_db=False):
        """Run kuzu-migrate command with given arguments."""
        cmd = ["bash", str(self.kuzu_migrate)]
        
        # Add --ddl and --db flags unless specifically omitted
        if not omit_ddl:
            cmd.extend(["--ddl", str(self.ddl_dir)])
        if not omit_db:
            cmd.extend(["--db", str(self.db_path)])
        
        cmd.extend(list(args))
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, output=result.stdout, stderr=result.stderr
            )
        
        return result
    
    def test_missing_ddl_directory_hint(self):
        """Test that missing DDL directory error provides '→ run init' hint."""
        # Don't create DDL directory, try to run status
        result = self.run_kuzu_migrate("status", check=False)
        
        assert result.returncode != 0
        error_output = result.stdout + result.stderr
        
        # Check for error message with actionable hint
        assert "DDL directory not found" in error_output
        assert "→ run 'init'" in error_output
        
        # Should not have verbose instructions
        assert "Run 'kuzu-migrate init' first" not in error_output  # Old verbose format
    
    def test_missing_kuzu_command_hint(self):
        """Test that missing kuzu command error provides '→ check PATH' hint."""
        # This test is tricky as we need kuzu to not be found
        # We'll mock this by temporarily modifying PATH
        original_path = os.environ.get('PATH', '')
        
        try:
            # Set PATH to empty to ensure kuzu won't be found
            os.environ['PATH'] = '/nonexistent'
            
            # Initialize first
            # We need to restore PATH temporarily for init to work
            os.environ['PATH'] = original_path
            self.run_kuzu_migrate("init")
            
            # Now remove PATH again and try to run status
            os.environ['PATH'] = '/nonexistent'
            result = self.run_kuzu_migrate("status", check=False)
            
            assert result.returncode != 0
            error_output = result.stdout + result.stderr
            
            # Check for error with actionable hint
            assert "command not found: kuzu" in error_output
            assert "→ check PATH" in error_output
            
        finally:
            # Always restore original PATH
            os.environ['PATH'] = original_path
    
    def test_already_applied_migration_hint(self):
        """Test that already applied migration shows appropriate message."""
        # Initialize and apply a migration
        self.run_kuzu_migrate("init")
        
        # Create a simple migration
        migration_content = """
CREATE NODE TABLE TestTable (
    id INT64 PRIMARY KEY,
    name STRING
);
"""
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        migration_file = self.migrations_dir / "001_create_test_table.cypher"
        migration_file.write_text(migration_content)
        
        # Apply the migration
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        
        # Try to apply again - should show already applied
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        
        output = result.stdout
        assert "Skipping already applied migration" in output
        
        # Should indicate database is up to date
        assert "Database is already up to date!" in output
    
    def test_failed_migration_hint(self):
        """Test that failed migration provides '→ fix syntax' hint."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Create migration with syntax error
        invalid_migration = """
CREATE NODE TABLE BrokenTable (
    id INT64 PRIMARY KEY,
    name STRING
    -- Missing closing parenthesis
;
"""
        migration_file = self.migrations_dir / "001_broken_migration.cypher"
        migration_file.write_text(invalid_migration)
        
        # Apply migration - should fail
        result = self.run_kuzu_migrate("apply", check=False)
        assert result.returncode != 0
        
        error_output = result.stdout + result.stderr
        
        # Check for concise actionable hint
        assert "Failed to apply" in error_output
        assert "→ fix migration" in error_output
        
        # Should not have verbose instructions
        assert "Fix the failing migration and run 'kuzu-migrate apply' again" not in error_output
    
    def test_database_not_found_hint(self):
        """Test that database not found error provides appropriate message."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Try to run status without database existing
        result = self.run_kuzu_migrate("status")
        # This should succeed but show informative message
        assert result.returncode == 0
        
        output = result.stdout
        # Should indicate no migrations have been applied
        assert "No migrations have been applied yet" in output
    
    def test_invalid_version_format_hint(self):
        """Test that invalid version format provides '→ use vX.Y.Z' hint."""
        # Initialize and create database
        self.run_kuzu_migrate("init")
        
        # Create a simple migration to establish database
        migration_content = """
CREATE NODE TABLE TestTable (
    id INT64 PRIMARY KEY
);
"""
        migration_file = self.migrations_dir / "001_test.cypher"
        migration_file.write_text(migration_content)
        self.run_kuzu_migrate("apply")
        
        # Try to create snapshot with invalid version
        result = self.run_kuzu_migrate("snapshot", "--version", "1.0.0", check=False)
        assert result.returncode != 0
        
        error_output = result.stdout + result.stderr
        
        # Check for concise format hint
        assert "Invalid version format" in error_output
        assert "→ use vX.Y.Z" in error_output
    
    def test_snapshot_already_exists_hint(self):
        """Test that existing snapshot provides '→ new version' hint."""
        # Initialize and create database
        self.run_kuzu_migrate("init")
        
        # Create a migration
        migration_content = """
CREATE NODE TABLE TestTable (
    id INT64 PRIMARY KEY
);
"""
        migration_file = self.migrations_dir / "001_test.cypher"
        migration_file.write_text(migration_content)
        self.run_kuzu_migrate("apply")
        
        # Create a snapshot
        result = self.run_kuzu_migrate("snapshot", "--version", "v1.0.0")
        assert result.returncode == 0
        
        # Try to create same snapshot again
        result = self.run_kuzu_migrate("snapshot", "--version", "v1.0.0", check=False)
        assert result.returncode != 0
        
        error_output = result.stdout + result.stderr
        
        # Check for concise hint
        assert "Snapshot already exists" in error_output
        assert "→ use different version" in error_output
    
    def test_no_command_specified_hint(self):
        """Test that no command specified provides '→ help' hint."""
        # Run without any command
        result = self.run_kuzu_migrate(check=False)
        assert result.returncode != 0
        
        error_output = result.stdout + result.stderr
        
        # Check for concise hint
        assert "No command specified" in error_output
        assert "→ see --help" in error_output
    
    def test_unknown_command_hint(self):
        """Test that unknown command provides '→ help' hint."""
        # Run with invalid command
        result = self.run_kuzu_migrate("invalid_command", check=False)
        assert result.returncode != 0
        
        error_output = result.stdout + result.stderr
        
        # Check for concise hint
        assert "Unknown command" in error_output
        assert "→ see --help" in error_output
    
    def test_hints_are_concise(self):
        """Test that all error hints follow concise format (1-2 words max)."""
        # Test various error scenarios and verify hint format
        test_cases = [
            # (command_args, expected_error_keyword)
            (["status"], "DDL directory not found"),  # Missing DDL
            (["invalid"], "Unknown command"),  # Invalid command
            ([], "No command specified"),  # No command
        ]
        
        for args, expected_error in test_cases:
            result = self.run_kuzu_migrate(*args, check=False)
            if result.returncode != 0:
                error_output = result.stdout + result.stderr
                
                if expected_error in error_output:
                    # Look for arrow hints
                    import re
                    arrow_hints = re.findall(r'→\s*([^\n]+)', error_output)
                    
                    for hint in arrow_hints:
                        # Hints should be concise (typically 1-4 words, allowing for phrases like "use different version")
                        word_count = len(hint.strip().split())
                        assert word_count <= 4, f"Hint too verbose: '{hint}' has {word_count} words"
                        
                        # Hints should not be full sentences (no periods at the end)
                        assert not hint.strip().endswith('.'), f"Hint should not be a sentence: '{hint}'"
                        
                        # Hints should be actionable (typically start with verb or contain directive)
                        hint_lower = hint.strip().lower()
                        common_hint_patterns = ['run', 'check', 'fix', 'use', 'try', 'see', 
                                              'init', 'apply', 'status', 'help', 'install',
                                              'new', 'different', 'valid']
                        assert any(pattern in hint_lower for pattern in common_hint_patterns), \
                            f"Hint doesn't seem actionable: '{hint}'"