"""KuzuDB connection management."""

from pathlib import Path
from typing import Optional
import kuzu_py
from infrastructure.types.result import Result, Ok, Err


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
    
    def execute_ddl_file(self, ddl_path: Path) -> Result[int, str]:
        """Execute DDL statements from a file.
        
        Args:
            ddl_path: Path to DDL file containing Cypher statements
            
        Returns:
            Result[int, str]: Ok(number_of_executed_statements) on success, 
                            Err(error_message) on failure
        """
        try:
            conn = self.get_connection()
            
            # Check if file exists
            if not ddl_path.exists():
                return Err(f"DDL file not found: {ddl_path}")
            
            # Read DDL file
            try:
                with open(ddl_path, 'r') as f:
                    ddl_content = f.read()
            except Exception as e:
                return Err(f"Failed to read DDL file: {e}")
            
            # Split by semicolons and execute each statement
            statements = [stmt.strip() for stmt in ddl_content.split(';') if stmt.strip()]
            executed_count = 0
            
            for statement in statements:
                # Remove comments and clean up the statement
                lines = []
                for line in statement.split('\n'):
                    # Remove inline comments (--) and trim
                    if '--' in line:
                        line = line[:line.index('--')]
                    line = line.strip()
                    if line:
                        lines.append(line)
                
                if lines:
                    clean_statement = '\n'.join(lines)
                    try:
                        conn.execute(clean_statement)
                        executed_count += 1
                    except Exception as e:
                        # Some statements might fail if tables already exist
                        if "already exists" not in str(e):
                            return Err(f"DDL execution failed: {e}")
                        # If it's an "already exists" error, count it as executed
                        executed_count += 1
            
            return Ok(executed_count)
            
        except Exception as e:
            return Err(f"DDL execution failed: {e}")
    
    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            # KuzuDB connections don't have explicit close
            self._conn = None
        if self._db is not None:
            self._db = None