"""Functional KuzuDB adapter for flake graph with extended schema support."""

import kuzu
from datetime import datetime
from pathlib import Path
from typing import TypedDict, Optional, List, Dict, Any, Union, Tuple
import json
from log_py import log


# Type definitions
class KuzuConnection(TypedDict):
    """Type for database connection information."""
    db: kuzu.Database
    conn: kuzu.Connection
    db_path: Path


class FlakeData(TypedDict, total=False):
    """Type for flake data structure."""
    path: str  # Primary key
    description: str
    language: str
    vss_embedding: Optional[List[float]]
    vss_analyzed_at: Optional[datetime]
    ast_score: Optional[float]
    ast_metrics: Optional[Dict[str, Any]]


class EmbeddingData(TypedDict):
    """Type for embedding data structure."""
    embedding_vector: List[float]
    embedding_model: str
    model_version: str
    created_at: str
    content_hash: str


# Error types following error_handling.md convention
class ErrorDict(TypedDict):
    """Base error type."""
    ok: bool  # Always False for errors
    error_type: str
    message: str
    details: Dict[str, Any]


class ConnectionErrorDict(ErrorDict):
    """Error when database connection fails."""
    pass


class SchemaErrorDict(ErrorDict):
    """Error when schema operations fail."""
    pass


class QueryErrorDict(ErrorDict):
    """Error when query execution fails."""
    pass


class ValidationErrorDict(ErrorDict):
    """Error when data validation fails."""
    pass


# Success types
class ConnectionSuccessDict(TypedDict):
    """Success result for connection operations."""
    ok: bool  # Always True for success
    connection: KuzuConnection


class FlakeSuccessDict(TypedDict):
    """Success result for flake operations."""
    ok: bool  # Always True for success
    data: FlakeData


class FlakeListSuccessDict(TypedDict):
    """Success result for list operations."""
    ok: bool  # Always True for success
    data: List[FlakeData]


class EmbeddingSuccessDict(TypedDict):
    """Success result for embedding operations."""
    ok: bool  # Always True for success
    data: EmbeddingData


class EmbeddingDictSuccessDict(TypedDict):
    """Success result for get_all_embeddings."""
    ok: bool  # Always True for success
    data: Dict[str, EmbeddingData]


class OperationSuccessDict(TypedDict):
    """Success result for operations without return data."""
    ok: bool  # Always True for success
    message: str


# Database connection functions
def create_connection(db_path: Union[str, Path]) -> Union[ConnectionSuccessDict, ConnectionErrorDict]:
    """Create a new KuzuDB connection.
    
    Args:
        db_path: Path to the KuzuDB database directory
        
    Returns:
        ConnectionSuccessDict with connection or ConnectionErrorDict on failure
    """
    try:
        path = Path(db_path)
        
        # If a directory is provided, create the database file inside it
        if path.is_dir():
            path.mkdir(parents=True, exist_ok=True)
            db_file = path / "db.kuzu"
        else:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            db_file = path
            
        db = kuzu.Database(str(db_file))
        conn = kuzu.Connection(db)
        
        # Initialize schema
        schema_result = initialize_schema(conn)
        if not schema_result.get('ok', False):
            return ConnectionErrorDict(
                ok=False,
                error_type="schema_initialization_error",
                message="Failed to initialize database schema",
                details={
                    "db_path": str(db_path),
                    "schema_error": schema_result
                }
            )
        
        connection = KuzuConnection(db=db, conn=conn, db_path=path)
        return ConnectionSuccessDict(ok=True, connection=connection)
        
    except Exception as e:
        return ConnectionErrorDict(
            ok=False,
            error_type="connection_error",
            message=f"Failed to create database connection: {str(e)}",
            details={
                "db_path": str(db_path),
                "exception": str(e),
                "exception_type": type(e).__name__
            }
        )


