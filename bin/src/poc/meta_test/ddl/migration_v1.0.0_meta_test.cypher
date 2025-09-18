// Meta-Test System Migration DDL for KuzuDB
// Version: 1.0.0
// Description: Extends requirement/graph schema for test quality metrics
// Base Schema: requirement/graph v3.4.0 (Cypher format)

// ============================================
// PHASE 1: Test Entity and Basic Relationships
// ============================================

// Test entity representing a test case/suite
CREATE NODE TABLE IF NOT EXISTS TestEntity (
    id STRING PRIMARY KEY,
    name STRING,
    description STRING,
    test_type STRING DEFAULT 'unit',  // unit, integration, e2e
    file_path STRING,
    // For future search integration
    embedding DOUBLE[256]
);

// Test execution results
CREATE NODE TABLE IF NOT EXISTS TestExecution (
    id STRING PRIMARY KEY,
    test_id STRING,
    timestamp STRING,
    passed BOOLEAN,
    duration_ms INT64,
    error_message STRING
);

// Relationship: Requirement verified by tests
CREATE REL TABLE IF NOT EXISTS VERIFIED_BY (
    FROM RequirementEntity TO TestEntity,
    verification_type STRING DEFAULT 'behavior',  // behavior, boundary, performance
    coverage_score DOUBLE DEFAULT 0.0
);

// Relationship: Test depends on other tests
CREATE REL TABLE IF NOT EXISTS TEST_DEPENDS_ON (
    FROM TestEntity TO TestEntity,
    dependency_type STRING DEFAULT 'setup'  // setup, data, sequence
);

// ============================================
// PHASE 2: Business Impact Tracking
// ============================================

// Incident tracking for value correlation
CREATE NODE TABLE IF NOT EXISTS Incident (
    id STRING PRIMARY KEY,
    timestamp STRING,
    severity STRING,  // low, medium, high, critical
    description STRING,
    business_impact DOUBLE,  // Monetary impact in base currency
    resolved BOOLEAN DEFAULT false
);

// Business metrics for correlation
CREATE NODE TABLE IF NOT EXISTS BusinessMetric (
    id STRING PRIMARY KEY,
    metric_name STRING,
    timestamp STRING,
    value DOUBLE,
    unit STRING  // percentage, currency, count
);

// Relationship: Test execution prevented incident
CREATE REL TABLE IF NOT EXISTS PREVENTED_BY (
    FROM Incident TO TestExecution,
    confidence DOUBLE DEFAULT 0.5,  // Confidence in prevention correlation
    time_window_hours INT32 DEFAULT 24
);

// Relationship: Requirement impacts business metric
CREATE REL TABLE IF NOT EXISTS IMPACTS (
    FROM RequirementEntity TO BusinessMetric,
    impact_type STRING,  // revenue, cost, satisfaction
    correlation_strength DOUBLE DEFAULT 0.0
);

// ============================================
// PHASE 3: Meta-Test Metrics Storage
// ============================================

// Stores calculated metric results
CREATE NODE TABLE IF NOT EXISTS MetricResult (
    id STRING PRIMARY KEY,
    requirement_id STRING,
    metric_name STRING,  // existence, reachability, etc.
    score DOUBLE,
    calculated_at STRING,
    details STRING  // JSON string for flexible details
);

// Learning data for Bayesian updates
CREATE NODE TABLE IF NOT EXISTS LearningData (
    id STRING PRIMARY KEY,
    metric_name STRING,
    requirement_id STRING,
    prior_value DOUBLE,
    posterior_value DOUBLE,
    evidence_count INT32,
    updated_at STRING
);

// Relationship: Metric results for requirements
CREATE REL TABLE IF NOT EXISTS HAS_METRIC (
    FROM RequirementEntity TO MetricResult,
    is_current BOOLEAN DEFAULT true
);

// ============================================
// PHASE 4: Improvement Tracking
// ============================================

// Improvement suggestions and their outcomes
CREATE NODE TABLE IF NOT EXISTS Improvement (
    id STRING PRIMARY KEY,
    requirement_id STRING,
    metric_name STRING,
    suggestion STRING,
    effort_estimate STRING,  // low, medium, high
    impact_estimate DOUBLE,
    status STRING DEFAULT 'pending',  // pending, implemented, rejected
    created_at STRING,
    completed_at STRING
);

// Relationship: Improvement affects metric
CREATE REL TABLE IF NOT EXISTS IMPROVES (
    FROM Improvement TO MetricResult,
    before_score DOUBLE,
    after_score DOUBLE,
    actual_impact DOUBLE
);

// ============================================
// VIEWS for Analysis (if supported by KuzuDB)
// ============================================

// View: Test coverage by requirement
// (Pseudo-SQL, adjust for KuzuDB syntax)
// CREATE VIEW requirement_test_coverage AS
// MATCH (r:RequirementEntity)-[v:VERIFIED_BY]->(t:TestEntity)
// RETURN r.id, COUNT(t) as test_count, AVG(v.coverage_score) as avg_coverage;

// View: Business value by test
// MATCH (t:TestEntity)<-[:VERIFIED_BY]-(r:RequirementEntity)-[:IMPACTS]->(m:BusinessMetric)
// RETURN t.id, SUM(m.value) as total_business_value;

// ============================================
// INDEXES for Performance
// ============================================

// CREATE INDEX idx_test_execution_timestamp ON TestExecution(timestamp);
// CREATE INDEX idx_metric_result_requirement ON MetricResult(requirement_id);
// CREATE INDEX idx_incident_timestamp ON Incident(timestamp);
// CREATE INDEX idx_business_metric_timestamp ON BusinessMetric(timestamp);