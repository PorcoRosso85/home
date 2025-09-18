"""E2E tests for kuzu-migrate apply --dry-run functionality.

This comprehensive test suite validates the dry-run functionality which allows users
to preview migration effects without actually modifying the database. Key test areas:

1. Output formatting with [DRY-RUN] indicators
2. Database state preservation (no actual changes)  
3. Migration validation without persistence
4. History table remains unmodified
5. Error detection for invalid migrations
6. Integration with existing migration patterns
7. Performance timing display without recording

The dry-run feature uses transaction rollback to validate migrations safely,
ensuring database integrity while providing detailed feedback about what
would happen during a real migration run.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestKuzuMigrateDryRun:
    """Test suite for kuzu-migrate apply --dry-run command."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment before each test and clean up after."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp(prefix="kuzu_migrate_dry_run_test_")
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
    
    def test_dry_run_shows_dry_run_indicators(self):
        """Test that dry-run output shows [DRY-RUN] indicators."""
        # Initialize and create migration
        self.run_kuzu_migrate("init")
        self.create_migration_file("001_create_test_table.cypher", """
CREATE NODE TABLE TestTable (
    id INT64 PRIMARY KEY,
    name STRING NOT NULL
);
""")
        
        # Run with dry-run flag
        result = self.run_kuzu_migrate("apply", "--dry-run")
        assert result.returncode == 0
        
        # Verify dry-run indicators are present
        assert "[DRY-RUN]" in result.stdout
        assert "📄 [DRY-RUN] Would apply migration: 001_create_test_table.cypher" in result.stdout
        assert "✅ [DRY-RUN] Would apply successfully" in result.stdout
        assert "[DRY-RUN] Migration Summary:" in result.stdout
        assert "Run without --dry-run to actually apply these migrations" in result.stdout
    
    def test_dry_run_does_not_modify_database(self):
        """Test that dry-run doesn't actually modify the database."""
        # Initialize and create migration
        self.run_kuzu_migrate("init")
        self.create_migration_file("001_create_person_table.cypher", """
CREATE NODE TABLE Person (
    id INT64 PRIMARY KEY,
    name STRING NOT NULL,
    age INT32
);
""")
        
        # Run dry-run
        result = self.run_kuzu_migrate("apply", "--dry-run")
        assert result.returncode == 0
        assert "[DRY-RUN]" in result.stdout
        
        # Verify table was NOT created in database
        query_result = self.run_kuzu_query("CALL TABLE_INFO('Person') RETURN *;")
        assert query_result.returncode != 0  # Should fail because table doesn't exist
        
        # Verify migration history was NOT updated
        history_query = """
MATCH (m:_migration_history)
WHERE m.migration_name = '001_create_person_table.cypher'
RETURN m.migration_name;
"""
        query_result = self.run_kuzu_query(history_query)
        # Should not find the migration in history
        assert "001_create_person_table.cypher" not in query_result.stdout
    
    def test_dry_run_validates_migrations_but_not_persisted(self):
        """Test that dry-run validates migration syntax but doesn't persist changes."""
        # Initialize and create multiple migrations
        self.run_kuzu_migrate("init")
        
        # Valid migration
        self.create_migration_file("001_create_user_table.cypher", """
CREATE NODE TABLE User (
    id INT64 PRIMARY KEY,
    username STRING NOT NULL
);
""")
        
        # Another valid migration that depends on the first
        self.create_migration_file("002_create_post_table.cypher", """
CREATE NODE TABLE Post (
    id INT64 PRIMARY KEY,
    title STRING NOT NULL,
    author_id INT64
);
CREATE REL TABLE AuthoredBy (FROM Post TO User);
""")
        
        # Run dry-run
        result = self.run_kuzu_migrate("apply", "--dry-run")
        assert result.returncode == 0
        
        # Verify both migrations show as would-be-applied
        assert "📄 [DRY-RUN] Would apply migration: 001_create_user_table.cypher" in result.stdout
        assert "📄 [DRY-RUN] Would apply migration: 002_create_post_table.cypher" in result.stdout
        assert "✅ [DRY-RUN] Would apply successfully" in result.stdout
        
        # Verify tables were NOT created
        for table in ["User", "Post", "AuthoredBy"]:
            query_result = self.run_kuzu_query(f"CALL TABLE_INFO('{table}') RETURN *;")
            assert query_result.returncode != 0
        
        # Verify no migrations recorded in history
        history_query = "MATCH (m:_migration_history) RETURN COUNT(m);"
        query_result = self.run_kuzu_query(history_query)
        # History table might exist but should be empty (or only contain the initial setup record)
        assert "0" in query_result.stdout or query_result.returncode != 0
    
    def test_dry_run_detects_invalid_migrations(self):
        """Test that dry-run detects invalid migration syntax."""
        # Initialize and create migration
        self.run_kuzu_migrate("init")
        
        # Invalid migration - syntax error
        self.create_migration_file("001_invalid_migration.cypher", """
CREATE NODE TABLE InvalidTable (
    id INT64 PRIMARY KEY,
    name STRING NOT NULL
    -- Missing closing parenthesis and semicolon
""")
        
        # Run dry-run
        result = self.run_kuzu_migrate("apply", "--dry-run")
        assert result.returncode != 0  # Should fail due to invalid syntax
        
        # Verify dry-run failure indicators
        assert "📄 [DRY-RUN] Would apply migration: 001_invalid_migration.cypher" in result.stdout
        assert "❌ [DRY-RUN] Would fail to apply" in result.stdout
        assert "Error:" in result.stdout
        
        # Verify database is not modified
        query_result = self.run_kuzu_query("CALL TABLE_INFO('InvalidTable') RETURN *;")
        assert query_result.returncode != 0
        
        # Verify no failed migration recorded in history (since it's dry-run)
        history_query = "MATCH (m:_migration_history) RETURN COUNT(m);"
        query_result = self.run_kuzu_query(history_query)
        assert "0" in query_result.stdout or query_result.returncode != 0
    
    def test_dry_run_with_already_applied_migrations(self):
        """Test dry-run behavior with already applied migrations."""
        # Initialize and create migration
        self.run_kuzu_migrate("init")
        self.create_migration_file("001_create_existing_table.cypher", """
CREATE NODE TABLE ExistingTable (
    id INT64 PRIMARY KEY,
    value STRING
);
""")
        
        # First, apply the migration normally
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        assert "Applied successfully" in result.stdout
        
        # Verify table exists
        query_result = self.run_kuzu_query("CALL TABLE_INFO('ExistingTable') RETURN *;")
        assert query_result.returncode == 0
        
        # Add a new migration
        self.create_migration_file("002_create_new_table.cypher", """
CREATE NODE TABLE NewTable (
    id INT64 PRIMARY KEY,
    data STRING
);
""")
        
        # Run dry-run
        result = self.run_kuzu_migrate("apply", "--dry-run")
        assert result.returncode == 0
        
        # Verify output shows skipped and would-apply
        assert "⏭️  Skipping already applied migration: 001_create_existing_table.cypher" in result.stdout
        assert "📄 [DRY-RUN] Would apply migration: 002_create_new_table.cypher" in result.stdout
        assert "✅ [DRY-RUN] Would apply successfully" in result.stdout
        
        # Verify new table was NOT created
        query_result = self.run_kuzu_query("CALL TABLE_INFO('NewTable') RETURN *;")
        assert query_result.returncode != 0
    
    def test_dry_run_migration_history_not_updated(self):
        """Test that migration history table is not updated during dry-run."""
        # Initialize and create migrations
        self.run_kuzu_migrate("init")
        
        self.create_migration_file("001_first_migration.cypher", """
CREATE NODE TABLE FirstTable (
    id INT64 PRIMARY KEY,
    name STRING
);
""")
        
        self.create_migration_file("002_second_migration.cypher", """
CREATE NODE TABLE SecondTable (
    id INT64 PRIMARY KEY,
    value INT64
);
""")
        
        # Run dry-run
        result = self.run_kuzu_migrate("apply", "--dry-run")
        assert result.returncode == 0
        
        # Verify migrations show as would-be-applied
        assert "📄 [DRY-RUN] Would apply migration: 001_first_migration.cypher" in result.stdout
        assert "📄 [DRY-RUN] Would apply migration: 002_second_migration.cypher" in result.stdout
        
        # Check migration history is empty (except for possible initial setup)
        history_query = """
MATCH (m:_migration_history)
WHERE m.migration_name IN ['001_first_migration.cypher', '002_second_migration.cypher']
RETURN m.migration_name;
"""
        query_result = self.run_kuzu_query(history_query)
        # Should not find either migration in history
        assert "001_first_migration.cypher" not in query_result.stdout
        assert "002_second_migration.cypher" not in query_result.stdout
        
        # Now apply normally and verify history is updated
        result = self.run_kuzu_migrate("apply")
        assert result.returncode == 0
        
        # Check migration history is now populated
        query_result = self.run_kuzu_query(history_query)
        assert query_result.returncode == 0
        assert "001_first_migration.cypher" in query_result.stdout
        assert "002_second_migration.cypher" in query_result.stdout
    
    def test_dry_run_execution_time_display(self):
        """Test that dry-run shows execution time without recording it."""
        # Initialize and create migration
        self.run_kuzu_migrate("init")
        self.create_migration_file("001_timed_migration.cypher", """
CREATE NODE TABLE TimedTable (
    id INT64 PRIMARY KEY,
    timestamp_field TIMESTAMP DEFAULT now()
);
""")
        
        # Run dry-run
        result = self.run_kuzu_migrate("apply", "--dry-run")
        assert result.returncode == 0
        
        # Verify execution time is displayed
        assert "✅ [DRY-RUN] Would apply successfully" in result.stdout
        assert "ms)" in result.stdout  # Should show execution time in milliseconds
        
        # Verify execution time is NOT recorded in database
        timing_query = """
MATCH (m:_migration_history)
WHERE m.migration_name = '001_timed_migration.cypher'
RETURN m.execution_time_ms;
"""
        query_result = self.run_kuzu_query(timing_query)
        # Should not find the migration record
        assert "execution_time_ms" not in query_result.stdout or query_result.returncode != 0
    
    def test_dry_run_follows_existing_patterns(self):
        """Test that dry-run follows the same migration discovery and ordering patterns."""
        # Initialize 
        self.run_kuzu_migrate("init")
        
        # Create migrations in non-alphabetical order to test sorting
        migrations = [
            ("003_third_migration.cypher", "CREATE NODE TABLE ThirdTable(id INT64 PRIMARY KEY);"),
            ("001_first_migration.cypher", "CREATE NODE TABLE FirstTable(id INT64 PRIMARY KEY);"),
            ("002_second_migration.cypher", "CREATE NODE TABLE SecondTable(id INT64 PRIMARY KEY);"),
        ]
        
        for filename, content in migrations:
            self.create_migration_file(filename, content)
        
        # Run dry-run
        result = self.run_kuzu_migrate("apply", "--dry-run")
        assert result.returncode == 0
        
        # Verify migrations are processed in correct order
        output_lines = result.stdout.split('\n')
        migration_order = []
        for line in output_lines:
            if "📄 [DRY-RUN] Would apply migration:" in line:
                migration_name = line.split(": ")[1].strip()
                migration_order.append(migration_name)
        
        expected_order = ["001_first_migration.cypher", "002_second_migration.cypher", "003_third_migration.cypher"]
        assert migration_order == expected_order, f"Expected {expected_order}, got {migration_order}"
        
        # Verify summary shows correct count
        assert "Found 3 migration file(s)" in result.stdout
        assert "[DRY-RUN] Migration Summary:" in result.stdout