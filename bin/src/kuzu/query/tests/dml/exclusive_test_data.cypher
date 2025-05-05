// 排他的関係テスト用データ

// 1. 要件エンティティの作成
CREATE (req1:RequirementEntity {id: 'REQ-001', title: '未関連付け要件', description: 'どのエンティティとも関連付けられていない要件', priority: 'HIGH'});
CREATE (req2:RequirementEntity {id: 'REQ-002', title: 'コード実装済み要件', description: 'コードと関連付けられた要件', priority: 'MEDIUM'});
CREATE (req3:RequirementEntity {id: 'REQ-003', title: '検証済み要件', description: '検証と関連付けられた要件', priority: 'LOW'});

// 2. コードエンティティの作成
CREATE (code1:CodeEntity {persistent_id: 'CODE-001', name: 'TestImplementation', type: 'class'});

// 3. 検証エンティティの作成
CREATE (ver1:RequirementVerification {id: 'TEST-001', name: '基本検証', description: '基本機能の検証'});
CREATE (ver2:RequirementVerification {id: 'TEST-002', name: '追加検証', description: '追加のテストケース'});

// 4. 初期関係の設定
// REQ-002とCODE-001を関連付け
MATCH (r:RequirementEntity {id: 'REQ-002'}), (c:CodeEntity {persistent_id: 'CODE-001'})
CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'IMPLEMENTS'}]->(c);

// REQ-003とTEST-001を関連付け
MATCH (r:RequirementEntity {id: 'REQ-003'}), (v:RequirementVerification {id: 'TEST-001'})
CREATE (r)-[:VERIFIED_BY]->(v);
