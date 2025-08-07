#!/usr/bin/env python3
"""Apply migration to remove Responsibility table."""

from pathlib import Path
import logging
import kuzu_py

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Connect to database directly
    db_path = Path("./data/kuzu.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    db = kuzu_py.Database(str(db_path / "kuzu.db"))
    conn = kuzu_py.Connection(db)
    
    # Check current tables
    logger.info("=== Current tables before migration ===")
    result = conn.execute("CALL show_tables() RETURN *")
    while result.has_next():
        row = result.get_next()
        logger.info(f"  {row[1]} ({row[2]})")
    
    # Apply migration statements one by one
    logger.info("=== Applying migration 003_remove_responsibility.cypher ===")
    
    # Step 1: Delete HAS_RESPONSIBILITY relationships
    try:
        logger.info("1. Deleting HAS_RESPONSIBILITY relationships...")
        conn.execute("MATCH ()-[r:HAS_RESPONSIBILITY]->() DELETE r")
        logger.info("   ✓ Success")
    except Exception as e:
        logger.error(f"   ✗ Error: {e}")
    
    # Step 2: Drop HAS_RESPONSIBILITY table
    try:
        logger.info("2. Dropping HAS_RESPONSIBILITY table...")
        conn.execute("DROP TABLE HAS_RESPONSIBILITY CASCADE")
        logger.info("   ✓ Success")
    except Exception as e:
        logger.error(f"   ✗ Error: {e}")
    
    # Step 3: Drop Responsibility table
    try:
        logger.info("3. Dropping Responsibility table...")
        conn.execute("DROP TABLE Responsibility CASCADE")
        logger.info("   ✓ Success")
    except Exception as e:
        logger.error(f"   ✗ Error: {e}")
    
    # Verify results
    logger.info("=== Tables after migration ===")
    result = conn.execute("CALL show_tables() RETURN *")
    while result.has_next():
        row = result.get_next()
        logger.info(f"  {row[1]} ({row[2]})")
    
    logger.info("✅ Migration completed!")

if __name__ == "__main__":
    main()