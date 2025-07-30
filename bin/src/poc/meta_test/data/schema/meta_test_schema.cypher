// Meta-Test System Schema Definition
// Extends the existing requirement/graph schema with meta-test capabilities

// ============================================
// NODES
// ============================================

// MetricValue node - stores metric calculation results
// Each requirement can have multiple metric values (one per metric type)
CREATE CONSTRAINT metric_value_unique IF NOT EXISTS
ON (m:MetricValue) ASSERT (m.requirement_id, m.metric_name) IS UNIQUE;

// Properties for MetricValue:
// - requirement_id: STRING (references RequirementEntity.id)
// - metric_name: STRING (one of: existence, reachability, boundary_coverage, 
//                        change_sensitivity, semantic_alignment, 
//                        runtime_correlation, value_probability)
// - current_value: FLOAT (0.0 to 1.0)
// - previous_value: FLOAT (0.0 to 1.0, optional)
// - confidence_lower: FLOAT (lower bound of confidence interval)
// - confidence_upper: FLOAT (upper bound of confidence interval)
// - updated_at: DATETIME
// - data_points: INTEGER (number of data points used in calculation)

// Correlation node - discovered correlations between metrics and outcomes
CREATE CONSTRAINT correlation_unique IF NOT EXISTS
ON (c:Correlation) ASSERT (c.requirement_id, c.metric_name, c.correlated_with) IS UNIQUE;

// Properties for Correlation:
// - requirement_id: STRING
// - metric_name: STRING
// - correlated_with: STRING (e.g., "cpu_usage", "revenue", "incident_rate")
// - strength: FLOAT (-1.0 to 1.0)
// - p_value: FLOAT (statistical significance)
// - discovered_at: DATETIME

// TestExecution node - runtime test execution history
CREATE CONSTRAINT test_execution_unique IF NOT EXISTS
ON (e:TestExecution) ASSERT e.execution_id IS UNIQUE;

// Properties for TestExecution:
// - execution_id: STRING (unique identifier)
// - requirement_id: STRING
// - test_id: STRING
// - timestamp: DATETIME
// - passed: BOOLEAN
// - duration_ms: INTEGER
// - environment: STRING (e.g., "dev", "staging", "prod")

// Incident node - production incidents
CREATE CONSTRAINT incident_unique IF NOT EXISTS
ON (i:Incident) ASSERT i.incident_id IS UNIQUE;

// Properties for Incident:
// - incident_id: STRING
// - timestamp: DATETIME
// - severity: STRING (low, medium, high, critical)
// - description: STRING
// - resolved_at: DATETIME (optional)
// - root_cause: STRING (optional)

// ============================================
// RELATIONSHIPS
// ============================================

// Requirement has metric values
// (RequirementEntity)-[:HAS_METRIC]->(MetricValue)

// Metric value updates over time (creates history chain)
// (MetricValue)-[:METRIC_UPDATE {timestamp, old_value, new_value}]->(RequirementEntity)

// Requirement has correlations
// (RequirementEntity)-[:HAS_CORRELATION {strength}]->(Correlation)

// Test execution relates to requirement
// (TestExecution)-[:TESTS_REQUIREMENT]->(RequirementEntity)

// Test execution relates to specific test
// (TestExecution)-[:EXECUTES_TEST]->(TestSpecification)

// Incident relates to requirements
// (Incident)-[:IMPACTS_REQUIREMENT {impact_score}]->(RequirementEntity)

// Test execution may prevent incident
// (TestExecution)-[:PREVENTS_INCIDENT {confidence}]->(Incident)

// ============================================
// INDEXES for Performance
// ============================================

CREATE INDEX metric_value_lookup IF NOT EXISTS
FOR (m:MetricValue) ON (m.requirement_id);

CREATE INDEX metric_value_by_name IF NOT EXISTS
FOR (m:MetricValue) ON (m.metric_name);

CREATE INDEX test_execution_by_req IF NOT EXISTS
FOR (e:TestExecution) ON (e.requirement_id);

CREATE INDEX test_execution_by_time IF NOT EXISTS
FOR (e:TestExecution) ON (e.timestamp);

CREATE INDEX incident_by_time IF NOT EXISTS
FOR (i:Incident) ON (i.timestamp);

CREATE INDEX incident_by_severity IF NOT EXISTS
FOR (i:Incident) ON (i.severity);

// ============================================
// EXAMPLE QUERIES
// ============================================

// Get all metrics for a requirement
/*
MATCH (r:RequirementEntity {id: 'req_001'})-[:HAS_METRIC]->(m:MetricValue)
RETURN m.metric_name, m.current_value, m.confidence_lower, m.confidence_upper
ORDER BY m.metric_name;
*/

// Get metric history for a specific metric
/*
MATCH (r:RequirementEntity {id: 'req_001'})<-[u:METRIC_UPDATE]-(m:MetricValue {metric_name: 'runtime_correlation'})
RETURN u.timestamp, u.old_value, u.new_value
ORDER BY u.timestamp DESC
LIMIT 10;
*/

// Find requirements with poor test quality
/*
MATCH (r:RequirementEntity)-[:HAS_METRIC]->(m:MetricValue)
WHERE m.current_value < 0.7
RETURN r.id, r.title, COLLECT({metric: m.metric_name, score: m.current_value}) as poor_metrics
ORDER BY SIZE(poor_metrics) DESC;
*/

// Analyze test execution patterns before incidents
/*
MATCH (i:Incident)-[:IMPACTS_REQUIREMENT]->(r:RequirementEntity)
MATCH (e:TestExecution)-[:TESTS_REQUIREMENT]->(r)
WHERE e.timestamp > (i.timestamp - duration({hours: 24})) 
  AND e.timestamp < i.timestamp
RETURN i.incident_id, i.severity, 
       COLLECT({test_id: e.test_id, passed: e.passed, hours_before: duration.between(e.timestamp, i.timestamp).hours}) as test_results
ORDER BY i.timestamp DESC;
*/