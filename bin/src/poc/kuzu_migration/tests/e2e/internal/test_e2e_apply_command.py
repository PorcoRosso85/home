"""E2E tests for kuzu-migrate apply command."""

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pytest


class TestKuzuMigrateApply:
    """Test suite for kuzu-migrate apply command."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment before each test and clean up after."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp(prefix="kuzu_migrate_test_")
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
    
    def test_apply_single_migration(self):
        """Test applying a single migration file."""
        # Initialize DDL directory
        result = self.run_kuzu_migrate("init")
        assert result.returncode == 0
        assert self.migrations_dir.exists()
        
        # Create a simple migration
        migration_content = """
-- Test migration: Create Person table
CREATE NODE TABLE Person (
    id INT64 PRIMARY KEY,
    name STRING NOT NULL,
    age INT32,
    created_at TIMESTAMP DEFAULT now()
);
"""
        self.create_migration_file("001_create_person_table.cypher", migration_content)
        
        # Apply migration
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        assert "Applied successfully" in result.stdout
        assert "001_create_person_table.cypher" in result.stdout
        
        # Verify table was created
        query_result = self.run_kuzu_query("CALL TABLE_INFO('Person') RETURN *;")
        assert query_result.returncode == 0
        assert "Person" in query_result.stdout
    
    def test_apply_multiple_migrations_in_order(self):
        """Test applying multiple migrations in correct order."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Create multiple migrations
        migrations = [
            ("001_create_person_table.cypher", """
CREATE NODE TABLE Person (
    id INT64 PRIMARY KEY,
    name STRING NOT NULL
);
"""),
            ("002_create_city_table.cypher", """
CREATE NODE TABLE City (
    id INT64 PRIMARY KEY,
    name STRING NOT NULL,
    population INT64
);
"""),
            ("003_create_lives_in_rel.cypher", """
CREATE REL TABLE LivesIn (
    FROM Person TO City,
    since DATE
);
""")
        ]
        
        for filename, content in migrations:
            self.create_migration_file(filename, content)
        
        # Apply migrations
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        
        # Verify all migrations were applied
        for filename, _ in migrations:
            assert filename in result.stdout
            assert "Applied successfully" in result.stdout
        
        # Verify tables were created
        for table_name in ["Person", "City", "LivesIn"]:
            query_result = self.run_kuzu_query(f"CALL TABLE_INFO('{table_name}') RETURN *;")
            assert query_result.returncode == 0
    
    def test_migration_history_tracking(self):
        """Test that migration history is properly tracked in _migration_history table."""
        # Initialize and create migration
        self.run_kuzu_migrate("init")
        migration_name = "001_create_test_table.cypher"
        self.create_migration_file(migration_name, """
CREATE NODE TABLE TestTable (
    id INT64 PRIMARY KEY,
    value STRING
);
""")
        
        # Apply migration
        self.run_kuzu_migrate("apply")
        
        # Check migration history table exists
        query_result = self.run_kuzu_query("CALL TABLE_INFO('_migration_history') RETURN *;")
        assert query_result.returncode == 0
        assert "_migration_history" in query_result.stdout
        
        # Check migration was recorded
        history_query = """
MATCH (m:_migration_history)
WHERE m.migration_name = '001_create_test_table.cypher'
RETURN m.migration_name, m.checksum, m.execution_time_ms, m.success;
"""
        query_result = self.run_kuzu_query(history_query)
        assert query_result.returncode == 0
        assert "001_create_test_table.cypher" in query_result.stdout
        assert "true" in query_result.stdout  # success = true
        
        # Verify checksum was recorded
        lines = query_result.stdout.strip().split('\n')
        for line in lines:
            if "001_create_test_table.cypher" in line and "|" in line:
                parts = line.split("|")
                assert len(parts) >= 4
                checksum = parts[1].strip()
                assert len(checksum) == 64  # SHA256 produces 64 character hex string
                break
    
    def test_skip_already_applied_migrations(self):
        """Test that already applied migrations are skipped on subsequent runs."""
        # Initialize and create migration
        self.run_kuzu_migrate("init")
        migration_content = """
CREATE NODE TABLE SkipTest (
    id INT64 PRIMARY KEY,
    name STRING
);
"""
        self.create_migration_file("001_skip_test.cypher", migration_content)
        
        # First apply
        result1 = self.run_kuzu_migrate("apply")
        assert result1.returncode == 0
        assert "Applied successfully" in result1.stdout
        assert "001_skip_test.cypher" in result1.stdout
        
        # Second apply - should skip
        result2 = self.run_kuzu_migrate("apply")
        assert result2.returncode == 0
        assert "Skipping already applied migration: 001_skip_test.cypher" in result2.stdout
        assert "Database is already up to date!" in result2.stdout
        
        # Add another migration
        self.create_migration_file("002_new_migration.cypher", """
CREATE NODE TABLE NewTable (
    id INT64 PRIMARY KEY
);
""")
        
        # Third apply - should skip first, apply second
        result3 = self.run_kuzu_migrate("apply")
        assert result3.returncode == 0
        assert "Skipping already applied migration: 001_skip_test.cypher" in result3.stdout
        assert "Applying migration: 002_new_migration.cypher" in result3.stdout
        assert "Applied successfully" in result3.stdout
    
    def test_failed_migration_handling(self):
        """Test handling of failed migrations with proper error recording."""
        # Initialize and create migrations
        self.run_kuzu_migrate("init")
        
        # First migration - valid
        self.create_migration_file("001_valid_migration.cypher", """
CREATE NODE TABLE ValidTable (
    id INT64 PRIMARY KEY,
    name STRING
);
""")
        
        # Second migration - invalid syntax
        self.create_migration_file("002_invalid_migration.cypher", """
CREATE NODE TABLE InvalidTable (
    id INT64 PRIMARY KEY,
    name STRING
    -- Missing closing parenthesis
;
""")
        
        # Third migration - should not be applied due to failure
        self.create_migration_file("003_should_not_apply.cypher", """
CREATE NODE TABLE ShouldNotExist (
    id INT64 PRIMARY KEY
);
""")
        
        # Apply migrations - should fail on second
        result = self.run_kuzu_migrate("apply", check=False)
        assert result.returncode != 0
        assert "001_valid_migration.cypher" in result.stdout
        assert "Applied successfully" in result.stdout
        assert "002_invalid_migration.cypher" in result.stdout
        assert "Failed to apply" in result.stdout
        assert "Migration process halted due to failure" in result.stdout
        
        # Verify first migration was applied
        query_result = self.run_kuzu_query("CALL TABLE_INFO('ValidTable') RETURN *;")
        assert query_result.returncode == 0
        
        # Verify third migration was NOT applied
        query_result = self.run_kuzu_query("CALL TABLE_INFO('ShouldNotExist') RETURN *;")
        assert query_result.returncode != 0
        
        # Check failed migration was recorded in history
        history_query = """
MATCH (m:_migration_history)
WHERE m.migration_name = '002_invalid_migration.cypher'
RETURN m.migration_name, m.success, m.error_message;
"""
        query_result = self.run_kuzu_query(history_query)
        assert query_result.returncode == 0
        assert "002_invalid_migration.cypher" in query_result.stdout
        assert "false" in query_result.stdout  # success = false
        
        # Run status to see failed migration
        status_result = self.run_kuzu_migrate("status")
        assert status_result.returncode == 0
        assert "Failed migrations:" in status_result.stdout
        assert "002_invalid_migration.cypher" in status_result.stdout
    
    def test_empty_migrations_directory(self):
        """Test behavior when migrations directory is empty."""
        # Initialize DDL directory
        self.run_kuzu_migrate("init")
        
        # Remove the default initial migration
        initial_migration = self.migrations_dir / "000_initial.cypher"
        if initial_migration.exists():
            initial_migration.unlink()
        
        # Apply with empty migrations directory
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        assert "No migration files found" in result.stdout
    
    def test_migration_with_comments_and_multiline(self):
        """Test migration with various SQL features like comments and multiline statements."""
        self.run_kuzu_migrate("init")
        
        complex_migration = """
-- This is a complex migration with various features
-- Testing comment handling

/* Multi-line comment
   spanning multiple lines
   should also work */

CREATE NODE TABLE Product (
    id INT64 PRIMARY KEY,
    name STRING NOT NULL,
    description STRING,
    price DOUBLE,
    -- Inline comment
    in_stock BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now()
);

-- Another single line comment

CREATE NODE TABLE Category (
    id INT64 PRIMARY KEY,
    name STRING NOT NULL,
    parent_id INT64
);

/* Create relationship between products and categories */
CREATE REL TABLE BelongsTo (
    FROM Product TO Category,
    primary BOOLEAN DEFAULT false
);
"""
        self.create_migration_file("001_complex_migration.cypher", complex_migration)
        
        # Apply migration
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        assert "Applied successfully" in result.stdout
        
        # Verify all tables were created
        for table_name in ["Product", "Category", "BelongsTo"]:
            query_result = self.run_kuzu_query(f"CALL TABLE_INFO('{table_name}') RETURN *;")
            assert query_result.returncode == 0
    
    def test_migration_execution_time_tracking(self):
        """Test that execution time is properly tracked for migrations."""
        self.run_kuzu_migrate("init")
        
        # Create a migration
        self.create_migration_file("001_timing_test.cypher", """
CREATE NODE TABLE TimingTest (
    id INT64 PRIMARY KEY,
    data STRING
);
""")
        
        # Apply migration
        self.run_kuzu_migrate("apply")
        
        # Check execution time was recorded
        timing_query = """
MATCH (m:_migration_history)
WHERE m.migration_name = '001_timing_test.cypher'
RETURN m.execution_time_ms;
"""
        query_result = self.run_kuzu_query(timing_query)
        assert query_result.returncode == 0
        
        # Extract execution time from output
        lines = query_result.stdout.strip().split('\n')
        for line in lines:
            if line and not line.startswith('-') and 'execution_time_ms' not in line:
                try:
                    exec_time = int(line.strip())
                    assert exec_time >= 0  # Should be non-negative
                    assert exec_time < 10000  # Should complete in less than 10 seconds
                    break
                except ValueError:
                    continue
    
    def test_migration_applied_timestamp(self):
        """Test that applied_at timestamp is properly set."""
        self.run_kuzu_migrate("init")
        
        # Record time before migration
        before_migration = datetime.now()
        
        # Create and apply migration
        self.create_migration_file("001_timestamp_test.cypher", """
CREATE NODE TABLE TimestampTest (
    id INT64 PRIMARY KEY
);
""")
        self.run_kuzu_migrate("apply")
        
        # Record time after migration
        after_migration = datetime.now()
        
        # Check applied_at timestamp
        timestamp_query = """
MATCH (m:_migration_history)
WHERE m.migration_name = '001_timestamp_test.cypher'
RETURN m.applied_at;
"""
        query_result = self.run_kuzu_query(timestamp_query)
        assert query_result.returncode == 0
        
        # The timestamp should be between before and after (with some buffer for processing)
        # Note: This is a basic check - actual timestamp parsing would require more sophisticated handling
        assert "20" in query_result.stdout  # Basic check for year in timestamp