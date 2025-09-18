"""Manual test for snapshot functionality."""

import tempfile
from pathlib import Path
from architecture.db import KuzuConnectionManager
import kuzu_py
import shutil


def test_manual_snapshot():
    """Manually test snapshot creation after migration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup database
        db_path = Path(tmpdir) / "test_db"
        conn_manager = KuzuConnectionManager(db_path=db_path)
        
        # Apply DDL
        ddl_path = Path(__file__).parent / "ddl" / "migrations" / "000_initial.cypher"
        conn_manager.execute_ddl_file(ddl_path)
        
        # Create snapshot directory
        snapshot_dir = Path(__file__).parent / "ddl" / "snapshots"
        snapshot_dir.mkdir(exist_ok=True)
        
        # Export database state
        conn = conn_manager.get_connection()
        
        # Get all tables
        result = conn.execute("CALL show_tables() RETURN *")
        tables = []
        while result.has_next():
            row = result.get_next()
            tables.append({
                'name': row[1],  # Table name is in column 1
                'type': row[2]   # Table type (NODE/REL)
            })
        
        # Create snapshot metadata
        snapshot_file = snapshot_dir / "snapshot_v1.0.0_manual.txt"
        with open(snapshot_file, 'w') as f:
            f.write("=== Manual Snapshot v1.0.0 ===\n")
            f.write(f"Database Path: {db_path}\n")
            f.write(f"Tables Created: {len(tables)}\n\n")
            
            f.write("Tables:\n")
            for table in tables:
                f.write(f"  - {table['name']} ({table['type']})\n")
            
            # Export each table structure
            f.write("\nTable Structures:\n")
            for table in tables:
                if table['type'] == 'NODE':
                    # Get node table properties
                    try:
                        result = conn.execute(f"MATCH (n:{table['name']}) RETURN n LIMIT 0")
                        f.write(f"\n{table['name']} (NODE TABLE):\n")
                        f.write("  Properties: [Schema would be here]\n")
                    except:
                        f.write(f"\n{table['name']} (NODE TABLE): No data to infer schema\n")
                elif table['type'] == 'REL':
                    f.write(f"\n{table['name']} (REL TABLE):\n")
                    f.write("  Properties: [Schema would be here]\n")
        
        print(f"Snapshot created: {snapshot_file}")
        print(f"Tables found: {[t['name'] for t in tables]}")
        
        # Verify snapshot was created
        assert snapshot_file.exists()
        return snapshot_file


if __name__ == "__main__":
    snapshot_file = test_manual_snapshot()
    with open(snapshot_file, 'r') as f:
        print("\nSnapshot content:")
        print(f.read())