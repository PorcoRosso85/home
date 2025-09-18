#!/usr/bin/env python3
"""
Apply migrations 004 and 005 to the database
"""

import kuzu
import os
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def apply_migration(conn: kuzu.Connection, migration_file: Path):
    """Apply a single migration file"""
    logger.info(f"Applying migration: {migration_file.name}")
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    # Split by statements and execute each
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for i, stmt in enumerate(statements):
        if 'MATCH' in stmt or 'CREATE' in stmt or 'DROP' in stmt or 'ALTER' in stmt:
            try:
                logger.info(f"  Executing statement {i+1}/{len(statements)}...")
                result = conn.execute(stmt)
                if hasattr(result, 'get_num_tuples'):
                    logger.info(f"    Affected rows: {result.get_num_tuples()}")
            except Exception as e:
                logger.error(f"    Error: {e}")
                # Continue with next statement

def main():
    db_path = "data/kuzu.db"
    migrations_dir = Path("ddl/migrations")
    
    # Connect to database
    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)
    
    # Apply migrations in order
    migrations = [
        "004_rename_contains_and_reverse_locates.cypher",
        "005_reverse_implements_to_implemented_by.cypher"
    ]
    
    for migration in migrations:
        migration_file = migrations_dir / migration
        if migration_file.exists():
            apply_migration(conn, migration_file)
        else:
            logger.error(f"Migration file not found: {migration}")
    
    # Verify final state
    logger.info("=== Verifying final schema ===")
    
    # Check tables
    result = conn.execute("CALL show_tables() RETURN *")
    logger.info("Tables in database:")
    while result.has_next():
        row = result.get_next()
        logger.info(f"  - {row}")
    
    # Check specific relationships
    logger.info("Checking new relationships:")
    
    # Check CONTAINS
    try:
        result = conn.execute("MATCH ()-[r:CONTAINS]->() RETURN COUNT(r) as count")
        if result.has_next():
            logger.info(f"  CONTAINS relationships: {result.get_next()[0]}")
    except:
        logger.warning("  CONTAINS relationship not found")
    
    # Check IMPLEMENTED_BY
    try:
        result = conn.execute("MATCH ()-[r:IMPLEMENTED_BY]->() RETURN COUNT(r) as count")
        if result.has_next():
            logger.info(f"  IMPLEMENTED_BY relationships: {result.get_next()[0]}")
    except:
        logger.warning("  IMPLEMENTED_BY relationship not found")
    
    # Check LOCATES direction
    try:
        result = conn.execute("MATCH (uri:LocationURI)-[r:LOCATES]->(impl:ImplementationEntity) RETURN COUNT(r) as count")
        if result.has_next():
            logger.info(f"  LOCATES (URI→Entity) relationships: {result.get_next()[0]}")
    except Exception as e:
        logger.error(f"  Error checking LOCATES: {e}")
    
    conn.close()
    db.close()
    logger.info("Migration complete!")

if __name__ == "__main__":
    main()