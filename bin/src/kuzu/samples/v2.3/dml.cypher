CREATE (v23:VersionState {id: "v2.3", timestamp: "2024-03-01", description: "Add analytics service", progress_percentage: 0.0});
MATCH (v22:VersionState {id: "v2.2"}), (v23:VersionState {id: "v2.3"}) CREATE (v22)-[:FOLLOWS]->(v23);
CREATE (analytics_api:LocationURI {id: "services/analytics/api.py"});
CREATE (analytics_req:RequirementEntity {id: "req_analytics", title: "Analytics service", priority: "low", requirement_type: "feature", resource: "analytics_db"});
MATCH (v:VersionState {id: "v2.3"}), (uri:LocationURI {id: "services/analytics/api.py"}) CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);
MATCH (uri:LocationURI {id: "services/analytics/api.py"}), (req:RequirementEntity {id: "req_analytics"}) CREATE (uri)-[:LOCATED_WITH_REQUIREMENT]->(req);
MATCH (analytics:RequirementEntity {id: "req_analytics"}), (auth:RequirementEntity {id: "req_auth"}) CREATE (analytics)-[:DEPENDS_ON {dependency_type: "service"}]->(auth);
MATCH (analytics:RequirementEntity {id: "req_analytics"}), (pay:RequirementEntity {id: "req_payment"}) CREATE (analytics)-[:DEPENDS_ON {dependency_type: "service"}]->(pay);
MATCH (analytics:RequirementEntity {id: "req_analytics"}), (notif:RequirementEntity {id: "req_notification"}) CREATE (analytics)-[:DEPENDS_ON {dependency_type: "service"}]->(notif);