def initialize_schema(conn: kuzu.Connection) -> Union[OperationSuccessDict, SchemaErrorDict]:
    """Create the extended schema if it doesn't exist.
    
    Args:
        conn: KuzuDB connection object
        
    Returns:
        OperationSuccessDict on success or SchemaErrorDict on failure
    """
    try:
        conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Flake(
                path STRING PRIMARY KEY,
                description STRING,
                language STRING,
                vss_embedding FLOAT[],
                vss_analyzed_at TIMESTAMP,
                ast_score FLOAT,
                ast_metrics STRING,
                embedding_model STRING,
                model_version STRING,
                embedding_created_at STRING,
                content_hash STRING
            )
        """)
        return OperationSuccessDict(
            ok=True,
            message="Schema initialized successfully"
        )
    except Exception as e:
        return SchemaErrorDict(
            ok=False,
            error_type="schema_creation_error",
            message=f"Failed to create schema: {str(e)}",
            details={
                "exception": str(e),
                "exception_type": type(e).__name__
            }
        )


def close_connection(connection: KuzuConnection) -> None:
    """Close the database connection.
    
    Args:
        connection: KuzuConnection to close
    """
    # KuzuDB handles connection cleanup automatically
    pass


# CRUD operations
def create_flake(connection: KuzuConnection, flake_data: FlakeData) -> Union[OperationSuccessDict, QueryErrorDict]:
    """Create a new flake node.
    
    Args:
        connection: KuzuDB connection
        flake_data: Flake data to insert
        
    Returns:
        OperationSuccessDict on success or QueryErrorDict on failure
    """
    try:
        # Validate required field
        if not flake_data.get('path'):
            return QueryErrorDict(
                ok=False,
                error_type="validation_error",
                message="Path is required for creating a flake",
                details={"flake_data": flake_data}
            )
        
        # Convert ast_metrics dict to string if provided
        metrics_str = json.dumps(flake_data.get('ast_metrics')) if flake_data.get('ast_metrics') else None
        
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
        
        connection['conn'].execute(query, {
            'path': flake_data['path'],
            'description': flake_data.get('description', ''),
            'language': flake_data.get('language', ''),
            'vss_embedding': flake_data.get('vss_embedding'),
            'vss_analyzed_at': flake_data.get('vss_analyzed_at'),
            'ast_score': flake_data.get('ast_score'),
            'ast_metrics': metrics_str
        })
        
        log("INFO", {
            "uri": "/kuzu/create_flake",
            "message": "Successfully created flake",
            "path": flake_data['path']
        })
        
        return OperationSuccessDict(
            ok=True,
            message=f"Successfully created flake at path: {flake_data['path']}"
        )
        
    except Exception as e:
        log("ERROR", {
            "uri": "/kuzu/create_flake",
            "message": "Failed to create flake",
            "error": str(e),
            "path": flake_data.get('path', 'unknown')
        })
        
        return QueryErrorDict(
            ok=False,
            error_type="query_execution_error",
            message=f"Failed to create flake: {str(e)}",
            details={
                "path": flake_data.get('path', 'unknown'),
                "exception": str(e),
                "exception_type": type(e).__name__,
                "query": "CREATE flake node"
            }
        )


def read_flake(connection: KuzuConnection, path: str) -> Union[FlakeSuccessDict, QueryErrorDict]:
    """Read a flake node by path.
    
    Args:
        connection: KuzuDB connection
        path: The flake path (primary key)
        
    Returns:
        FlakeSuccessDict with data or QueryErrorDict on failure/not found
    """
    try:
        if not path:
            return QueryErrorDict(
                ok=False,
                error_type="validation_error",
                message="Path is required for reading a flake",
                details={"path": path}
            )
            
        query = """
            MATCH (f:Flake {path: $path})
            RETURN f.*
        """
        result = connection['conn'].execute(query, {'path': path})
        
        # Get results without pandas
        for row in result:
            # Convert row to dict
            row_dict = {}
            for i, col in enumerate(result.get_column_names()):
                row_dict[col] = row[i]
            
            # Parse ast_metrics back to dict if present
            if row_dict.get('f.ast_metrics'):
                try:
                    row_dict['f.ast_metrics'] = json.loads(row_dict['f.ast_metrics'])
                except json.JSONDecodeError:
                    row_dict['f.ast_metrics'] = None
            
            # Clean up column names and return as FlakeData
            cleaned_data = {k.replace('f.', ''): v for k, v in row_dict.items() if v is not None}
            
            return FlakeSuccessDict(
                ok=True,
                data=FlakeData(**cleaned_data)
            )
        
        # No results found
        return QueryErrorDict(
            ok=False,
            error_type="not_found",
            message=f"Flake not found at path: {path}",
            details={"path": path}
        )
        
    except Exception as e:
        log("ERROR", {
            "uri": "/kuzu/read_flake",
            "message": "Failed to read flake",
            "error": str(e),
            "path": path
        })
        
        return QueryErrorDict(
            ok=False,
            error_type="query_execution_error",
            message=f"Failed to read flake: {str(e)}",
            details={
                "path": path,
                "exception": str(e),
                "exception_type": type(e).__name__,
                "query": "MATCH flake by path"
            }
        )


def update_flake(connection: KuzuConnection, path: str, updates: Dict[str, Any]) -> Union[OperationSuccessDict, QueryErrorDict]:
    """Update a flake node with provided fields.
    
    Args:
        connection: KuzuDB connection
        path: The flake path (primary key)
        updates: Dictionary of fields to update
        
    Returns:
        OperationSuccessDict on success or QueryErrorDict on failure
    """
    try:
        if not path:
            return QueryErrorDict(
                ok=False,
                error_type="validation_error",
                message="Path is required for updating a flake",
                details={"path": path, "updates": updates}
            )
            
        # Build SET clause dynamically
        set_clauses = []
        params = {'path': path}
        
        for key, value in updates.items():
            if key == 'ast_metrics' and isinstance(value, dict):
                value = json.dumps(value)
            
            set_clauses.append(f"f.{key} = ${key}")
            params[key] = value
        
        if not set_clauses:
            return OperationSuccessDict(
                ok=True,
                message=f"No updates provided for flake at path: {path}"
            )
        
        query = f"""
            MATCH (f:Flake {{path: $path}})
            SET {', '.join(set_clauses)}
        """
        
        connection['conn'].execute(query, params)
        
        log("INFO", {
            "uri": "/kuzu/update_flake",
            "message": "Successfully updated flake",
            "path": path,
            "updated_fields": list(updates.keys())
        })
        
        return OperationSuccessDict(
            ok=True,
            message=f"Successfully updated flake at path: {path}"
        )
        
    except Exception as e:
        log("ERROR", {
            "uri": "/kuzu/update_flake",
            "message": "Failed to update flake",
            "error": str(e),
            "path": path
        })
        
        return QueryErrorDict(
            ok=False,
            error_type="query_execution_error",
            message=f"Failed to update flake: {str(e)}",
            details={
                "path": path,
                "updates": updates,
                "exception": str(e),
                "exception_type": type(e).__name__,
                "query": "UPDATE flake node"
            }
        )


def delete_flake(connection: KuzuConnection, path: str) -> Union[OperationSuccessDict, QueryErrorDict]:
    """Delete a flake node.
    
    Args:
        connection: KuzuDB connection
        path: The flake path (primary key)
        
    Returns:
        OperationSuccessDict on success or QueryErrorDict on failure
    """
    try:
        if not path:
            return QueryErrorDict(
                ok=False,
                error_type="validation_error",
                message="Path is required for deleting a flake",
                details={"path": path}
            )
            
        query = """
            MATCH (f:Flake {path: $path})
            DELETE f
        """
        connection['conn'].execute(query, {'path': path})
        
        log("INFO", {
            "uri": "/kuzu/delete_flake",
            "message": "Successfully deleted flake",
            "path": path
        })
        
        return OperationSuccessDict(
            ok=True,
            message=f"Successfully deleted flake at path: {path}"
        )
        
    except Exception as e:
        log("ERROR", {
            "uri": "/kuzu/delete_flake",
            "message": "Failed to delete flake",
            "error": str(e),
            "path": path
        })
        
        return QueryErrorDict(
            ok=False,
            error_type="query_execution_error",
            message=f"Failed to delete flake: {str(e)}",
            details={
                "path": path,
                "exception": str(e),
                "exception_type": type(e).__name__,
                "query": "DELETE flake node"
            }
        )


# Query operations
def list_flakes(connection: KuzuConnection, 
                language: Optional[str] = None,
                limit: Optional[int] = None) -> Union[FlakeListSuccessDict, QueryErrorDict]:
    """List all flakes with optional filtering.
    
    Args:
        connection: KuzuDB connection
        language: Filter by programming language
        limit: Maximum number of results
        
    Returns:
        FlakeListSuccessDict with data or QueryErrorDict on failure
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
        
        result = connection['conn'].execute(query, params)
        
        flakes = []
        for row in result:
            # Convert row to dict
            row_dict = {}
            for i, col in enumerate(result.get_column_names()):
                row_dict[col] = row[i]
            
            # Parse ast_metrics back to dict if present
            if row_dict.get('f.ast_metrics'):
                try:
                    row_dict['f.ast_metrics'] = json.loads(row_dict['f.ast_metrics'])
                except json.JSONDecodeError:
                    row_dict['f.ast_metrics'] = None
            
            # Clean up column names
            cleaned_data = {k.replace('f.', ''): v for k, v in row_dict.items() if v is not None}
            flakes.append(FlakeData(**cleaned_data))
        
        log("INFO", {
            "uri": "/kuzu/list_flakes",
            "message": f"Successfully listed {len(flakes)} flakes",
            "language": language,
            "limit": limit,
            "count": len(flakes)
        })
        
        return FlakeListSuccessDict(
            ok=True,
            data=flakes
        )
        
    except Exception as e:
        log("ERROR", {
            "uri": "/kuzu/list_flakes",
            "message": "Failed to list flakes",
            "error": str(e),
            "language": language,
            "limit": limit
        })
        
        return QueryErrorDict(
            ok=False,
            error_type="query_execution_error",
            message=f"Failed to list flakes: {str(e)}",
            details={
                "language": language,
                "limit": limit,
                "exception": str(e),
                "exception_type": type(e).__name__,
                "query": "MATCH all flakes"
            }
        )


