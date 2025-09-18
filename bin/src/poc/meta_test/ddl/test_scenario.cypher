// メタテストシステムの効果測定テストシナリオ
// ECサイト決済システムを例に価値連鎖を実証

// ============================================
// Phase 1: ビジネス要件の定義（Day 0）
// ============================================

// 決済処理の信頼性要件
CREATE (r:RequirementEntity {
    id: 'req_payment_high_availability',
    title: '決済処理の高可用性',
    description: '決済処理は99.9%の成功率を維持し、1日の売上目標1000万円を達成する',
    status: 'active'
});

// ============================================
// Phase 2: テストなしで運用開始（Day 1-7）
// ============================================

// ビジネスメトリクス：売上が不安定
CREATE (:BusinessMetric {id: 'revenue_day1', metric_name: 'daily_revenue', timestamp: '2024-01-01', value: 8000000, unit: 'JPY'});
CREATE (:BusinessMetric {id: 'revenue_day2', metric_name: 'daily_revenue', timestamp: '2024-01-02', value: 7500000, unit: 'JPY'});
CREATE (:BusinessMetric {id: 'revenue_day3', metric_name: 'daily_revenue', timestamp: '2024-01-03', value: 9000000, unit: 'JPY'});

// インシデント発生
CREATE (:Incident {
    id: 'inc_day2',
    timestamp: '2024-01-02T14:00:00Z',
    severity: 'high',
    description: '決済処理で想定外の金額によるエラー',
    business_impact: 2500000,  // 250万円の機会損失
    resolved: false
});

// メトリクス計算結果（テストなし）
CREATE (m1:MetricResult {
    id: 'metric_day7_existence',
    requirement_id: 'req_payment_high_availability',
    metric_name: 'existence',
    score: 0.0,  // テストが存在しない
    calculated_at: '2024-01-07',
    details: '{"total_tests": 0}'
});

// ============================================
// Phase 3: テスト追加（Day 8）
// ============================================

// 境界値テストを追加
CREATE (t1:TestEntity {
    id: 'test_payment_edge_cases',
    name: '決済金額境界値テスト',
    description: '0円、1円、上限額（1000万円）のテスト',
    test_type: 'unit',
    file_path: 'tests/payment/test_edge_cases.py'
});

// タイムアウトテストを追加
CREATE (t2:TestEntity {
    id: 'test_payment_timeout',
    name: '決済タイムアウトテスト',
    description: '外部API遅延時の処理',
    test_type: 'integration',
    file_path: 'tests/payment/test_timeout.py'
});

// 要件とテストを関連付け
MATCH (r:RequirementEntity {id: 'req_payment_high_availability'})
MATCH (t1:TestEntity {id: 'test_payment_edge_cases'})
CREATE (r)-[:VERIFIED_BY {verification_type: 'boundary', coverage_score: 0.90}]->(t1);

MATCH (r:RequirementEntity {id: 'req_payment_high_availability'})
MATCH (t2:TestEntity {id: 'test_payment_timeout'})
CREATE (r)-[:VERIFIED_BY {verification_type: 'reliability', coverage_score: 0.85}]->(t2);

// ============================================
// Phase 4: テスト実行でバグ発見（Day 9-10）
// ============================================

// テスト失敗：境界値バグを発見
CREATE (:TestExecution {
    id: 'exec_day9_fail',
    test_id: 'test_payment_edge_cases',
    timestamp: '2024-01-09T10:00:00Z',
    passed: false,
    error_message: '0円決済でNullPointerException'
});

// バグ修正後、テスト成功
CREATE (:TestExecution {
    id: 'exec_day10_pass',
    test_id: 'test_payment_edge_cases',
    timestamp: '2024-01-10T15:00:00Z',
    passed: true
});

// ============================================
// Phase 5: 改善後の運用（Day 11-30）
// ============================================

// 売上が安定
CREATE (:BusinessMetric {id: 'revenue_day11', metric_name: 'daily_revenue', timestamp: '2024-01-11', value: 10200000, unit: 'JPY'});
CREATE (:BusinessMetric {id: 'revenue_day12', metric_name: 'daily_revenue', timestamp: '2024-01-12', value: 10500000, unit: 'JPY'});
CREATE (:BusinessMetric {id: 'revenue_day13', metric_name: 'daily_revenue', timestamp: '2024-01-13', value: 10300000, unit: 'JPY'});

// インシデントなし（テストが防いだ）
CREATE (prevented_inc:Incident {
    id: 'inc_prevented_day15',
    timestamp: '2024-01-15T00:00:00Z',
    severity: 'high',
    description: '0円決済バグによる障害（テストにより防止）',
    business_impact: 3000000,  // 防げた損失額
    resolved: true
});

// テスト実行がインシデントを防いだ
MATCH (i:Incident {id: 'inc_prevented_day15'})
MATCH (e:TestExecution {id: 'exec_day10_pass'})
CREATE (i)-[:PREVENTED_BY {confidence: 0.95, time_window_hours: 120}]->(e);

// ============================================
// Phase 6: 効果測定（Day 30）
// ============================================

// メトリクス再計算
CREATE (m2:MetricResult {
    id: 'metric_day30_existence',
    requirement_id: 'req_payment_high_availability',
    metric_name: 'existence',
    score: 1.0,  // テストが存在
    calculated_at: '2024-01-30'
});

CREATE (m3:MetricResult {
    id: 'metric_day30_value_probability',
    requirement_id: 'req_payment_high_availability',
    metric_name: 'value_probability',
    score: 0.92,  // 高いビジネス価値貢献
    calculated_at: '2024-01-30',
    details: '{"prevented_incidents": 1, "business_impact_saved": 3000000, "revenue_improvement": 2500000}'
});

// 学習データ：ベイズ更新
CREATE (:LearningData {
    id: 'learn_day30',
    metric_name: 'value_probability',
    requirement_id: 'req_payment_high_availability',
    prior_value: 0.5,      // 初期推定
    posterior_value: 0.92, // 実績に基づく更新
    evidence_count: 20,    // 20日分のデータ
    updated_at: '2024-01-30'
});

// ============================================
// 効果測定クエリ
// ============================================

// ROI計算：テストの投資対効果
// - テスト作成コスト：50万円（2人日）
// - 防げた損失：300万円
// - 売上改善：250万円/月
// → ROI = (300万 + 250万) / 50万 = 11倍