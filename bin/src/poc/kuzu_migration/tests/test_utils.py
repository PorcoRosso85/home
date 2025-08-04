"""Test utilities for kuzu_migration tests.

This module provides helper functions and utilities for testing:
- Migration file generation
- Database state verification
- Test data creation
- Assertion helpers
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import kuzu


class MigrationTestHelper:
    """Helper class for migration testing."""
    
    @staticmethod
    def create_migration_set(
        ddl_dir: Path,
        migrations: List[Tuple[str, str]]
    ) -> List[Path]:
        """Create a set of migration files.
        
        Args:
            ddl_dir: Directory to create migrations in
            migrations: List of (filename, content) tuples
            
        Returns:
            List[Path]: Paths to created migration files
        """
        created_files = []
        for filename, content in migrations:
            filepath = ddl_dir / filename
            filepath.write_text(content)
            created_files.append(filepath)
        return created_files
    
    @staticmethod
    def verify_migration_applied(
        conn: kuzu.Connection,
        migration_name: str,
        migrations_table: str = "_migrations"
    ) -> bool:
        """Verify if a specific migration has been applied.
        
        Args:
            conn: KuzuDB connection
            migration_name: Name of the migration to check
            migrations_table: Name of the migrations tracking table
            
        Returns:
            bool: True if migration is applied, False otherwise
        """
        try:
            query = f"""
            MATCH (m:{migrations_table})
            WHERE m.name = $name
            RETURN m.name
            """
            result = conn.execute(query, {"name": migration_name})
            return result.has_next()
        except Exception:
            return False
    
    @staticmethod
    def get_applied_migrations(
        conn: kuzu.Connection,
        migrations_table: str = "_migrations"
    ) -> List[str]:
        """Get list of applied migration names.
        
        Args:
            conn: KuzuDB connection
            migrations_table: Name of the migrations tracking table
            
        Returns:
            List[str]: Names of applied migrations in order
        """
        try:
            query = f"""
            MATCH (m:{migrations_table})
            RETURN m.name
            ORDER BY m.applied_at
            """
            result = conn.execute(query)
            migrations = []
            while result.has_next():
                migrations.append(result.get_next()[0])
            return migrations
        except Exception:
            return []


class CLITestHelper:
    """Helper class for CLI testing."""
    
    @staticmethod
    def run_kuzu_migrate(
        args: List[str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[Path] = None
    ) -> subprocess.CompletedProcess:
        """Run kuzu-migrate CLI command.
        
        Args:
            args: Command line arguments
            env: Environment variables
            cwd: Working directory
            
        Returns:
            subprocess.CompletedProcess: Result of the command
        """
        cmd = ["kuzu-migrate"] + args
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd
        )
    
    @staticmethod
    def assert_command_success(
        result: subprocess.CompletedProcess,
        expected_output: Optional[str] = None
    ) -> None:
        """Assert that a CLI command executed successfully.
        
        Args:
            result: Result from subprocess.run
            expected_output: Optional expected output substring
        """
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        if expected_output:
            assert expected_output in result.stdout, \
                f"Expected '{expected_output}' in output: {result.stdout}"
    
    @staticmethod
    def assert_command_failure(
        result: subprocess.CompletedProcess,
        expected_error: Optional[str] = None
    ) -> None:
        """Assert that a CLI command failed.
        
        Args:
            result: Result from subprocess.run
            expected_error: Optional expected error substring
        """
        assert result.returncode != 0, "Command should have failed"
        if expected_error:
            assert expected_error in result.stderr, \
                f"Expected '{expected_error}' in error: {result.stderr}"


class DatabaseTestHelper:
    """Helper class for database state verification."""
    
    @staticmethod
    def table_exists(conn: kuzu.Connection, table_name: str) -> bool:
        """Check if a table exists in the database.
        
        Args:
            conn: KuzuDB connection
            table_name: Name of the table
            
        Returns:
            bool: True if table exists
        """
        try:
            # Try a simple query on the table
            conn.execute(f"MATCH (n:{table_name}) RETURN n LIMIT 1")
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_table_properties(
        conn: kuzu.Connection,
        table_name: str
    ) -> Dict[str, Any]:
        """Get properties of a table.
        
        Args:
            conn: KuzuDB connection
            table_name: Name of the table
            
        Returns:
            Dict[str, Any]: Table properties
        """
        # This is a placeholder - actual implementation would depend on
        # KuzuDB's schema introspection capabilities
        return {}
    
    @staticmethod
    def count_nodes(conn: kuzu.Connection, label: str) -> int:
        """Count nodes with a specific label.
        
        Args:
            conn: KuzuDB connection
            label: Node label
            
        Returns:
            int: Number of nodes
        """
        result = conn.execute(f"MATCH (n:{label}) RETURN COUNT(n)")
        return result.get_next()[0]
    
    @staticmethod
    def count_relationships(
        conn: kuzu.Connection,
        rel_type: str,
        from_label: Optional[str] = None,
        to_label: Optional[str] = None
    ) -> int:
        """Count relationships of a specific type.
        
        Args:
            conn: KuzuDB connection
            rel_type: Relationship type
            from_label: Optional source node label
            to_label: Optional target node label
            
        Returns:
            int: Number of relationships
        """
        if from_label and to_label:
            query = f"""
            MATCH (a:{from_label})-[r:{rel_type}]->(b:{to_label})
            RETURN COUNT(r)
            """
        else:
            query = f"MATCH ()-[r:{rel_type}]->() RETURN COUNT(r)"
        
        result = conn.execute(query)
        return result.get_next()[0]


# Test data generators
def generate_test_users(count: int) -> List[Dict[str, Any]]:
    """Generate test user data.
    
    Args:
        count: Number of users to generate
        
    Returns:
        List[Dict[str, Any]]: User data
    """
    users = []
    for i in range(count):
        users.append({
            "id": i + 1,
            "name": f"User{i + 1}",
            "email": f"user{i + 1}@example.com"
        })
    return users


def generate_test_relationships(
    users: List[Dict[str, Any]],
    rel_probability: float = 0.3
) -> List[Tuple[int, int]]:
    """Generate test relationship data.
    
    Args:
        users: List of user data
        rel_probability: Probability of relationship between users
        
    Returns:
        List[Tuple[int, int]]: List of (from_id, to_id) tuples
    """
    import random
    relationships = []
    
    for i, user1 in enumerate(users):
        for j, user2 in enumerate(users):
            if i != j and random.random() < rel_probability:
                relationships.append((user1["id"], user2["id"]))
    
    return relationships