def find_by_embedding_similarity(connection: KuzuConnection,
                               embedding: List[float],
                               threshold: float = 0.8,
                               limit: int = 10) -> Union[FlakeListSuccessDict, QueryErrorDict]:
    """Find flakes with similar embeddings.
    
    Args:
        connection: KuzuDB connection
        embedding: Query embedding vector
        threshold: Minimum similarity threshold (0-1)
        limit: Maximum number of results
        
    Returns:
        FlakeListSuccessDict with data or QueryErrorDict on failure
    """
    try:
        if not embedding or not isinstance(embedding, list):
            return QueryErrorDict(
                ok=False,
                error_type="validation_error",
                message="Valid embedding vector is required",
                details={
                    "embedding_type": type(embedding).__name__,
                    "embedding_length": len(embedding) if isinstance(embedding, list) else 0
                }
            )
            
        # Note: This is a simplified example. In practice, you'd want to use
        # a proper vector similarity function or extension
        query = """
            MATCH (f:Flake)
            WHERE f.vss_embedding IS NOT NULL
            RETURN f.*, f.path as path
            LIMIT $limit
        """
        
        result = connection['conn'].execute(query, {'limit': limit})
        
        flakes = []
        for row in result:
            # Convert row to dict
            row_dict = {}
            for i, col in enumerate(result.get_column_names()):
                row_dict[col] = row[i]
            
            if row_dict.get('f.ast_metrics'):
                try:
                    row_dict['f.ast_metrics'] = json.loads(row_dict['f.ast_metrics'])
                except json.JSONDecodeError:
                    row_dict['f.ast_metrics'] = None
            
            cleaned_data = {k.replace('f.', ''): v for k, v in row_dict.items() if v is not None}
            flakes.append(FlakeData(**cleaned_data))
        
        log("INFO", {
            "uri": "/kuzu/find_by_embedding_similarity",
            "message": f"Found {len(flakes)} similar flakes",
            "threshold": threshold,
            "limit": limit,
            "count": len(flakes)
        })
        
        return FlakeListSuccessDict(
            ok=True,
            data=flakes
        )
        
    except Exception as e:
        log("ERROR", {
            "uri": "/kuzu/find_by_embedding_similarity",
            "message": "Failed to find similar flakes",
            "error": str(e),
            "threshold": threshold,
            "limit": limit
        })
        
        return QueryErrorDict(
            ok=False,
            error_type="query_execution_error",
            message=f"Failed to find similar flakes: {str(e)}",
            details={
                "threshold": threshold,
                "limit": limit,
                "exception": str(e),
                "exception_type": type(e).__name__,
                "query": "MATCH flakes with embeddings"
            }
        )


