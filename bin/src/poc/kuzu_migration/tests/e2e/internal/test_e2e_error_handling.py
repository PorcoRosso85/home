"""E2E tests for kuzu-migrate error handling and troubleshooting."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestKuzuMigrateErrorHandling:
    """Test suite for kuzu-migrate error handling and failure scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment before each test and clean up after."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp(prefix="kuzu_migrate_error_test_")
        self.ddl_dir = Path(self.temp_dir) / "ddl"
        self.db_path = Path(self.temp_dir) / "test.db"
        self.migrations_dir = self.ddl_dir / "migrations"
        
        # Path to kuzu-migrate script
        self.kuzu_migrate = Path(__file__).parent.parent.parent.parent / "src" / "kuzu-migrate.sh"
        assert self.kuzu_migrate.exists(), f"kuzu-migrate.sh not found at {self.kuzu_migrate}"
        
        yield
        
        # Clean up
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def run_kuzu_migrate(self, *args, check=True):
        """Run kuzu-migrate command with given arguments."""
        cmd = ["bash", str(self.kuzu_migrate), "--ddl", str(self.ddl_dir), "--db", str(self.db_path)] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, output=result.stdout, stderr=result.stderr
            )
        
        return result
    
    def create_migration_file(self, filename: str, content: str):
        """Create a migration file in the migrations directory."""
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        migration_path = self.migrations_dir / filename
        migration_path.write_text(content)
        return migration_path
    
    def run_kuzu_query(self, query: str):
        """Run a Cypher query against the test database."""
        cmd = ["kuzu", str(self.db_path)]
        result = subprocess.run(
            cmd, 
            input=query, 
            capture_output=True, 
            text=True, 
            check=False
        )
        return result
    
    def test_invalid_cypher_syntax_error(self):
        """Test error messages for invalid Cypher syntax."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Create migration with invalid Cypher syntax
        invalid_migrations = [
            # Missing closing parenthesis
            ("001_missing_parenthesis.cypher", """
CREATE NODE TABLE Person (
    id INT64 PRIMARY KEY,
    name STRING
    -- Missing closing parenthesis
;
"""),
            # Invalid property type
            ("002_invalid_type.cypher", """
CREATE NODE TABLE Product (
    id INT64 PRIMARY KEY,
    name INVALID_TYPE NOT NULL
);
"""),
            # Syntax error in CREATE statement
            ("003_syntax_error.cypher", """
CREATE NODE TABLE
    id INT64 PRIMARY KEY
);
"""),
            # Missing semicolon
            ("004_missing_semicolon.cypher", """
CREATE NODE TABLE Test1 (
    id INT64 PRIMARY KEY
)

CREATE NODE TABLE Test2 (
    id INT64 PRIMARY KEY
);
"""),
        ]
        
        for filename, content in invalid_migrations:
            # Clear migrations directory
            for f in self.migrations_dir.glob("*.cypher"):
                f.unlink()
            
            # Create invalid migration
            self.create_migration_file(filename, content)
            
            # Apply migration - should fail
            result = self.run_kuzu_migrate("apply", check=False)
            assert result.returncode != 0
            
            # Check error message contains helpful information
            assert "Failed to apply" in result.stdout
            assert filename in result.stdout
            assert "Error:" in result.stdout
            
            # Error message should be descriptive
            error_output = result.stdout + result.stderr
            # Should contain some indication of the syntax error
            assert any(keyword in error_output.lower() for keyword in 
                      ["syntax", "parser", "invalid", "error", "failed"])
    
    def test_missing_database_error(self):
        """Test error messages when database path is invalid or missing."""
        # Don't initialize database, use non-existent path
        non_existent_db = Path(self.temp_dir) / "non_existent" / "database.db"
        
        # Try to run status command on missing database
        cmd = ["bash", str(self.kuzu_migrate), "--ddl", str(self.ddl_dir), 
               "--db", str(non_existent_db), "status"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        # Should fail with appropriate error
        assert result.returncode != 0
        error_output = result.stdout + result.stderr
        
        # Check for helpful error message
        assert any(keyword in error_output.lower() for keyword in 
                  ["database", "not found", "does not exist", "error", "failed"])
    
    def test_troubleshooting_steps_in_errors(self):
        """Test that error messages include troubleshooting steps."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Create a migration that will fail
        self.create_migration_file("001_failing_migration.cypher", """
CREATE NODE TABLE FailingTable (
    id INT64 PRIMARY KEY,
    name STRING
    -- Syntax error: missing closing parenthesis
;
""")
        
        # Apply migration - should fail
        result = self.run_kuzu_migrate("apply", check=False)
        assert result.returncode != 0
        
        # Check for troubleshooting guidance
        error_output = result.stdout + result.stderr
        
        # Should include guidance on what to do next
        assert any(phrase in error_output for phrase in [
            "Fix the failing migration",
            "run 'kuzu-migrate apply' again",
            "Migration process halted due to failure"
        ])
    
    def test_failed_migrations_recorded_in_history(self):
        """Test that failed migrations are properly recorded in _migration_history."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Create a valid migration first
        self.create_migration_file("001_valid_migration.cypher", """
