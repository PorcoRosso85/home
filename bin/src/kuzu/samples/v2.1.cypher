-- v2.1: Payment Service Addition (2024-02-01)
-- Create version node
CREATE (v21:VersionState {id: "v2.1", timestamp: "2024-02-01", description: "Add payment service", progress_percentage: 0.0});

-- Create version relationship
MATCH (v20:VersionState {id: "v2.0"}), (v21:VersionState {id: "v2.1"}) 
CREATE (v20)-[:FOLLOWS]->(v21);

-- Create location nodes for payment service components  
CREATE (pay_api:LocationURI {id: "services/payment/api.py"});
CREATE (pay_webhook:LocationURI {id: "services/payment/webhook.py"});

-- Create requirement nodes
CREATE (pay_req:RequirementEntity {id: "req_payment", title: "Payment service", priority: "high", requirement_type: "feature", resource: "payment_db"});
CREATE (stripe_req:RequirementEntity {id: "req_stripe", title: "Stripe SDK", priority: "high", requirement_type: "library", resource: null});
CREATE (webhook_req:RequirementEntity {id: "req_webhook", title: "Webhook handler", priority: "medium", requirement_type: "feature", resource: null});

-- Create relationships between version and locations
MATCH (v:VersionState {id: "v2.1"}), (uri:LocationURI {id: "services/payment/api.py"}) 
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);
MATCH (v:VersionState {id: "v2.1"}), (uri:LocationURI {id: "services/payment/webhook.py"}) 
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);

-- Create relationships between locations and requirements
MATCH (uri:LocationURI {id: "services/payment/api.py"}), (req:RequirementEntity {id: "req_payment"}) 
CREATE (uri)-[:LOCATED_WITH_REQUIREMENT]->(req);
MATCH (uri:LocationURI {id: "services/payment/webhook.py"}), (req:RequirementEntity {id: "req_webhook"}) 
CREATE (uri)-[:LOCATED_WITH_REQUIREMENT]->(req);

-- Create dependency relationships
MATCH (pay:RequirementEntity {id: "req_payment"}), (auth:RequirementEntity {id: "req_auth"}) 
CREATE (pay)-[:DEPENDS_ON {dependency_type: "service"}]->(auth);
MATCH (pay:RequirementEntity {id: "req_payment"}), (stripe:RequirementEntity {id: "req_stripe"}) 
CREATE (pay)-[:DEPENDS_ON {dependency_type: "library"}]->(stripe);