# Embedding operations
def store_embedding(connection: KuzuConnection, flake_id: str, embedding_data: EmbeddingData) -> Union[OperationSuccessDict, QueryErrorDict]:
    """Store embedding data for a flake.
    
    Args:
        connection: KuzuDB connection
        flake_id: Identifier for the flake
        embedding_data: Embedding data to store
        
    Returns:
        OperationSuccessDict on success or QueryErrorDict on failure
    """
    try:
        if not flake_id:
            return QueryErrorDict(
                ok=False,
                error_type="validation_error",
                message="Flake ID is required for storing embedding",
                details={"flake_id": flake_id}
            )
            
        if not embedding_data.get('embedding_vector'):
            return QueryErrorDict(
                ok=False,
                error_type="validation_error",
                message="Embedding vector is required",
                details={
                    "flake_id": flake_id,
                    "embedding_data_keys": list(embedding_data.keys())
                }
            )
            
        # First ensure the flake exists
        flake_path = f"/src/{flake_id}"  # Construct path from ID
        
        # Update flake with embedding data, creating node if it doesn't exist
        query = """
            MERGE (f:Flake {path: $path})
            SET f.vss_embedding = $embedding_vector,
                f.embedding_model = $embedding_model,
                f.model_version = $model_version,
                f.embedding_created_at = $created_at,
                f.content_hash = $content_hash
        """
        
        connection['conn'].execute(query, {
            'path': flake_path,
            'embedding_vector': embedding_data['embedding_vector'],
            'embedding_model': embedding_data['embedding_model'],
            'model_version': embedding_data['model_version'],
            'created_at': embedding_data['created_at'],
            'content_hash': embedding_data['content_hash']
        })
        
        log("INFO", {
            "uri": "/kuzu/store_embedding",
            "message": f"Stored embedding for flake {flake_id}",
            "component": "flake_graph.kuzu_adapter_functional",
            "operation": "store_embedding",
            "flake_id": flake_id
        })
        
        return OperationSuccessDict(
            ok=True,
            message=f"Successfully stored embedding for flake: {flake_id}"
        )
        
    except Exception as e:
        log("ERROR", {
            "uri": "/kuzu/store_embedding",
            "message": f"Failed to store embedding for {flake_id}",
            "component": "flake_graph.kuzu_adapter_functional",
            "operation": "store_embedding",
            "error": str(e),
            "flake_id": flake_id
        })
        
        return QueryErrorDict(
            ok=False,
            error_type="query_execution_error",
            message=f"Failed to store embedding: {str(e)}",
            details={
                "flake_id": flake_id,
                "exception": str(e),
                "exception_type": type(e).__name__,
                "query": "UPDATE flake with embedding"
            }
        )


