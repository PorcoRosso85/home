// エグゼクティブ視点の要件定義
// 階層レベル: 1 (Architecture) - アーキテクチャレベル

// 4. コンプライアンスアーキテクチャ要件
CREATE (compliance_arch:RequirementEntity {
    id: 'req_exec_compliance_arch_001',
    title: 'コンプライアンスアーキテクチャ',
    description: '法規制要件を自動的に満たすアーキテクチャを構築し、コンプライアンスリスクをゼロにする',
    priority: 240,
    requirement_type: 'regulatory',
    status: 'proposed',
    verification_required: true,
    implementation_details: '{"regulations": ["GDPR", "SOX", "HIPAA"], "audit_trail": "automatic", "compliance_check": "continuous"}',
    acceptance_criteria: '全システムが自動的にコンプライアンス要件を満たし、監査証跡が完全であること',
    technical_specifications: '{"audit_log_retention": "7_years", "encryption": "AES-256", "access_control": "RBAC"}'
})
CREATE (loc_compliance:LocationURI {id: 'loc://architecture/executive/compliance_001'})
CREATE (loc_compliance)-[:LOCATES {entity_type: 'requirement'}]->(compliance_arch)

// 5. 予算管理アーキテクチャ要件
CREATE (budget_arch:RequirementEntity {
    id: 'req_exec_budget_arch_001',
    title: '予算最適化アーキテクチャ',
    description: 'リアルタイムの予算追跡と最適化により、プロジェクト予算の効率的な配分を実現する',
    priority: 235,
    requirement_type: 'financial',
    status: 'proposed',
    verification_required: true,
    implementation_details: '{"tracking_granularity": "daily", "optimization_algorithm": "dynamic_programming", "alert_thresholds": [80, 90, 95]}',
    acceptance_criteria: '予算消化率をリアルタイムで追跡し、予算超過を事前に防止できること',
    technical_specifications: '{"integration": ["ERP", "Project_Management_Tools"], "reporting": "real-time_dashboard"}'
})
CREATE (loc_budget:LocationURI {id: 'loc://architecture/executive/budget_001'})
CREATE (loc_budget)-[:LOCATES {entity_type: 'requirement'}]->(budget_arch)

// 6. リソース管理アーキテクチャ要件
CREATE (resource_arch:RequirementEntity {
    id: 'req_exec_resource_arch_001',
    title: 'リソース最適化アーキテクチャ',
    description: '人的リソースの最適配置により、プロジェクト効率を最大化する',
    priority: 230,
    requirement_type: 'operational',
    status: 'proposed',
    verification_required: true,
    implementation_details: '{"resource_types": ["developers", "designers", "managers"], "optimization_criteria": ["skills", "availability", "cost"]}',
    acceptance_criteria: 'リソース利用率を95%以上に維持し、スキルマッチングが最適化されること',
    technical_specifications: '{"ai_matching": "skill_based", "capacity_planning": "predictive"}'
})
CREATE (loc_resource:LocationURI {id: 'loc://architecture/executive/resource_001'})
CREATE (loc_resource)-[:LOCATES {entity_type: 'requirement'}]->(resource_arch)

// ビジョン要件への依存関係（アーキテクチャはビジョンに依存）
// 取得したビジョン要件
MATCH (roi_vision:RequirementEntity {id: 'req_exec_roi_vision_001'})
MATCH (align_vision:RequirementEntity {id: 'req_exec_alignment_vision_001'})
MATCH (risk_vision:RequirementEntity {id: 'req_exec_risk_vision_001'})

// アーキテクチャ要件を取得
MATCH (compliance_arch:RequirementEntity {id: 'req_exec_compliance_arch_001'})
MATCH (budget_arch:RequirementEntity {id: 'req_exec_budget_arch_001'})
MATCH (resource_arch:RequirementEntity {id: 'req_exec_resource_arch_001'})

// 依存関係を作成（アーキテクチャ → ビジョン）
CREATE (compliance_arch)-[:DEPENDS_ON {dependency_type: 'requires', reason: 'コンプライアンスはリスク管理ビジョンの実現に必要'}]->(risk_vision)
CREATE (budget_arch)-[:DEPENDS_ON {dependency_type: 'requires', reason: '予算管理はROI最大化ビジョンの実現に必要'}]->(roi_vision)
CREATE (resource_arch)-[:DEPENDS_ON {dependency_type: 'requires', reason: 'リソース最適化は戦略的アライメントの実現に必要'}]->(align_vision)