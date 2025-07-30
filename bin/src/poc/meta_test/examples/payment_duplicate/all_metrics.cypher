// Example: Payment Duplicate Prevention - All 7 Metrics
// This demonstrates how all 7 metrics apply to a real business requirement

// ============================================
// REQUIREMENT: Prevent Duplicate Payments
// ============================================

MERGE (r:RequirementEntity {id: 'req_payment_dup_001'})
SET r.title = 'Prevent Duplicate Payments',
    r.description = 'System must prevent duplicate payment processing within a 5-minute window for the same user, merchant, and amount',
    r.business_value = 'Prevents revenue loss and maintains customer trust',
    r.thresholds = '{"time_window_minutes": 5, "amount_tolerance": 0.01}';

// ============================================
// TESTS
// ============================================

// Test 1: Basic duplicate detection
MERGE (t1:TestSpecification {id: 'test_payment_dup_basic'})
SET t1.test_type = 'integration',
    t1.description = 'Verify duplicate payment is rejected within 5 minute window',
    t1.given_context = 'User has made a payment of $100 to merchant ABC',
    t1.when_action = 'User attempts identical payment after 3 minutes',
    t1.then_expected = 'Payment is rejected with duplicate error';

// Test 2: Boundary test - just before window
MERGE (t2:TestSpecification {id: 'test_payment_dup_boundary_before'})
SET t2.test_type = 'integration',
    t2.description = 'Test payment at 4:59 is rejected',
    t2.given_context = 'Payment made at time T',
    t2.when_action = 'Identical payment at T + 4:59',
    t2.then_expected = 'Payment rejected';

// Test 3: Boundary test - just after window
MERGE (t3:TestSpecification {id: 'test_payment_dup_boundary_after'})
SET t3.test_type = 'integration',
    t3.description = 'Test payment at 5:01 is accepted',
    t3.given_context = 'Payment made at time T',
    t3.when_action = 'Identical payment at T + 5:01',
    t3.then_expected = 'Payment accepted';

// Test 4: Different amount test
MERGE (t4:TestSpecification {id: 'test_payment_diff_amount'})
SET t4.test_type = 'integration',
    t4.description = 'Verify different amount payments are allowed',
    t4.given_context = 'Payment of $100 made',
    t4.when_action = 'Payment of $150 to same merchant within window',
    t4.then_expected = 'Payment accepted';

// Link tests to requirement
MATCH (r:RequirementEntity {id: 'req_payment_dup_001'})
MATCH (t:TestSpecification)
WHERE t.id IN ['test_payment_dup_basic', 'test_payment_dup_boundary_before', 
               'test_payment_dup_boundary_after', 'test_payment_diff_amount']
MERGE (r)-[:VERIFIED_BY]->(t);

// ============================================
// METRIC 1: EXISTENCE (Score: 1.0)
// ============================================

MERGE (m1:MetricValue {requirement_id: 'req_payment_dup_001', metric_name: 'existence'})
SET m1.current_value = 1.0,  // Tests exist
    m1.confidence_lower = 1.0,
    m1.confidence_upper = 1.0,
    m1.updated_at = datetime(),
    m1.data_points = 4;  // 4 tests

// ============================================
// METRIC 2: REACHABILITY (Score: 1.0)
// ============================================

MERGE (m2:MetricValue {requirement_id: 'req_payment_dup_001', metric_name: 'reachability'})
SET m2.current_value = 1.0,  // No circular dependencies
    m2.confidence_lower = 1.0,
    m2.confidence_upper = 1.0,
    m2.updated_at = datetime(),
    m2.data_points = 4;

// ============================================
// METRIC 3: BOUNDARY COVERAGE (Score: 0.83)
// ============================================

MERGE (m3:MetricValue {requirement_id: 'req_payment_dup_001', metric_name: 'boundary_coverage'})
SET m3.current_value = 0.83,  // 5/6 boundaries covered
    m3.confidence_lower = 0.8,
    m3.confidence_upper = 0.86,
    m3.updated_at = datetime(),
    m3.data_points = 6,
    m3.details = 'Covered: 4:59, 5:01, amount difference. Missing: amount tolerance boundaries';

// Missing: Test for $0.01 difference (tolerance boundary)

// ============================================
// METRIC 4: CHANGE SENSITIVITY (Score: 0.75)
// ============================================

MERGE (m4:MetricValue {requirement_id: 'req_payment_dup_001', metric_name: 'change_sensitivity'})
SET m4.current_value = 0.75,  // 3/4 changes would be detected
    m4.confidence_lower = 0.7,
    m4.confidence_upper = 0.8,
    m4.updated_at = datetime(),
    m4.data_points = 4,
    m4.details = 'Detects: time window change, amount check removal, merchant check removal. Missing: tolerance change detection';

// ============================================
// METRIC 5: SEMANTIC ALIGNMENT (Score: 0.9)
// ============================================

MERGE (m5:MetricValue {requirement_id: 'req_payment_dup_001', metric_name: 'semantic_alignment'})
SET m5.current_value = 0.9,  // High alignment between requirement and test descriptions
    m5.confidence_lower = 0.85,
    m5.confidence_upper = 0.95,
    m5.updated_at = datetime(),
    m5.data_points = 4,
    m5.details = 'Tests clearly describe duplicate payment scenarios matching requirement language';

