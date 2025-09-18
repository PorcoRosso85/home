CREATE (v201:VersionState {id: "v2.0.1", timestamp: "2024-01-20", description: "Infrastructure setup", change_reason: "Resolve missing dependencies", progress_percentage: 0.0});
MATCH (v20:VersionState {id: "v2.0"}), (v201:VersionState {id: "v2.0.1"}) CREATE (v20)-[:FOLLOWS]->(v201);
CREATE (db_config:LocationURI {id: "infrastructure/database/config.yaml"});
CREATE (jwt_config:LocationURI {id: "infrastructure/auth/jwt_config.py"});
MATCH (v:VersionState {id: "v2.0.1"}), (uri:LocationURI {id: "infrastructure/database/config.yaml"}) CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);
MATCH (v:VersionState {id: "v2.0.1"}), (uri:LocationURI {id: "infrastructure/auth/jwt_config.py"}) CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);
MATCH (uri:LocationURI {id: "infrastructure/database/config.yaml"}), (req:RequirementEntity {id: "req_postgres"}) CREATE (uri)-[:LOCATED_WITH_REQUIREMENT {entity_type: "infrastructure"}]->(req);
MATCH (uri:LocationURI {id: "infrastructure/auth/jwt_config.py"}), (req:RequirementEntity {id: "req_jwt"}) CREATE (uri)-[:LOCATED_WITH_REQUIREMENT {entity_type: "library"}]->(req);