def get_embedding(connection: KuzuConnection, flake_id: str) -> Union[EmbeddingSuccessDict, QueryErrorDict]:
    """Get embedding data for a specific flake.
    
    Args:
        connection: KuzuDB connection
        flake_id: Identifier for the flake
        
    Returns:
        EmbeddingSuccessDict with data or QueryErrorDict on failure/not found
    """
    try:
        if not flake_id:
            return QueryErrorDict(
                ok=False,
                error_type="validation_error",
                message="Flake ID is required for getting embedding",
                details={"flake_id": flake_id}
            )
            
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
        
        result = connection['conn'].execute(query, {'path': flake_path})
        
        for row in result:
            embedding_data = EmbeddingData(
                embedding_vector=row[0],
                embedding_model=row[1] or '',
                model_version=row[2] or '',
                created_at=row[3] or '',
                content_hash=row[4] or ''
            )
            
            return EmbeddingSuccessDict(
                ok=True,
                data=embedding_data
            )
        
        # No embedding found
        return QueryErrorDict(
            ok=False,
            error_type="not_found",
            message=f"No embedding found for flake: {flake_id}",
            details={
                "flake_id": flake_id,
                "path": flake_path
            }
        )
        
    except Exception as e:
        log("ERROR", {
            "uri": "/kuzu/get_embedding",
            "message": f"Failed to get embedding for {flake_id}",
            "component": "flake_graph.kuzu_adapter_functional",
            "operation": "get_embedding",
            "error": str(e),
            "flake_id": flake_id
        })
        
        return QueryErrorDict(
            ok=False,
            error_type="query_execution_error",
            message=f"Failed to get embedding: {str(e)}",
            details={
                "flake_id": flake_id,
                "exception": str(e),
                "exception_type": type(e).__name__,
                "query": "MATCH flake embedding"
            }
        )


