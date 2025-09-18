// Sample Data for Meta-Test POC
// Demonstrates the value chain: Test → Requirement → Business Impact

// ============================================
// Step 1: Create Requirements (from base schema)
// ============================================

CREATE (r1:RequirementEntity {
    id: 'req_payment_reliability',
    title: '決済処理の信頼性',
    description: '決済処理は99.9%の成功率を維持し、エラー時は適切にリトライする',
    status: 'active'
});

CREATE (r2:RequirementEntity {
    id: 'req_user_auth',
    title: 'ユーザー認証',
    description: 'ユーザーは安全に認証され、セッションは適切に管理される',
    status: 'active'
});

// ============================================
// Step 2: Create Tests
// ============================================

CREATE (t1:TestEntity {
    id: 'test_payment_boundary',
    name: '決済境界値テスト',
    description: '決済金額の上限・下限をテスト',
    test_type: 'unit',
    file_path: 'tests/payment/test_boundary.py'
});

CREATE (t2:TestEntity {
    id: 'test_payment_retry',
    name: '決済リトライテスト',
    description: 'エラー時のリトライロジックをテスト',
    test_type: 'integration',
    file_path: 'tests/payment/test_retry.py'
});

CREATE (t3:TestEntity {
    id: 'test_auth_session',
    name: 'セッション管理テスト',
    description: 'セッションの作成・検証・破棄をテスト',
    test_type: 'integration',
    file_path: 'tests/auth/test_session.py'
});

// ============================================
// Step 3: Link Tests to Requirements
// ============================================

MATCH (r1:RequirementEntity {id: 'req_payment_reliability'})
MATCH (t1:TestEntity {id: 'test_payment_boundary'})
CREATE (r1)-[:VERIFIED_BY {verification_type: 'boundary', coverage_score: 0.85}]->(t1);

MATCH (r1:RequirementEntity {id: 'req_payment_reliability'})
MATCH (t2:TestEntity {id: 'test_payment_retry'})
CREATE (r1)-[:VERIFIED_BY {verification_type: 'behavior', coverage_score: 0.90}]->(t2);

MATCH (r2:RequirementEntity {id: 'req_user_auth'})
MATCH (t3:TestEntity {id: 'test_auth_session'})
CREATE (r2)-[:VERIFIED_BY {verification_type: 'behavior', coverage_score: 0.75}]->(t3);

// ============================================
// Step 4: Create Test Executions
// ============================================

// Successful executions
CREATE (:TestExecution {
    id: 'exec_001',
    test_id: 'test_payment_boundary',
    timestamp: '2024-01-30T10:00:00Z',
    passed: true,
    duration_ms: 150
});

CREATE (:TestExecution {
    id: 'exec_002',
    test_id: 'test_payment_retry',
    timestamp: '2024-01-30T10:05:00Z',
    passed: true,
    duration_ms: 2500
});

// Failed execution (detected issue)
CREATE (:TestExecution {
    id: 'exec_003',
    test_id: 'test_payment_boundary',
    timestamp: '2024-01-29T15:00:00Z',
    passed: false,
    duration_ms: 180,
    error_message: 'Boundary check failed for amount > 1000000'
});

// ============================================
// Step 5: Create Business Metrics
// ============================================

// Daily revenue metrics
CREATE (:BusinessMetric {
    id: 'revenue_20240130',
    metric_name: 'daily_revenue',
    timestamp: '2024-01-30T23:59:59Z',
    value: 5000000,
    unit: 'JPY'
});

CREATE (:BusinessMetric {
    id: 'revenue_20240129',
    metric_name: 'daily_revenue',
    timestamp: '2024-01-29T23:59:59Z',
    value: 4800000,
    unit: 'JPY'
});

// Payment success rate
CREATE (:BusinessMetric {
    id: 'payment_success_20240130',
    metric_name: 'payment_success_rate',
    timestamp: '2024-01-30T23:59:59Z',
    value: 99.8,
    unit: 'percentage'
});

// ============================================
// Step 6: Create Incidents
// ============================================

// Incident that was prevented by test
CREATE (i1:Incident {
    id: 'inc_001',
    timestamp: '2024-01-29T18:00:00Z',
    severity: 'high',
    description: '決済処理で境界値エラーによる障害の可能性を検出',
    business_impact: 500000,
    resolved: true
});

// ============================================
// Step 7: Link Business Impact
// ============================================

// Requirement impacts business metrics
MATCH (r:RequirementEntity {id: 'req_payment_reliability'})
MATCH (m:BusinessMetric {metric_name: 'daily_revenue'})
CREATE (r)-[:IMPACTS {impact_type: 'revenue', correlation_strength: 0.85}]->(m);

MATCH (r:RequirementEntity {id: 'req_payment_reliability'})
MATCH (m:BusinessMetric {metric_name: 'payment_success_rate'})
CREATE (r)-[:IMPACTS {impact_type: 'reliability', correlation_strength: 0.95}]->(m);

// Test execution prevented incident
MATCH (i:Incident {id: 'inc_001'})
MATCH (e:TestExecution {id: 'exec_003'})
CREATE (i)-[:PREVENTED_BY {confidence: 0.9, time_window_hours: 3}]->(e);

// ============================================
// Step 8: Create Metric Results
// ============================================

// Metric results for req_payment_reliability
CREATE (m1:MetricResult {
    id: 'metric_001',
    requirement_id: 'req_payment_reliability',
    metric_name: 'existence',
    score: 1.0,
    calculated_at: '2024-01-31T00:00:00Z',
    details: '{"total_tests": 2, "test_types": ["unit", "integration"]}'
});

CREATE (m2:MetricResult {
    id: 'metric_002',
    requirement_id: 'req_payment_reliability',
    metric_name: 'boundary_coverage',
    score: 0.85,
    calculated_at: '2024-01-31T00:00:00Z',
    details: '{"boundaries_tested": 3, "boundaries_total": 4}'
});

CREATE (m3:MetricResult {
    id: 'metric_003',
    requirement_id: 'req_payment_reliability',
    metric_name: 'value_probability',
    score: 0.88,
    calculated_at: '2024-01-31T00:00:00Z',
    details: '{"prevented_incidents": 1, "business_impact_saved": 500000}'
});

// Link metrics to requirements
MATCH (r:RequirementEntity {id: 'req_payment_reliability'})
MATCH (m:MetricResult {requirement_id: 'req_payment_reliability'})
CREATE (r)-[:HAS_METRIC {is_current: true}]->(m);

// ============================================
// Step 9: Learning Data
// ============================================

CREATE (:LearningData {
    id: 'learn_001',
    metric_name: 'value_probability',
    requirement_id: 'req_payment_reliability',
    prior_value: 0.5,
    posterior_value: 0.88,
    evidence_count: 10,
    updated_at: '2024-01-31T00:00:00Z'
});