// 階層違反の例：タスクレベル（Level 4）がビジョンレベル（Level 0）に依存

// タスクレベルの要件を作成
CREATE (task:RequirementEntity {
    id: 'req_exec_task_001',
    title: 'ダッシュボード実装タスク',
    description: 'エグゼクティブ向けダッシュボードの実装',
    priority: 100,
    requirement_type: 'functional',
    status: 'proposed'
})

// ビジョンレベルの要件を作成
CREATE (vision:RequirementEntity {
    id: 'req_exec_vision_new_001',
    title: '経営見える化ビジョン',
    description: 'リアルタイムで経営状況を可視化する',
    priority: 255,
    requirement_type: 'strategic',
    status: 'proposed'
})

// 階層違反: タスク（下位）がビジョン（上位）に依存
CREATE (task)-[:DEPENDS_ON {dependency_type: 'requires', reason: '実装にビジョンが必要'}]->(vision)