def get_all_embeddings(connection: KuzuConnection) -> Union[EmbeddingDictSuccessDict, QueryErrorDict]:
    """Get all stored embeddings.
    
    Args:
        connection: KuzuDB connection
        
    Returns:
        EmbeddingDictSuccessDict with data or QueryErrorDict on failure
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
        
        result = connection['conn'].execute(query)
        
        embeddings = {}
        for row in result:
            path = row[0]
            # Extract flake ID from path
            flake_id = path.split('/')[-1] if '/' in path else path
            
            embeddings[flake_id] = EmbeddingData(
                embedding_vector=row[1],
                embedding_model=row[2] or '',
                model_version=row[3] or '',
                created_at=row[4] or '',
                content_hash=row[5] or ''
            )
        
        log("INFO", {
            "uri": "/kuzu/get_all_embeddings",
            "message": f"Retrieved {len(embeddings)} embeddings from KuzuDB",
            "component": "flake_graph.kuzu_adapter_functional",
            "operation": "get_all_embeddings"
        })
        
        return EmbeddingDictSuccessDict(
            ok=True,
            data=embeddings
        )
        
    except Exception as e:
        log("ERROR", {
            "uri": "/kuzu/get_all_embeddings",
            "message": "Failed to get all embeddings",
            "component": "flake_graph.kuzu_adapter_functional",
            "operation": "get_all_embeddings",
            "error": str(e)
        })
        
        return QueryErrorDict(
            ok=False,
            error_type="query_execution_error",
            message=f"Failed to get all embeddings: {str(e)}",
            details={
                "exception": str(e),
                "exception_type": type(e).__name__,
                "query": "MATCH all flakes with embeddings"
            }
        )


# Compatibility wrapper class
class KuzuAdapter:
    """Compatibility wrapper for the functional KuzuDB adapter.
    
    This class provides backward compatibility with the original class-based API
    while using the functional implementation internally.
    """
    
    def __init__(self, db_path: Union[str, Path]):
        """Initialize KuzuDB connection and ensure schema exists.
        
        Args:
            db_path: Path to the KuzuDB database directory
            
        Raises:
            RuntimeError: If connection creation fails
        """
        self.db_path = Path(db_path)
        result = create_connection(db_path)
        
        if not result.get('ok', False):
            error_details = result.get('details', {})
            raise RuntimeError(
                f"Failed to create KuzuDB connection: {result.get('message', 'Unknown error')}. "
                f"Details: {error_details}"
            )
            
        self._connection = result['connection']
        self.db = self._connection['db']
        self.conn = self._connection['conn']
    
    def _initialize_schema(self) -> None:
        """Create the extended schema if it doesn't exist."""
        # Schema is already initialized in create_connection
        pass
    
    def create_flake(self, 
                     path: str,
                     description: str,
                     language: str,
                     vss_embedding: Optional[List[float]] = None,
                     vss_analyzed_at: Optional[datetime] = None,
                     ast_score: Optional[float] = None,
                     ast_metrics: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new flake node."""
        flake_data = FlakeData(
            path=path,
            description=description,
            language=language,
            vss_embedding=vss_embedding,
            vss_analyzed_at=vss_analyzed_at,
            ast_score=ast_score,
            ast_metrics=ast_metrics
        )
        result = create_flake(self._connection, flake_data)
        return result.get('ok', False)
    
    def read_flake(self, path: str) -> Optional[Dict[str, Any]]:
        """Read a flake node by path."""
        result = read_flake(self._connection, path)
        if result.get('ok', False):
            return dict(result['data'])
        return None
    
    def update_flake(self, path: str, **kwargs) -> bool:
        """Update a flake node with provided fields."""
        result = update_flake(self._connection, path, kwargs)
        return result.get('ok', False)
    
    def delete_flake(self, path: str) -> bool:
        """Delete a flake node."""
        result = delete_flake(self._connection, path)
        return result.get('ok', False)
    
    def list_flakes(self, 
                    language: Optional[str] = None,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all flakes with optional filtering."""
        result = list_flakes(self._connection, language, limit)
        if result.get('ok', False):
            return [dict(flake) for flake in result['data']]
        return []
    
    def find_by_embedding_similarity(self, 
                                   embedding: List[float],
                                   threshold: float = 0.8,
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """Find flakes with similar embeddings using cosine similarity."""
        result = find_by_embedding_similarity(self._connection, embedding, threshold, limit)
        if result.get('ok', False):
            return [dict(flake) for flake in result['data']]
        return []
    
    def store_embedding(self, flake_id: str, embedding_data: Dict[str, Any]) -> None:
        """Store embedding data for a flake."""
        # Convert dict to EmbeddingData
        typed_embedding = EmbeddingData(
            embedding_vector=embedding_data.get('embedding_vector', []),
            embedding_model=embedding_data.get('embedding_model', ''),
            model_version=embedding_data.get('model_version', ''),
            created_at=embedding_data.get('created_at', ''),
            content_hash=embedding_data.get('content_hash', '')
        )
        result = store_embedding(self._connection, flake_id, typed_embedding)
        if not result.get('ok', False):
            raise RuntimeError(f"Failed to store embedding: {result.get('message', 'Unknown error')}")
    
    def get_embedding(self, flake_id: str) -> Optional[Dict[str, Any]]:
        """Get embedding data for a specific flake."""
        result = get_embedding(self._connection, flake_id)
        if result.get('ok', False):
            return dict(result['data'])
        return None
    
    def get_all_embeddings(self) -> Dict[str, Dict[str, Any]]:
        """Get all stored embeddings."""
        result = get_all_embeddings(self._connection)
        if result.get('ok', False):
            return {k: dict(v) for k, v in result['data'].items()}
        return {}
    
    def close(self) -> None:
        """Close the database connection."""
        close_connection(self._connection)