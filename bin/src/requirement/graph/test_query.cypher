CREATE (r:RequirementEntity {
    id: 'req_test_friction_001',
    title: 'ユーザーフレンドリーな検索機能',
    description: '使いやすい検索を実装',
    priority: 'critical'
})
CREATE (loc:LocationURI {id: 'loc://vision/search/test_001'})
CREATE (loc)-[:LOCATES]->(r)