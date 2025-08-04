"""KuzuDB adapter for flake graph with extended schema support."""

import kuzu
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import json
from log_py import log


class KuzuAdapter:
    """Adapter for KuzuDB with extended schema for flake analysis."""
    
    def __init__(self, db_path: Union[str, Path]):
        """Initialize KuzuDB connection and ensure schema exists.
        
        Args:
            db_path: Path to the KuzuDB database directory
        """
        self.db_path = Path(db_path)
        
        # If a directory is provided, create the database file inside it
        if self.db_path.is_dir():
            self.db_path.mkdir(parents=True, exist_ok=True)
            db_file = self.db_path / "db.kuzu"
        else:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            db_file = self.db_path
            
        self.db = kuzu.Database(str(db_file))
        self.conn = kuzu.Connection(self.db)
        self._initialize_schema()
    
    def _initialize_schema(self) -> None:
        """Create the extended schema if it doesn't exist."""
        # Create node table for flakes with extended properties
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Flake(
                path STRING PRIMARY KEY,
                description STRING,
                language STRING,
                vss_embedding FLOAT[],
                vss_analyzed_at TIMESTAMP,
                ast_score FLOAT,
                ast_metrics STRING
            )
        """)
        
    def create_flake(self, 
                     path: str,
                     description: str,
                     language: str,
                     vss_embedding: Optional[List[float]] = None,
                     vss_analyzed_at: Optional[datetime] = None,
                     ast_score: Optional[float] = None,
                     ast_metrics: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new flake node.
        
        Args:
            path: Primary key - the flake path
            description: Description of the flake
            language: Programming language
            vss_embedding: Vector space search embedding
            vss_analyzed_at: Timestamp of VSS analysis
            ast_score: Abstract syntax tree score
            ast_metrics: Additional AST metrics as a map
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert ast_metrics dict to map format if provided
            metrics_str = json.dumps(ast_metrics) if ast_metrics else None
            
            query = """
                CREATE (f:Flake {
                    path: $path,
                    description: $description,
                    language: $language,
                    vss_embedding: $vss_embedding,
                    vss_analyzed_at: $vss_analyzed_at,
                    ast_score: $ast_score,
                    ast_metrics: $ast_metrics
                })
            """
            
            self.conn.execute(query, {
                'path': path,
                'description': description,
                'language': language,
                'vss_embedding': vss_embedding,
                'vss_analyzed_at': vss_analyzed_at,
                'ast_score': ast_score,
                'ast_metrics': metrics_str
            })
            return True
        except Exception as e:
            log("ERROR", {
                "uri": "/kuzu/create_flake",
                "message": "Failed to create flake",
                "error": str(e),
                "path": path
            })
            return False
    
    def read_flake(self, path: str) -> Optional[Dict[str, Any]]:
        """Read a flake node by path.
        
        Args:
            path: The flake path (primary key)
            
        Returns:
            Dictionary with flake data or None if not found
        """
        try:
            query = """
                MATCH (f:Flake {path: $path})
                RETURN f.*
            """
            result = self.conn.execute(query, {'path': path})
            
            # Get results without pandas
            has_result = False
            for row in result:
                has_result = True
                # Convert row to dict
                row_dict = {}
                for i, col in enumerate(result.get_column_names()):
                    row_dict[col] = row[i]
                
                # Parse ast_metrics back to dict if present
                if row_dict.get('f.ast_metrics'):
                    row_dict['f.ast_metrics'] = json.loads(row_dict['f.ast_metrics'])
                
                # Clean up column names
                return {k.replace('f.', ''): v for k, v in row_dict.items()}
            
            if not has_result:
                return None
            
        except Exception as e:
            log("ERROR", {
                "uri": "/kuzu/read_flake",
                "message": "Failed to read flake",
                "error": str(e),
                "path": path
            })
            return None
    
    def update_flake(self, 
                     path: str,
                     **kwargs) -> bool:
        """Update a flake node with provided fields.
        
        Args:
            path: The flake path (primary key)
            **kwargs: Fields to update (description, language, vss_embedding, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build SET clause dynamically
            set_clauses = []
            params = {'path': path}
            
            for key, value in kwargs.items():
                if key == 'ast_metrics' and isinstance(value, dict):
                    value = json.dumps(value)
                
                set_clauses.append(f"f.{key} = ${key}")
                params[key] = value
            
            if not set_clauses:
                return True  # Nothing to update
            
            query = f"""
                MATCH (f:Flake {{path: $path}})
                SET {', '.join(set_clauses)}
            """
            
            self.conn.execute(query, params)
            return True
            
        except Exception as e:
            log("ERROR", {
                "uri": "/kuzu/update_flake",
                "message": "Failed to update flake",
                "error": str(e),
                "path": path
            })
            return False
    
    def delete_flake(self, path: str) -> bool:
        """Delete a flake node.
        
        Args:
            path: The flake path (primary key)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                MATCH (f:Flake {path: $path})
                DELETE f
            """
            self.conn.execute(query, {'path': path})
            return True
            
        except Exception as e:
            log("ERROR", {
                "uri": "/kuzu/delete_flake",
                "message": "Failed to delete flake",
                "error": str(e),
                "path": path
            })
            return False
    
    def list_flakes(self, 
                    language: Optional[str] = None,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all flakes with optional filtering.
        
        Args:
            language: Filter by programming language
            limit: Maximum number of results
            
        Returns:
            List of flake dictionaries
        """
        try:
            where_clause = ""
            params = {}
            
            if language:
                where_clause = "WHERE f.language = $language"
                params['language'] = language
            
            limit_clause = f"LIMIT {limit}" if limit else ""
            
            query = f"""
                MATCH (f:Flake)
                {where_clause}
                RETURN f.*
                ORDER BY f.path
                {limit_clause}
            """
            
            result = self.conn.execute(query, params)
            
            flakes = []
            for row in result:
                # Convert row to dict
                row_dict = {}
                for i, col in enumerate(result.get_column_names()):
                    row_dict[col] = row[i]
                
                # Parse ast_metrics back to dict if present
                if row_dict.get('f.ast_metrics'):
                    row_dict['f.ast_metrics'] = json.loads(row_dict['f.ast_metrics'])
                
                # Clean up column names
                flakes.append({k.replace('f.', ''): v for k, v in row_dict.items()})
            
            return flakes
            
        except Exception as e:
            log("ERROR", {
                "uri": "/kuzu/list_flakes",
                "message": "Failed to list flakes",
                "error": str(e),
                "language": language,
                "limit": limit
            })
            return []
    
    def find_by_embedding_similarity(self, 
                                   embedding: List[float],
                                   threshold: float = 0.8,
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """Find flakes with similar embeddings using cosine similarity.
        
        Args:
            embedding: Query embedding vector
            threshold: Minimum similarity threshold (0-1)
            limit: Maximum number of results
            
        Returns:
            List of flakes with similarity scores
        """
        try:
            # Note: This is a simplified example. In practice, you'd want to use
            # a proper vector similarity function or extension
            query = """
                MATCH (f:Flake)
                WHERE f.vss_embedding IS NOT NULL
                RETURN f.*, f.path as path
                LIMIT $limit
            """
            
            result = self.conn.execute(query, {'limit': limit})
            
            flakes = []
            for row in result:
                # Convert row to dict
                row_dict = {}
                for i, col in enumerate(result.get_column_names()):
                    row_dict[col] = row[i]
                
                if row_dict.get('f.ast_metrics'):
                    row_dict['f.ast_metrics'] = json.loads(row_dict['f.ast_metrics'])
                
                flakes.append({k.replace('f.', ''): v for k, v in row_dict.items()})
            
            return flakes
            
        except Exception as e:
            log("ERROR", {
                "uri": "/kuzu/find_by_embedding_similarity",
                "message": "Failed to find similar flakes",
                "error": str(e),
                "threshold": threshold,
                "limit": limit
            })
            return []
    
    def store_embedding(self, flake_id: str, embedding_data: Dict[str, Any]) -> None:
        """Store embedding data for a flake.
        
        Args:
            flake_id: Identifier for the flake
            embedding_data: Dictionary containing embedding vector and metadata
        """
        try:
            # First ensure the flake exists
            flake_path = f"/src/{flake_id}"  # Construct path from ID
            
            # Update flake with embedding data
            query = """
                MATCH (f:Flake {path: $path})
                SET f.vss_embedding = $embedding_vector,
                    f.embedding_model = $embedding_model,
                    f.model_version = $model_version,
                    f.embedding_created_at = $created_at,
                    f.content_hash = $content_hash
            """
            
            self.conn.execute(query, {
                'path': flake_path,
                'embedding_vector': embedding_data.get('embedding_vector', []),
                'embedding_model': embedding_data.get('embedding_model', ''),
                'model_version': embedding_data.get('model_version', ''),
                'created_at': embedding_data.get('created_at', ''),
                'content_hash': embedding_data.get('content_hash', '')
            })
            
            log("info", {
                "message": f"Stored embedding for flake {flake_id}",
                "component": "flake_graph.KuzuAdapter",
                "operation": "store_embedding",
                "flake_id": flake_id
            })
            
        except Exception as e:
            log("error", {
                "message": f"Failed to store embedding for {flake_id}",
                "component": "flake_graph.KuzuAdapter",
                "operation": "store_embedding",
                "error": str(e),
                "flake_id": flake_id
            })
    
    def get_embedding(self, flake_id: str) -> Optional[Dict[str, Any]]:
        """Get embedding data for a specific flake.
        
        Args:
            flake_id: Identifier for the flake
            
        Returns:
            Embedding data dictionary or None if not found
        """
        try:
            flake_path = f"/src/{flake_id}"
            
            query = """
                MATCH (f:Flake {path: $path})
                WHERE f.vss_embedding IS NOT NULL
                RETURN f.vss_embedding as embedding_vector,
                       f.embedding_model as embedding_model,
                       f.model_version as model_version,
                       f.embedding_created_at as created_at,
                       f.content_hash as content_hash
            """
            
            result = self.conn.execute(query, {'path': flake_path})
            
            for row in result:
                return {
                    'embedding_vector': row[0],
                    'embedding_model': row[1],
                    'model_version': row[2],
                    'created_at': row[3],
                    'content_hash': row[4]
                }
            
            return None
            
        except Exception as e:
            log("error", {
                "message": f"Failed to get embedding for {flake_id}",
                "component": "flake_graph.KuzuAdapter",
                "operation": "get_embedding",
                "error": str(e),
                "flake_id": flake_id
            })
            return None
    
    def get_all_embeddings(self) -> Dict[str, Dict[str, Any]]:
        """Get all stored embeddings.
        
        Returns:
            Dictionary mapping flake IDs to embedding data
        """
        try:
            query = """
                MATCH (f:Flake)
                WHERE f.vss_embedding IS NOT NULL
                RETURN f.path as path,
                       f.vss_embedding as embedding_vector,
                       f.embedding_model as embedding_model,
                       f.model_version as model_version,
                       f.embedding_created_at as created_at,
                       f.content_hash as content_hash
            """
            
            result = self.conn.execute(query)
            
            embeddings = {}
            for row in result:
                path = row[0]
                # Extract flake ID from path
                flake_id = path.split('/')[-1] if '/' in path else path
                
                embeddings[flake_id] = {
                    'embedding_vector': row[1],
                    'embedding_model': row[2],
                    'model_version': row[3],
                    'created_at': row[4],
                    'content_hash': row[5]
                }
            
            log("info", {
                "message": f"Retrieved {len(embeddings)} embeddings from KuzuDB",
                "component": "flake_graph.KuzuAdapter",
                "operation": "get_all_embeddings"
            })
            
            return embeddings
            
        except Exception as e:
            log("error", {
                "message": "Failed to get all embeddings",
                "component": "flake_graph.KuzuAdapter",
                "operation": "get_all_embeddings",
                "error": str(e)
            })
            return {}
    
    def close(self) -> None:
        """Close the database connection."""
        # KuzuDB handles connection cleanup automatically
        pass