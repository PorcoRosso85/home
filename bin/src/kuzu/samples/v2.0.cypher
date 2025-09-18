-- v2.0: Basic Authentication Service (2024-01-15)
-- Create version node
CREATE (v20:VersionState {id: "v2.0", timestamp: "2024-01-15", description: "Basic auth service", progress_percentage: 0.0});

-- Create location nodes for auth service components
CREATE (auth_api:LocationURI {id: "services/auth/api.py"});
CREATE (auth_db:LocationURI {id: "services/auth/models.py"});

-- Create requirement nodes
CREATE (auth_req:RequirementEntity {id: "req_auth", title: "Authentication service", priority: "high", requirement_type: "feature", resource: "user_db"});
CREATE (db_req:RequirementEntity {id: "req_postgres", title: "PostgreSQL database", priority: "high", requirement_type: "infrastructure", resource: "user_db"});
CREATE (jwt_req:RequirementEntity {id: "req_jwt", title: "JWT library", priority: "high", requirement_type: "library", resource: null});

-- Create relationships between version and locations
MATCH (v:VersionState {id: "v2.0"}), (uri:LocationURI {id: "services/auth/api.py"}) 
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);
MATCH (v:VersionState {id: "v2.0"}), (uri:LocationURI {id: "services/auth/models.py"}) 
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);

-- Create relationships between locations and requirements
MATCH (uri:LocationURI {id: "services/auth/api.py"}), (req:RequirementEntity {id: "req_auth"}) 
CREATE (uri)-[:LOCATED_WITH_REQUIREMENT]->(req);

-- Create dependency relationships
MATCH (auth:RequirementEntity {id: "req_auth"}), (db:RequirementEntity {id: "req_postgres"}) 
CREATE (auth)-[:DEPENDS_ON {dependency_type: "infrastructure"}]->(db);
MATCH (auth:RequirementEntity {id: "req_auth"}), (jwt:RequirementEntity {id: "req_jwt"}) 
CREATE (auth)-[:DEPENDS_ON {dependency_type: "library"}]->(jwt);