CREATE NODE TABLE ValidTable (
    id INT64 PRIMARY KEY,
    name STRING
);
""")
        
        # Create a failing migration
        self.create_migration_file("002_failing_migration.cypher", """
CREATE NODE TABLE FailingTable (
    id INT64 PRIMARY KEY,
    invalid syntax here
);
""")
        
        # Apply migrations - should fail on second
        result = self.run_kuzu_migrate("apply", check=False)
        assert result.returncode != 0
        
        # Check that the failed migration was recorded
        history_query = """
MATCH (m:_migration_history)
WHERE m.migration_name = '002_failing_migration.cypher'
RETURN m.migration_name, m.success, m.error_message;
"""
        query_result = self.run_kuzu_query(history_query)
        assert query_result.returncode == 0
        
        output = query_result.stdout
        assert "002_failing_migration.cypher" in output
        assert "false" in output  # success = false
        
        # The error_message should be recorded
        lines = output.strip().split('\n')
        for line in lines:
            if "002_failing_migration.cypher" in line and "|" in line:
                parts = line.split("|")
                assert len(parts) >= 3
                error_msg = parts[2].strip()
                assert error_msg != ""  # Error message should not be empty
                assert error_msg != "''"  # Error message should not be empty string
                break
    
    def test_multiple_failures_stop_execution(self):
        """Test that migration process stops after first failure."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Create multiple migrations, second one fails
        migrations = [
            ("001_valid_migration.cypher", """
CREATE NODE TABLE FirstTable (
    id INT64 PRIMARY KEY
);
"""),
            ("002_failing_migration.cypher", """
CREATE NODE TABLE SecondTable (
    INVALID SYNTAX
);
"""),
            ("003_should_not_run.cypher", """
CREATE NODE TABLE ThirdTable (
    id INT64 PRIMARY KEY
);
"""),
        ]
        
        for filename, content in migrations:
            self.create_migration_file(filename, content)
        
        # Apply migrations
        result = self.run_kuzu_migrate("apply", check=False)
        assert result.returncode != 0
        
        # Check output
        assert "001_valid_migration.cypher" in result.stdout
        assert "Applied successfully" in result.stdout
        assert "002_failing_migration.cypher" in result.stdout
        assert "Failed to apply" in result.stdout
        
        # Third migration should not be mentioned
        assert "003_should_not_run.cypher" not in result.stdout
        
        # Verify first table was created
        query_result = self.run_kuzu_query("CALL TABLE_INFO('FirstTable') RETURN *;")
        assert query_result.returncode == 0
        
        # Verify third table was NOT created
        query_result = self.run_kuzu_query("CALL TABLE_INFO('ThirdTable') RETURN *;")
        assert query_result.returncode != 0
    
    def test_error_recovery_after_fix(self):
        """Test that migrations can continue after fixing a failed migration."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Create a failing migration
        failing_content = """