// ============================================
// METRIC 6: RUNTIME CORRELATION (Score: 0.85)
// ============================================

MERGE (m6:MetricValue {requirement_id: 'req_payment_dup_001', metric_name: 'runtime_correlation'})
SET m6.current_value = 0.85,  // Strong correlation with operational metrics
    m6.confidence_lower = 0.75,
    m6.confidence_upper = 0.95,
    m6.updated_at = datetime(),
    m6.data_points = 180,  // 180 days of data
    m6.details = 'Strong negative correlation with duplicate_payment_rate (-0.82), positive correlation with payment_success_rate (0.78)';

// Create correlation records
MERGE (c1:Correlation {
    requirement_id: 'req_payment_dup_001',
    metric_name: 'runtime_correlation',
    correlated_with: 'duplicate_payment_rate'
})
SET c1.strength = -0.82,
    c1.p_value = 0.001,
    c1.discovered_at = datetime() - duration({days: 30});

MERGE (c2:Correlation {
    requirement_id: 'req_payment_dup_001',
    metric_name: 'runtime_correlation',
    correlated_with: 'payment_success_rate'
})
SET c2.strength = 0.78,
    c2.p_value = 0.003,
    c2.discovered_at = datetime() - duration({days: 30});

// ============================================
// METRIC 7: VALUE PROBABILITY (Score: 0.92)
// ============================================

MERGE (m7:MetricValue {requirement_id: 'req_payment_dup_001', metric_name: 'value_probability'})
SET m7.current_value = 0.92,  // High probability of business value
    m7.confidence_lower = 0.85,
    m7.confidence_upper = 0.98,
    m7.updated_at = datetime(),
    m7.data_points = 90,  // 90 days of business metrics
    m7.details = 'Prevented $125,000 in duplicate charges last quarter, reduced support tickets by 35%';

// ============================================
// SAMPLE RUNTIME DATA
// ============================================

// Test executions showing high pass rate
CREATE (e1:TestExecution {
    execution_id: 'payment_exec_001',
    requirement_id: 'req_payment_dup_001',
    test_id: 'test_payment_dup_basic',
    timestamp: datetime() - duration({hours: 12}),
    passed: true,
    duration_ms: 345,
    environment: 'prod'
});

CREATE (e2:TestExecution {
    execution_id: 'payment_exec_002',
    requirement_id: 'req_payment_dup_001',
    test_id: 'test_payment_dup_boundary_before',
    timestamp: datetime() - duration({hours: 12}),
    passed: true,
    duration_ms: 289,
    environment: 'prod'
});

// One test failure that predicted an incident
CREATE (e3:TestExecution {
    execution_id: 'payment_exec_003',
    requirement_id: 'req_payment_dup_001',
    test_id: 'test_payment_dup_basic',
    timestamp: datetime() - duration({days: 14}),
    passed: false,
    duration_ms: 1250,
    environment: 'staging'
});

// Incident that occurred after test failure
CREATE (i1:Incident {
    incident_id: 'payment_inc_001',
    timestamp: datetime() - duration({days: 13}),
    severity: 'high',
    description: 'Duplicate payments processed due to cache invalidation issue',
    resolved_at: datetime() - duration({days: 13, hours: 4}),
    root_cause: 'Redis cache TTL misconfiguration'
});

// ============================================
// RELATIONSHIPS
// ============================================

// Link all metrics to requirement
MATCH (r:RequirementEntity {id: 'req_payment_dup_001'})
MATCH (m:MetricValue {requirement_id: 'req_payment_dup_001'})
MERGE (r)-[:HAS_METRIC]->(m);

// Link correlations
MATCH (r:RequirementEntity {id: 'req_payment_dup_001'})
MATCH (c:Correlation {requirement_id: 'req_payment_dup_001'})
MERGE (r)-[:HAS_CORRELATION {strength: c.strength}]->(c);

// Link executions
MATCH (r:RequirementEntity {id: 'req_payment_dup_001'})
MATCH (e:TestExecution {requirement_id: 'req_payment_dup_001'})
MERGE (e)-[:TESTS_REQUIREMENT]->(r);

// Link incident
MATCH (r:RequirementEntity {id: 'req_payment_dup_001'})
MATCH (i:Incident {incident_id: 'payment_inc_001'})
MERGE (i)-[:IMPACTS_REQUIREMENT {impact_score: 0.9}]->(r);

// Test failure predicted incident
MATCH (e:TestExecution {execution_id: 'payment_exec_003'})
MATCH (i:Incident {incident_id: 'payment_inc_001'})
MERGE (e)-[:PREVENTS_INCIDENT {confidence: 0.8}]->(i);

// ============================================
// IMPROVEMENT SUGGESTIONS BASED ON METRICS
// ============================================

// Based on the metrics, the system would suggest:
// 1. Add test for amount tolerance boundary ($0.01 difference) - improves boundary coverage
// 2. Add mutation test for tolerance value changes - improves change sensitivity
// 3. Continue monitoring runtime correlations - maintains high value probability
// 4. Consider adding performance tests - current tests don't cover response time requirements