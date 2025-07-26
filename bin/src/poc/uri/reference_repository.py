"""
ReferenceEntity Repository - グラフデータベース永続化
Based on requirement/graph's kuzu_repository.py patterns
依存: domain errors
外部依存: kuzu
"""
from typing import List, Dict, Optional, Any, Union
import os

# Error types following requirement/graph patterns
from typing import TypedDict, Literal


class DatabaseError(TypedDict):
    """Database operation error"""
    type: Literal["DatabaseError"]
    message: str
    operation: str
    database_name: Optional[str]
    error_code: Optional[str]
    details: Optional[Dict[str, Any]]


class ValidationError(TypedDict):
    """Validation error for input data"""
    type: Literal["ValidationError"]
    message: str
    field: str
    value: Any
    constraint: str
    expected: Optional[str]


class NotFoundError(TypedDict):
    """Resource not found error"""
    type: Literal["NotFoundError"]
    message: str
    resource_type: str
    resource_id: str
    search_criteria: Optional[Dict[str, Any]]


# Simple logging following the pattern
def debug(component: str, message: str, **kwargs):
    """Debug logging"""
    print(f"[DEBUG] {component}: {message}", kwargs)


def info(component: str, message: str, **kwargs):
    """Info logging"""
    print(f"[INFO] {component}: {message}", kwargs)


