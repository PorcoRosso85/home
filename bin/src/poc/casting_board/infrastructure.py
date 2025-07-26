"""Infrastructure layer for KuzuDB integration."""

from typing import Union, List, Optional
import kuzu
from .domain import ResourceDict, ErrorDict


def create_in_memory_database() -> kuzu.Database:
    """Create an in-memory KuzuDB database."""
    return kuzu.Database(":memory:")


class ResourceRepository:
    """Repository for Resource entities using KuzuDB."""
    
    def __init__(self, database: kuzu.Database):
        self.db = database
        self.conn = kuzu.Connection(database)
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Initialize the graph schema for resources."""
        # Create node tables
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Resource (
                id STRING,
                name STRING,
                resource_type STRING,
                PRIMARY KEY (id)
            )
        """)
        
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Capability (
                name STRING,
                PRIMARY KEY (name)
            )
        """)
        
        # Create relationship tables
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS HAS_CAPABILITY (
                FROM Resource TO Capability,
                level INT64
            )
        """)
    
    def save(self, resource: ResourceDict) -> Union[ResourceDict, ErrorDict]:
        """Save or update a resource in the graph database."""
        try:
            # Check if resource exists
            result = self.conn.execute(
                "MATCH (r:Resource {id: $id}) RETURN r",
                {"id": resource["id"]}
            )
            
            if result.has_next():
                # Update existing resource
                self.conn.execute("""
                    MATCH (r:Resource {id: $id})
                    SET r.name = $name, r.resource_type = $resource_type
                """, {
                    "id": resource["id"],
                    "name": resource["name"],
                    "resource_type": resource["resource_type"]
                })
            else:
                # Create new resource
                self.conn.execute("""
                    CREATE (r:Resource {
                        id: $id,
                        name: $name,
                        resource_type: $resource_type
                    })
                """, {
                    "id": resource["id"],
                    "name": resource["name"],
                    "resource_type": resource["resource_type"]
                })
            
            # Update capabilities
            # First, remove existing capabilities
            self.conn.execute("""
                MATCH (r:Resource {id: $id})-[h:HAS_CAPABILITY]->(c:Capability)
                DELETE h
            """, {"id": resource["id"]})
            
            # Then add current capabilities
            for capability in resource["capabilities"]:
                # Ensure capability node exists
                self.conn.execute("""
                    MERGE (c:Capability {name: $name})
                """, {"name": capability["name"]})
                
                # Create relationship
                self.conn.execute("""
                    MATCH (r:Resource {id: $resource_id})
                    MATCH (c:Capability {name: $capability_name})
                    CREATE (r)-[:HAS_CAPABILITY {level: $level}]->(c)
                """, {
                    "resource_id": resource["id"],
                    "capability_name": capability["name"],
                    "level": capability["level"]
                })
            
            return resource
            
        except Exception as e:
            return ErrorDict(
                type="BusinessRuleError",
                message=f"Failed to save resource: {str(e)}",
                field=None
            )
    
    def find_by_id(self, resource_id: str) -> Optional[ResourceDict]:
        """Find a resource by its ID."""
        # Find resource node
        result = self.conn.execute("""
            MATCH (r:Resource {id: $id})
            RETURN r.id, r.name, r.resource_type
        """, {"id": resource_id})
        
        if not result.has_next():
            return None
        
        row = result.get_next()
        resource = ResourceDict(
            id=row[0],
            name=row[1],
            resource_type=row[2],
            capabilities=[],
            availability=[]
        )
        
        # Find capabilities
        cap_result = self.conn.execute("""
            MATCH (r:Resource {id: $id})-[h:HAS_CAPABILITY]->(c:Capability)
            RETURN c.name, h.level
        """, {"id": resource_id})
        
        while cap_result.has_next():
            cap_row = cap_result.get_next()
            resource["capabilities"].append({
                "name": cap_row[0],
                "level": cap_row[1]
            })
        
        return resource
    
    def find_by_capability(self, capability_name: str, minimum_level: int = 0) -> List[ResourceDict]:
        """Find resources that have a specific capability at minimum level."""
        result = self.conn.execute("""
            MATCH (r:Resource)-[h:HAS_CAPABILITY]->(c:Capability {name: $capability_name})
            WHERE h.level >= $minimum_level
            RETURN r.id, r.name, r.resource_type, h.level
        """, {
            "capability_name": capability_name,
            "minimum_level": minimum_level
        })
        
        resources = []
        resource_ids = set()
        
        while result.has_next():
            row = result.get_next()
            resource_id = row[0]
            
            if resource_id not in resource_ids:
                resource_ids.add(resource_id)
                # Get full resource details
                full_resource = self.find_by_id(resource_id)
                if full_resource:
                    resources.append(full_resource)
        
        return resources
    
    def get_schema(self) -> dict:
        """Get the current graph schema."""
        # For now, return our known schema
        # KuzuDB's schema introspection API varies by version
        return {
            "nodes": ["Resource", "Capability"],
            "relationships": ["HAS_CAPABILITY"]
        }