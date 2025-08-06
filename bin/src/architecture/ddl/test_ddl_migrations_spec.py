"""
Tests for DDL migrations application and table creation
Following the testing philosophy: no mocks, test actual behavior
"""
import pytest
import tempfile
import os
from pathlib import Path

# Import from architecture module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from architecture.db import KuzuConnectionManager
import kuzu_py


class TestDDLMigrations:
    """Test DDL migrations can be applied successfully"""

    def setup_method(self):
        """Setup test environment"""
        # Get the migrations directory path
        self.migrations_dir = Path(__file__).parent / "migrations"
        assert self.migrations_dir.exists(), f"Migrations directory not found: {self.migrations_dir}"

    def read_migration_file(self, filename: str) -> str:
        """Read a migration file and return its content"""
        migration_path = self.migrations_dir / filename
        assert migration_path.exists(), f"Migration file not found: {migration_path}"
        
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Filter out comments and empty lines
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                lines.append(line)
        
        # Join lines and split by semicolon to get individual statements
        return ' '.join(lines)

    def test_initial_migration_creates_tables(self):
        """Test that initial migration creates all expected tables"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create database connection
            db_path = Path(tmpdir) / "test_db"
            conn_manager = KuzuConnectionManager(db_path=db_path)
            conn = conn_manager.get_connection()
        
        # Read and execute the initial migration
        migration_content = self.read_migration_file("000_initial.cypher")
        
        # Execute each statement separately
        statements = [s.strip() for s in migration_content.split(';') if s.strip()]
        for statement in statements:
            conn.execute(statement)
        
        # Verify all expected tables were created
        expected_node_tables = [
            "ImplementationEntity",
            "ImplementationURI",
            "VersionState",
            "Responsibility"
        ]
        
        expected_rel_tables = [
            "LOCATES",
            "TRACKS_STATE_OF",
            "CONTAINS_LOCATION",
            "DEPENDS_ON",
            "HAS_RESPONSIBILITY",
            "SIMILAR_TO"
        ]
        
        # Check tables
        result = conn.execute("CALL show_tables() RETURN *")
        tables = []
        while result.has_next():
            row = result.get_next()
            tables.append({
                'name': row[1],  # Table name is in column 1
                'type': row[2]   # Table type (NODE/REL)
            })
        
        # Check node tables
        created_node_tables = [t['name'] for t in tables if t['type'] == 'NODE']
        for table in expected_node_tables:
            assert table in created_node_tables, f"Node table {table} was not created"
        
        # Check relationship tables
        created_rel_tables = [t['name'] for t in tables if t['type'] == 'REL']
        for table in expected_rel_tables:
            assert table in created_rel_tables, f"Relationship table {table} was not created"

    def test_requirement_entity_migration(self):
        """Test that requirement entity migration adds new tables"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create database connection
            db_path = Path(tmpdir) / "test_db"
            conn_manager = KuzuConnectionManager(db_path=db_path)
            conn = conn_manager.get_connection()
        
        # Apply initial migration
        initial_migration = self.read_migration_file("000_initial.cypher")
        statements = [s.strip() for s in initial_migration.split(';') if s.strip()]
        for statement in statements:
            conn.execute(statement)
        
        # Apply requirement entity migration
        req_migration = self.read_migration_file("002_add_requirement_entity.cypher")
        statements = [s.strip() for s in req_migration.split(';') if s.strip()]
        for statement in statements:
            conn.execute(statement)
        
        # Verify tables were created
        result = conn.execute("CALL show_tables() RETURN *")
        tables = []
        while result.has_next():
            row = result.get_next()
            tables.append({
                'name': row[1],
                'type': row[2]
            })
        
        # Verify RequirementEntity table was created
        node_tables = [t['name'] for t in tables if t['type'] == 'NODE']
        assert "RequirementEntity" in node_tables, "RequirementEntity table was not created"
        
        # Verify IMPLEMENTS relationship was created
        rel_tables = [t['name'] for t in tables if t['type'] == 'REL']
        assert "IMPLEMENTS" in rel_tables, "IMPLEMENTS relationship was not created"

    def test_multiple_migrations_in_sequence(self):
        """Test applying multiple migrations in sequence"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create database connection
            db_path = Path(tmpdir) / "test_db"
            conn_manager = KuzuConnectionManager(db_path=db_path)
            conn = conn_manager.get_connection()
        
        # Apply migrations in order
        migration_files = [
            "000_initial.cypher",
            "002_add_requirement_entity.cypher"
        ]
        
        for migration_file in migration_files:
            migration_content = self.read_migration_file(migration_file)
            statements = [s.strip() for s in migration_content.split(';') if s.strip()]
            for statement in statements:
                conn.execute(statement)
        
        # Verify final state has all tables
        result = conn.execute("CALL show_tables() RETURN *")
        all_tables = []
        while result.has_next():
            row = result.get_next()
            all_tables.append(row[1])  # Table name is in column 1
        
        # Should have all tables from both migrations
        expected_tables = [
            "ImplementationEntity", "ImplementationURI", "VersionState",
            "Responsibility", "RequirementEntity", "LOCATES", "TRACKS_STATE_OF",
            "CONTAINS_LOCATION", "DEPENDS_ON", "HAS_RESPONSIBILITY",
            "SIMILAR_TO", "IMPLEMENTS"
        ]
        
        for table in expected_tables:
            assert table in all_tables, f"Table {table} missing after migrations"

    def test_migration_with_file_based_database(self):
        """Test migrations work with file-based database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create database connection with explicit path
            db_path = Path(tmpdir) / "test_migrations"
            conn_manager = KuzuConnectionManager(db_path=db_path)
            conn = conn_manager.get_connection()
            
            # Apply initial migration
            migration_content = self.read_migration_file("000_initial.cypher")
            statements = [s.strip() for s in migration_content.split(';') if s.strip()]
            for statement in statements:
                conn.execute(statement)
            
            # Verify tables exist
            result = conn.execute("CALL show_tables() RETURN *")
            tables = []
            while result.has_next():
                row = result.get_next()
                tables.append(row[1])  # Table name
            assert len(tables) > 0, "No tables created in file-based database"