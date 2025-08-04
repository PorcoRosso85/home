"""Common pytest fixtures and utilities for kuzu_migration tests.

This module provides shared test fixtures for:
- Temporary database creation
- Test data setup
- KuzuDB connection management
- Migration utilities
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import kuzu
import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test databases.
    
    Yields:
        Path: Path to the temporary directory
    """
    temp_path = Path(tempfile.mkdtemp(prefix="kuzu_test_"))
    try:
        yield temp_path
    finally:
        if temp_path.exists():
            shutil.rmtree(temp_path)


@pytest.fixture
def temp_db_path(temp_dir: Path) -> Path:
    """Create a path for a temporary test database.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path: Path to the test database directory
    """
    db_path = temp_dir / "test_db"
    return db_path


@pytest.fixture
def kuzu_db(temp_db_path: Path) -> Generator[kuzu.Database, None, None]:
    """Create a temporary KuzuDB database instance.
    
    Args:
        temp_db_path: Path to the temporary database
        
    Yields:
        kuzu.Database: KuzuDB database instance
    """
    db = kuzu.Database(str(temp_db_path))
    try:
        yield db
    finally:
        del db  # Ensure database is closed


@pytest.fixture
def kuzu_conn(kuzu_db: kuzu.Database) -> Generator[kuzu.Connection, None, None]:
    """Create a KuzuDB connection.
    
    Args:
        kuzu_db: KuzuDB database instance
        
    Yields:
        kuzu.Connection: KuzuDB connection instance
    """
    conn = kuzu.Connection(kuzu_db)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def sample_ddl_dir(temp_dir: Path) -> Path:
    """Create a sample DDL directory with test migrations.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        Path: Path to the DDL directory with sample migrations
    """
    ddl_dir = temp_dir / "ddl"
    ddl_dir.mkdir(exist_ok=True)
    
    # Create sample migration files
    migrations = [
        ("001_create_user_table.cypher", 
         "CREATE NODE TABLE User(id INT64, name STRING, PRIMARY KEY(id));"),
        ("002_create_follows_rel.cypher",
         "CREATE REL TABLE Follows(FROM User TO User, since DATE);"),
        ("003_add_user_email.cypher",
         "ALTER TABLE User ADD email STRING;"),
    ]
    
    for filename, content in migrations:
        (ddl_dir / filename).write_text(content)
    
    return ddl_dir


@pytest.fixture
def migration_config(temp_db_path: Path, sample_ddl_dir: Path) -> dict:
    """Create a migration configuration dictionary.
    
    Args:
        temp_db_path: Path to the temporary database
        sample_ddl_dir: Path to the DDL directory
        
    Returns:
        dict: Migration configuration
    """
    return {
        "database_path": str(temp_db_path),
        "ddl_path": str(sample_ddl_dir),
        "migrations_table": "_migrations",
    }


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables before each test."""
    # Store original environment
    original_env = os.environ.copy()
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.internal = pytest.mark.internal
pytest.mark.external = pytest.mark.external


# Helper functions for tests
def create_test_migration(path: Path, name: str, content: str) -> Path:
    """Create a test migration file.
    
    Args:
        path: Directory to create the migration in
        name: Name of the migration file
        content: Cypher content of the migration
        
    Returns:
        Path: Path to the created migration file
    """
    migration_path = path / name
    migration_path.write_text(content)
    return migration_path


def verify_table_exists(conn: kuzu.Connection, table_name: str) -> bool:
    """Verify if a table exists in the database.
    
    Args:
        conn: KuzuDB connection
        table_name: Name of the table to check
        
    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        # Try to query the table
        conn.execute(f"MATCH (n:{table_name}) RETURN COUNT(n) LIMIT 1;")
        return True
    except Exception:
        return False


def get_migration_count(conn: kuzu.Connection, migrations_table: str = "_migrations") -> int:
    """Get the count of applied migrations.
    
    Args:
        conn: KuzuDB connection
        migrations_table: Name of the migrations tracking table
        
    Returns:
        int: Number of applied migrations
    """
    try:
        result = conn.execute(f"MATCH (m:{migrations_table}) RETURN COUNT(m);")
        return result.get_next()[0]
    except Exception:
        return 0