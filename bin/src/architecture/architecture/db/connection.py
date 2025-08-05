"""KuzuDB connection management."""

from pathlib import Path
from typing import Optional
import kuzu_py


class KuzuConnectionManager:
    """Manages connections to KuzuDB."""
    
    def __init__(self, db_path: str | Path):
        """Initialize connection manager.
        
        Args:
            db_path: Path to the database directory
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self._db: Optional[kuzu_py.Database] = None
        self._conn: Optional[kuzu_py.Connection] = None
    
    def get_connection(self) -> kuzu_py.Connection:
        """Get or create a connection to the database.
        
        Returns:
            Active database connection
        """
        if self._conn is None:
            if self._db is None:
                # KuzuDB expects a file path, not a directory
                db_file = self.db_path / "kuzu.db"
                self._db = kuzu_py.Database(str(db_file))
            self._conn = kuzu_py.Connection(self._db)
        return self._conn
    
    def execute_ddl_file(self, ddl_path: Path) -> None:
        """Execute DDL statements from a file.
        
        Args:
            ddl_path: Path to DDL file containing Cypher statements
        """
        conn = self.get_connection()
        
        # Read DDL file
        with open(ddl_path, 'r') as f:
            ddl_content = f.read()
        
        # Split by semicolons and execute each statement
        statements = [stmt.strip() for stmt in ddl_content.split(';') if stmt.strip()]
        
        for statement in statements:
            # Skip comments and empty lines
            lines = [line for line in statement.split('\n') 
                    if line.strip() and not line.strip().startswith('--')]
            
            if lines:
                clean_statement = '\n'.join(lines)
                try:
                    conn.execute(clean_statement)
                except Exception as e:
                    # Some statements might fail if tables already exist
                    if "already exists" not in str(e):
                        raise
    
    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            # KuzuDB connections don't have explicit close
            self._conn = None
        if self._db is not None:
            self._db = None