CREATE NODE TABLE TestTable (
    id INT64 PRIMARY KEY,
    name INVALID_TYPE
);
"""
        self.create_migration_file("001_failing_migration.cypher", failing_content)
        
        # First attempt - should fail
        result = self.run_kuzu_migrate("apply", check=False)
        assert result.returncode != 0
        assert "Failed to apply" in result.stdout
        
        # Fix the migration
        fixed_content = """
CREATE NODE TABLE TestTable (
    id INT64 PRIMARY KEY,
    name STRING
);
"""
        self.create_migration_file("001_failing_migration.cypher", fixed_content)
        
        # Second attempt - should succeed
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        # Note: The current implementation might skip this as already attempted
        # or it might retry. Either behavior is acceptable as long as it's consistent.
        
        # Add a new migration to verify system is working
        self.create_migration_file("002_new_migration.cypher", """
CREATE NODE TABLE AnotherTable (
    id INT64 PRIMARY KEY
);
""")
        
        # Apply new migration
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        
        # Verify the new table was created
        query_result = self.run_kuzu_query("CALL TABLE_INFO('AnotherTable') RETURN *;")
        assert query_result.returncode == 0
    
    def test_detailed_error_messages_for_common_mistakes(self):
        """Test that common migration mistakes produce helpful error messages."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Test duplicate table creation
        self.create_migration_file("001_create_table.cypher", """
CREATE NODE TABLE Users (
    id INT64 PRIMARY KEY,
    name STRING
);
""")
        self.create_migration_file("002_duplicate_table.cypher", """
CREATE NODE TABLE Users (
    id INT64 PRIMARY KEY,
    email STRING
);
""")
        
        # Apply first migration
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        
        # Apply second migration - should fail with duplicate table error
        result = self.run_kuzu_migrate("apply", check=False)
        assert result.returncode != 0
        
        error_output = result.stdout + result.stderr
        # Should indicate table already exists
        assert any(keyword in error_output.lower() for keyword in 
                  ["already exists", "duplicate", "users"])
    
    def test_permission_error_handling(self):
        """Test error handling when database directory has permission issues."""
        # This test might be skipped on some systems where we can't change permissions
        import stat
        
        # Initialize normally first
        self.run_kuzu_migrate("init")
        
        # Create a simple migration
        self.create_migration_file("001_test.cypher", """
CREATE NODE TABLE TestTable (
    id INT64 PRIMARY KEY
);
""")
        
        # Try to make database directory read-only
        try:
            os.chmod(self.temp_dir, stat.S_IRUSR | stat.S_IXUSR)
            
            # Try to apply migration - should fail due to permissions
            result = self.run_kuzu_migrate("apply", check=False)
            assert result.returncode != 0
            
            error_output = result.stdout + result.stderr
            # Should mention permission or access issue
            assert any(keyword in error_output.lower() for keyword in 
                      ["permission", "access", "denied", "error"])
            
        finally:
            # Restore permissions for cleanup
            os.chmod(self.temp_dir, stat.S_IRWXU)
    
    def test_status_command_shows_failed_migrations(self):
        """Test that status command properly displays failed migrations."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Create and apply a valid migration
        self.create_migration_file("001_valid.cypher", """
CREATE NODE TABLE ValidTable (
    id INT64 PRIMARY KEY
);
""")
        self.run_kuzu_migrate("apply")
        
        # Create and attempt to apply a failing migration
        self.create_migration_file("002_failing.cypher", """
CREATE NODE TABLE FailTable (
    SYNTAX ERROR
);
""")
        self.run_kuzu_migrate("apply", check=False)
        
        # Run status command
        result = self.run_kuzu_migrate("status")
        assert result.returncode == 0
        
        # Check output contains failed migrations section
        assert "Failed migrations:" in result.stdout
        assert "002_failing.cypher" in result.stdout
        assert "Error:" in result.stdout
        
        # Should also show successful migrations
        assert "Applied migrations:" in result.stdout
        assert "001_valid.cypher" in result.stdout