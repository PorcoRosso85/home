// エグゼクティブ視点の要件定義
// 階層レベル: 0 (Vision) - 最上位のビジョン・戦略レベル

// 1. ROI（投資対効果）に関するビジョン要件
CREATE (roi_vision:RequirementEntity {
    id: 'req_exec_roi_vision_001',
    title: 'ROI最大化ビジョン',
    description: 'すべての開発投資において、定量的なROI測定とその最大化を実現する',
    priority: 255,
    requirement_type: 'strategic',
    status: 'proposed',
    verification_required: true,
    implementation_details: '{"measurement_methods": ["NPV", "IRR", "Payback Period"], "target_roi": "300%", "measurement_cycle": "quarterly"}',
    acceptance_criteria: 'すべてのプロジェクトでROI測定が可能で、目標ROIを達成すること'
})
CREATE (loc_roi:LocationURI {id: 'loc://vision/executive/roi_001'})
CREATE (loc_roi)-[:LOCATES {entity_type: 'requirement'}]->(roi_vision)

// 2. 戦略的アライメントに関するビジョン要件
CREATE (align_vision:RequirementEntity {
    id: 'req_exec_alignment_vision_001',
    title: '戦略的アライメントビジョン',
    description: '全社戦略と技術戦略の完全な整合性を実現し、ビジネス価値を最大化する',
    priority: 250,
    requirement_type: 'strategic',
    status: 'proposed',
    verification_required: true,
    implementation_details: '{"alignment_areas": ["business_strategy", "technology_roadmap", "talent_development"], "review_cycle": "monthly"}',
    acceptance_criteria: '全プロジェクトが企業戦略と整合し、戦略的価値を創出すること'
})
CREATE (loc_align:LocationURI {id: 'loc://vision/executive/alignment_001'})
CREATE (loc_align)-[:LOCATES {entity_type: 'requirement'}]->(align_vision)

// 3. リスク管理に関するビジョン要件
CREATE (risk_vision:RequirementEntity {
    id: 'req_exec_risk_vision_001',
    title: 'プロアクティブリスク管理ビジョン',
    description: '予防的リスク管理により、プロジェクトリスクを最小化し、成功確率を最大化する',
    priority: 245,
    requirement_type: 'strategic',
    status: 'proposed',
    verification_required: true,
    implementation_details: '{"risk_categories": ["technical", "financial", "operational", "compliance"], "mitigation_strategies": "proactive"}',
    acceptance_criteria: 'リスクの早期発見と予防的対策により、重大インシデントをゼロにすること'
})
CREATE (loc_risk:LocationURI {id: 'loc://vision/executive/risk_001'})
CREATE (loc_risk)-[:LOCATES {entity_type: 'requirement'}]->(risk_vision)

// ビジョン要件間の依存関係（同レベルなので依存関係なし）
EOF < /dev/null
