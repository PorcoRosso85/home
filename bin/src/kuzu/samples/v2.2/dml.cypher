CREATE (v22:VersionState {id: "v2.2", timestamp: "2024-02-15", description: "Add notification service", change_reason: "Email/SMS notifications", progress_percentage: 0.0});
MATCH (v21:VersionState {id: "v2.1"}), (v22:VersionState {id: "v2.2"}) CREATE (v21)-[:FOLLOWS]->(v22);
CREATE (notif_api:LocationURI {id: "services/notification/api.py"});
CREATE (notif_req:RequirementEntity {id: "req_notification", title: "Notification service", description: "Email and SMS notifications", priority: "medium", requirement_type: "feature"});
MATCH (v:VersionState {id: "v2.2"}), (uri:LocationURI {id: "services/notification/api.py"}) CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);
MATCH (uri:LocationURI {id: "services/notification/api.py"}), (req:RequirementEntity {id: "req_notification"}) CREATE (uri)-[:LOCATED_WITH_REQUIREMENT {entity_type: "feature"}]->(req);
MATCH (pay:RequirementEntity {id: "req_payment"}), (notif:RequirementEntity {id: "req_notification"}) CREATE (pay)-[:DEPENDS_ON {dependency_type: "service"}]->(notif);
MATCH (notif:RequirementEntity {id: "req_notification"}), (pay:RequirementEntity {id: "req_payment"}) CREATE (notif)-[:DEPENDS_ON {dependency_type: "service"}]->(pay);