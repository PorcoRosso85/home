// Initial baseline values for meta-test metrics
// This file sets up initial metric values for existing requirements

// ============================================
// BASELINE METRIC VALUES
// ============================================

// Assuming we have some existing requirements, create baseline metrics
// In practice, these would be calculated by running the metric calculations

// Example requirement: User Authentication
MERGE (r1:RequirementEntity {id: 'req_auth_001'})
SET r1.title = 'User Authentication',
    r1.description = 'Users must be able to authenticate using username and password with proper security measures';

// Create baseline metrics for req_auth_001
MERGE (m1:MetricValue {requirement_id: 'req_auth_001', metric_name: 'existence'})
SET m1.current_value = 1.0,
    m1.confidence_lower = 1.0,
    m1.confidence_upper = 1.0,
    m1.updated_at = datetime(),
    m1.data_points = 1;

MERGE (m2:MetricValue {requirement_id: 'req_auth_001', metric_name: 'reachability'})
SET m2.current_value = 1.0,
    m2.confidence_lower = 1.0,
    m2.confidence_upper = 1.0,
    m2.updated_at = datetime(),
    m2.data_points = 1;

MERGE (m3:MetricValue {requirement_id: 'req_auth_001', metric_name: 'boundary_coverage'})
SET m3.current_value = 0.75,
    m3.confidence_lower = 0.7,
    m3.confidence_upper = 0.8,
    m3.updated_at = datetime(),
    m3.data_points = 4;

MERGE (m4:MetricValue {requirement_id: 'req_auth_001', metric_name: 'change_sensitivity'})
SET m4.current_value = 0.6,
    m4.confidence_lower = 0.5,
    m4.confidence_upper = 0.7,
    m4.updated_at = datetime(),
    m4.data_points = 5;

MERGE (m5:MetricValue {requirement_id: 'req_auth_001', metric_name: 'semantic_alignment'})
SET m5.current_value = 0.85,
    m5.confidence_lower = 0.8,
    m5.confidence_upper = 0.9,
    m5.updated_at = datetime(),
    m5.data_points = 3;

// Runtime metrics start with neutral values
MERGE (m6:MetricValue {requirement_id: 'req_auth_001', metric_name: 'runtime_correlation'})
SET m6.current_value = 0.5,
    m6.confidence_lower = 0.2,
    m6.confidence_upper = 0.8,
    m6.updated_at = datetime(),
    m6.data_points = 0;

MERGE (m7:MetricValue {requirement_id: 'req_auth_001', metric_name: 'value_probability'})
SET m7.current_value = 0.5,
    m7.confidence_lower = 0.2,
    m7.confidence_upper = 0.8,
    m7.updated_at = datetime(),
    m7.data_points = 0;

// Create relationships
MATCH (r:RequirementEntity {id: 'req_auth_001'})
MATCH (m:MetricValue {requirement_id: 'req_auth_001'})
MERGE (r)-[:HAS_METRIC]->(m);

// ============================================
// EXAMPLE TEST DATA
// ============================================

// Create test specifications
MERGE (t1:TestSpecification {id: 'test_auth_login'})
SET t1.test_type = 'integration',
    t1.description = 'Test user login with valid credentials';

MERGE (t2:TestSpecification {id: 'test_auth_lockout'})
SET t2.test_type = 'integration',
    t2.description = 'Test account lockout after failed attempts';

// Link tests to requirement
MATCH (r:RequirementEntity {id: 'req_auth_001'})
MATCH (t1:TestSpecification {id: 'test_auth_login'})
MATCH (t2:TestSpecification {id: 'test_auth_lockout'})
MERGE (r)-[:VERIFIED_BY]->(t1)
MERGE (r)-[:VERIFIED_BY]->(t2);

// ============================================
// SAMPLE EXECUTION HISTORY
// ============================================

// Create some test execution history
CREATE (e1:TestExecution {
    execution_id: 'exec_001',
    requirement_id: 'req_auth_001',
    test_id: 'test_auth_login',
    timestamp: datetime() - duration({days: 7}),
    passed: true,
    duration_ms: 234,
    environment: 'dev'
});

CREATE (e2:TestExecution {
    execution_id: 'exec_002',
    requirement_id: 'req_auth_001',
    test_id: 'test_auth_login',
    timestamp: datetime() - duration({days: 6}),
    passed: true,
    duration_ms: 189,
    environment: 'dev'
});

CREATE (e3:TestExecution {
    execution_id: 'exec_003',
    requirement_id: 'req_auth_001',
    test_id: 'test_auth_lockout',
    timestamp: datetime() - duration({days: 5}),
    passed: false,
    duration_ms: 567,
    environment: 'dev'
});

// Link executions
MATCH (r:RequirementEntity {id: 'req_auth_001'})
MATCH (e:TestExecution {requirement_id: 'req_auth_001'})
MERGE (e)-[:TESTS_REQUIREMENT]->(r);

MATCH (t:TestSpecification {id: 'test_auth_login'})
MATCH (e:TestExecution {test_id: 'test_auth_login'})
MERGE (e)-[:EXECUTES_TEST]->(t);

MATCH (t:TestSpecification {id: 'test_auth_lockout'})
MATCH (e:TestExecution {test_id: 'test_auth_lockout'})
MERGE (e)-[:EXECUTES_TEST]->(t);

// ============================================
// SAMPLE INCIDENT
// ============================================

CREATE (i1:Incident {
    incident_id: 'inc_001',
    timestamp: datetime() - duration({days: 4}),
    severity: 'medium',
    description: 'Users unable to login due to authentication service timeout',
    resolved_at: datetime() - duration({days: 4, hours: 2})
});

// Link incident to requirement
MATCH (r:RequirementEntity {id: 'req_auth_001'})
MATCH (i:Incident {incident_id: 'inc_001'})
MERGE (i)-[:IMPACTS_REQUIREMENT {impact_score: 0.7}]->(r);

// The failed test might have predicted this incident
MATCH (e:TestExecution {execution_id: 'exec_003'})
MATCH (i:Incident {incident_id: 'inc_001'})
WHERE e.timestamp < i.timestamp
MERGE (e)-[:PREVENTS_INCIDENT {confidence: 0.6}]->(i);