def create_reference_repository(db_path: str = None, existing_db=None) -> Union[Dict, Dict[str, Any]]:
    """
    Create a KuzuDB-based repository for ReferenceEntity
    
    Args:
        db_path: Database path (default: environment dependent)
                 - Test environment: ":memory:" (in-memory)
                 - Production: URI_DB_PATH or ./uri_graph.db
        existing_db: Existing database instance (for testing)
    
    Returns:
        Repository functions dictionary or error
    """
    # Import kuzu here to avoid top-level dependency
    import kuzu
    
    if existing_db:
        # Use provided database instance (for testing)
        db = existing_db
        conn = kuzu.Connection(db)
        db_path = ":memory:"  # For logging purposes
    else:
        # Default to environment variable or current directory
        if db_path is None:
            db_path = os.environ.get("URI_DB_PATH", "./uri_graph.db")
            info("uri.repo", "Using database path", db_path=db_path)
        
        debug("uri.repo", "Using database path", path=str(db_path))
        
        # Check if in-memory database
        in_memory = db_path == ":memory:"
        
        # Create database and connection
        try:
            if in_memory:
                db = kuzu.Database(database_path=":memory:")
            else:
                db = kuzu.Database(database_path=str(db_path))
            
            conn = kuzu.Connection(db)
        except Exception as e:
            return DatabaseError(
                type="DatabaseError",
                message=f"Failed to create database connection: {str(e)}",
                operation="connect",
                database_name=str(db_path),
                error_code="CONNECTION_FAILED",
                details={"error": str(e)}
            )
    
    def init_schema():
        """Initialize schema - assumes DDL is pre-applied"""
        try:
            conn.execute("MATCH (n:ReferenceEntity) RETURN count(n) LIMIT 1")
            return None  # Success
        except Exception as e:
            return DatabaseError(
                type="DatabaseError",
                message="Schema not initialized. Apply DDL first",
                operation="schema_check",
                database_name=str(db_path),
                error_code="SCHEMA_NOT_INITIALIZED",
                details={"error": str(e)}
            )
    
    # Check schema unless explicitly skipped
    if not os.environ.get("URI_SKIP_SCHEMA_CHECK"):
        schema_result = init_schema()
        if schema_result is not None:
            return schema_result
    
    def save(reference: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update a reference entity"""
        try:
            # Validate required fields
            required_fields = ["uri", "title", "entity_type"]
            for field in required_fields:
                if field not in reference:
                    return ValidationError(
                        type="ValidationError",
                        message=f"Missing required field: {field}",
                        field=field,
                        value=None,
                        constraint="required",
                        expected="Non-empty string"
                    )
            
            # Check if reference exists
            existing_check = conn.execute("""
                MATCH (r:ReferenceEntity {uri: $uri})
                RETURN r
            """, {"uri": reference["uri"]})
            
            is_new = not existing_check.has_next()
            
            if is_new:
                # Create new reference
                conn.execute("""
                    CREATE (r:ReferenceEntity {
                        uri: $uri,
                        title: $title,
                        description: $description,
                        entity_type: $entity_type,
                        metadata: $metadata,
                        created_at: current_timestamp(),
                        updated_at: current_timestamp()
                    })
                    RETURN r
                """, {
                    "uri": reference["uri"],
                    "title": reference["title"],
                    "description": reference.get("description", ""),
                    "entity_type": reference["entity_type"],
                    "metadata": reference.get("metadata", "{}")
                })
            else:
                # Update existing reference
                conn.execute("""
                    MATCH (r:ReferenceEntity {uri: $uri})
                    SET r.title = $title,
                        r.description = $description,
                        r.entity_type = $entity_type,
                        r.metadata = $metadata,
                        r.updated_at = current_timestamp()
                    RETURN r
                """, {
                    "uri": reference["uri"],
                    "title": reference["title"],
                    "description": reference.get("description", ""),
                    "entity_type": reference["entity_type"],
                    "metadata": reference.get("metadata", "{}")
                })
            
            return reference
            
        except Exception as e:
            return DatabaseError(
                type="DatabaseError",
                message=f"Failed to save reference: {str(e)}",
                operation="save",
                database_name=str(db_path),
                error_code="SAVE_FAILED",
                details={"uri": reference.get("uri"), "error": str(e)}
            )
    
    def find(uri: str) -> Dict[str, Any]:
        """Find a reference by URI"""
        try:
            result = conn.execute("""
                MATCH (r:ReferenceEntity {uri: $uri})
                RETURN r
            """, {"uri": uri})
            
            if result.has_next():
                row = result.get_next()
                node = row[0]
                
                return {
                    "uri": node["uri"],
                    "title": node["title"],
                    "description": node.get("description", ""),
                    "entity_type": node["entity_type"],
                    "metadata": node.get("metadata", "{}"),
                    "created_at": node.get("created_at"),
                    "updated_at": node.get("updated_at")
                }
            
            return NotFoundError(
                type="NotFoundError",
                message=f"Reference {uri} not found",
                resource_type="reference",
                resource_id=uri,
                search_criteria={"uri": uri}
            )
            
        except Exception as e:
            return DatabaseError(
                type="DatabaseError",
                message=f"Failed to find reference: {str(e)}",
                operation="find",
                database_name=str(db_path),
                error_code="FIND_FAILED",
                details={"uri": uri, "error": str(e)}
            )
    
    def find_all() -> List[Dict[str, Any]]:
        """Get all references"""
        try:
            result = conn.execute("""
                MATCH (r:ReferenceEntity)
                RETURN r
                ORDER BY r.created_at DESC
            """)
            
            references = []
            while result.has_next():
                row = result.get_next()
                node = row[0]
                
                references.append({
                    "uri": node["uri"],
                    "title": node["title"],
                    "description": node.get("description", ""),
                    "entity_type": node["entity_type"],
                    "metadata": node.get("metadata", "{}"),
                    "created_at": node.get("created_at"),
                    "updated_at": node.get("updated_at")
                })
            
            return references
            
        except Exception:
            return []
    
    def add_implementation(source_uri: str, target_uri: str, 
                          implementation_type: str = "implements",
                          confidence: float = 1.0) -> Dict:
        """Add IMPLEMENTS relationship between references"""
        try:
            # Validate URIs exist
            for uri in [source_uri, target_uri]:
                check = conn.execute("""
                    MATCH (r:ReferenceEntity {uri: $uri})
                    RETURN count(r) > 0
                """, {"uri": uri})
                
                if not check.has_next() or not check.get_next()[0]:
                    return NotFoundError(
                        type="NotFoundError",
                        message=f"Reference {uri} not found",
                        resource_type="reference",
                        resource_id=uri,
                        search_criteria={"uri": uri}
                    )
            
            # Check if relationship already exists
            existing_rel = conn.execute("""
                MATCH (source:ReferenceEntity {uri: $source_uri})
                      -[rel:IMPLEMENTS]->
                      (target:ReferenceEntity {uri: $target_uri})
                RETURN rel
            """, {
                "source_uri": source_uri,
                "target_uri": target_uri
            })
            
            if not existing_rel.has_next():
                # Create relationship
                conn.execute("""
                    MATCH (source:ReferenceEntity {uri: $source_uri})
                    MATCH (target:ReferenceEntity {uri: $target_uri})
                    CREATE (source)-[:IMPLEMENTS {
                        implementation_type: $type,
                        confidence: $confidence,
                        created_at: current_timestamp()
                    }]->(target)
                    RETURN source, target
                """, {
                    "source_uri": source_uri,
                    "target_uri": target_uri,
                    "type": implementation_type,
                    "confidence": confidence
                })
            
            return {
                "success": True,
                "source": source_uri,
                "target": target_uri,
                "relationship": "IMPLEMENTS"
            }
            
        except Exception as e:
            return DatabaseError(
                type="DatabaseError",
                message=f"Failed to add implementation: {str(e)}",
                operation="add_implementation",
                database_name=str(db_path),
                error_code="IMPLEMENTATION_FAILED",
                details={
                    "source_uri": source_uri,
                    "target_uri": target_uri,
                    "error": str(e)
                }
            )
    
    def find_implementations(uri: str, direction: str = "outgoing") -> List[Dict]:
        """Find implementation relationships for a reference
        
        Args:
            uri: The reference URI
            direction: "outgoing" (this implements others) or "incoming" (others implement this)
        """
        try:
            if direction == "outgoing":
                # Find what this reference implements
                query = """
                    MATCH (source:ReferenceEntity {uri: $uri})
                          -[rel:IMPLEMENTS]->
                          (target:ReferenceEntity)
                    RETURN target, rel
                    ORDER BY rel.created_at DESC
                """
            else:
                # Find what implements this reference
                query = """
                    MATCH (source:ReferenceEntity)
                          -[rel:IMPLEMENTS]->
                          (target:ReferenceEntity {uri: $uri})
                    RETURN source, rel
                    ORDER BY rel.created_at DESC
                """
            
            result = conn.execute(query, {"uri": uri})
            
            implementations = []
            while result.has_next():
                row = result.get_next()
                node = row[0]
                rel = row[1]
                
                implementations.append({
                    "reference": {
                        "uri": node["uri"],
                        "title": node["title"],
                        "description": node.get("description", ""),
                        "entity_type": node["entity_type"]
                    },
                    "relationship": {
                        "type": rel.get("implementation_type", "implements"),
                        "confidence": rel.get("confidence", 1.0),
                        "created_at": rel.get("created_at")
                    }
                })
            
            return implementations
            
        except Exception:
            return []
    
    def search(query: str) -> List[Dict[str, Any]]:
        """Search references by text in title or description"""
        try:
            result = conn.execute("""
                MATCH (r:ReferenceEntity)
                WHERE r.title CONTAINS $query OR r.description CONTAINS $query
                RETURN r
                ORDER BY r.created_at DESC
            """, {"query": query})
            
            references = []
            while result.has_next():
                row = result.get_next()
                node = row[0]
                
                references.append({
                    "uri": node["uri"],
                    "title": node["title"],
                    "description": node.get("description", ""),
                    "entity_type": node["entity_type"],
                    "metadata": node.get("metadata", "{}"),
                    "created_at": node.get("created_at"),
                    "updated_at": node.get("updated_at")
                })
            
            return references
            
        except Exception:
            return []
    
    def execute(query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a Cypher query"""
        try:
            result = conn.execute(query, parameters)
            data = []
            while result.has_next():
                data.append(result.get_next())
            return {"data": data, "status": "success"}
        except Exception as e:
            return DatabaseError(
                type="DatabaseError",
                message=f"Query execution failed: {str(e)}",
                operation="execute",
                database_name=str(db_path),
                error_code="QUERY_FAILED",
                details={"query": query[:200], "error": str(e)}
            )
    
    return {
        "save": save,
        "find": find,
        "find_all": find_all,
        "add_implementation": add_implementation,
        "find_implementations": find_implementations,
        "search": search,
        "db": db,  # For testing
        "connection": conn,  # For direct access
        "execute": execute  # For custom queries
    }