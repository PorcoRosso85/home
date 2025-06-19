-- v2.2: Notification Service Addition (2024-02-15)
-- Create version node
CREATE (v22:VersionState {id: "v2.2", timestamp: "2024-02-15", description: "Add notification service", progress_percentage: 0.0});

-- Create version relationship
MATCH (v21:VersionState {id: "v2.1"}), (v22:VersionState {id: "v2.2"}) 
CREATE (v21)-[:FOLLOWS]->(v22);

-- Create location nodes for notification service components
CREATE (notif_api:LocationURI {id: "services/notification/api.py"});

-- Create requirement nodes
CREATE (notif_req:RequirementEntity {id: "req_notification", title: "Notification service", priority: "medium", requirement_type: "feature", resource: "queue"});
CREATE (queue_req:RequirementEntity {id: "req_rabbitmq", title: "RabbitMQ", priority: "high", requirement_type: "infrastructure", resource: "queue"});
CREATE (email_req:RequirementEntity {id: "req_sendgrid", title: "SendGrid API", priority: "medium", requirement_type: "library", resource: null});
CREATE (sms_req:RequirementEntity {id: "req_twilio", title: "Twilio SDK", priority: "low", requirement_type: "library", resource: null});

-- Create relationships between version and locations
MATCH (v:VersionState {id: "v2.2"}), (uri:LocationURI {id: "services/notification/api.py"})
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);

-- Create relationships between locations and requirements
MATCH (uri:LocationURI {id: "services/notification/api.py"}), (req:RequirementEntity {id: "req_notification"})
CREATE (uri)-[:LOCATED_WITH_REQUIREMENT]->(req);

-- Create dependency relationships
MATCH (notif:RequirementEntity {id: "req_notification"}), (auth:RequirementEntity {id: "req_auth"}) 
CREATE (notif)-[:DEPENDS_ON {dependency_type: "service"}]->(auth);
MATCH (notif:RequirementEntity {id: "req_notification"}), (queue:RequirementEntity {id: "req_rabbitmq"})
CREATE (notif)-[:DEPENDS_ON {dependency_type: "infrastructure"}]->(queue);
MATCH (notif:RequirementEntity {id: "req_notification"}), (email:RequirementEntity {id: "req_sendgrid"})
CREATE (notif)-[:DEPENDS_ON {dependency_type: "library"}]->(email);
MATCH (notif:RequirementEntity {id: "req_notification"}), (sms:RequirementEntity {id: "req_twilio"})
CREATE (notif)-[:DEPENDS_ON {dependency_type: "library"}]->(sms);

-- Payment service depends on notification
MATCH (pay:RequirementEntity {id: "req_payment"}), (notif:RequirementEntity {id: "req_notification"}) 
CREATE (pay)-[:DEPENDS_ON {dependency_type: "service"}]->(notif);