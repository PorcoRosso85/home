// 階層型トレーサビリティモデル - 動く設計書関連クエリ

// 設計書のためのデータを作成
// @name: create_living_documentation_data
// プロジェクトコンテキストを作成
CREATE (project:ProjectContext {
  id: 'PROJ-001',
  name: 'サンプルプロジェクト',
  description: 'トレーサビリティモデルのサンプルプロジェクト',
  start_date: '2024-01-01',
  version: '1.0.0'
})

// 設計書セクションを作成
CREATE (section1:DocumentationSection {
  id: 'DOC-SECTION-001',
  title: 'システム概要',
  order: 1,
  description: 'システム全体の概要と目的',
  last_updated: '2024-05-01'
})

CREATE (section2:DocumentationSection {
  id: 'DOC-SECTION-002',
  title: '認証機能',
  order: 2,
  description: 'ユーザー認証に関する機能の説明',
  last_updated: '2024-05-01'
})

CREATE (section3:DocumentationSection {
  id: 'DOC-SECTION-003',
  title: 'データモデル',
  order: 3,
  description: 'システムのデータモデルの説明',
  last_updated: '2024-05-01'
})

// プロジェクトとセクションの関連付け
CREATE (project)-[:HAS_SECTION]->(section1)
CREATE (project)-[:HAS_SECTION]->(section2)
CREATE (project)-[:HAS_SECTION]->(section3)

// 要件の作成
CREATE (req1:RequirementEntity {
  id: 'REQ-DOC-001',
  title: 'ユーザー認証要件',
  description: 'ユーザーはメールアドレスとパスワードで認証できること',
  priority: 'high',
  requirement_type: 'functional',
  status: 'completed'
})

CREATE (req2:RequirementEntity {
  id: 'REQ-DOC-002',
  title: 'ユーザー管理要件',
  description: '管理者はユーザーの追加・編集・削除ができること',
  priority: 'high',
  requirement_type: 'functional',
  status: 'in_progress'
})

CREATE (req3:RequirementEntity {
  id: 'REQ-DOC-003',
  title: 'パスワードポリシー要件',
  description: 'パスワードは8文字以上で、大文字・小文字・数字・記号を含むこと',
  priority: 'medium',
  requirement_type: 'security',
  status: 'completed'
})

// コードエンティティの作成
CREATE (code1:CodeEntity {
  persistent_id: 'CODE-DOC-001',
  name: 'AuthenticationService',
  type: 'class',
  signature: 'class AuthenticationService',
  complexity: 7,
  start_position: 100,
  end_position: 1000
})

CREATE (code2:CodeEntity {
  persistent_id: 'CODE-DOC-002',
  name: 'UserManagementService',
  type: 'class',
  signature: 'class UserManagementService',
  complexity: 8,
  start_position: 1100,
  end_position: 2000
})

CREATE (code3:CodeEntity {
  persistent_id: 'CODE-DOC-003',
  name: 'PasswordValidator',
  type: 'class',
  signature: 'class PasswordValidator',
  complexity: 5,
  start_position: 2100,
  end_position: 3000
})

// 要件とコードの関連付け
CREATE (req1)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code1)
CREATE (req2)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code2)
CREATE (req3)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code3)
CREATE (req1)-[:IS_IMPLEMENTED_BY {implementation_type: 'support'}]->(code3)

// 設計書セクションと要件の関連付け
CREATE (section2)-[:DOCUMENTS_REQUIREMENT]->(req1)
CREATE (section2)-[:DOCUMENTS_REQUIREMENT]->(req2)
CREATE (section2)-[:DOCUMENTS_REQUIREMENT]->(req3)

// コード例と図を含むドキュメント部品
CREATE (codeSample:DocumentationComponent {
  id: 'DOC-COMP-001',
  title: '認証コードサンプル',
  content_type: 'code_sample',
  content: '```java\npublic class AuthenticationService {\n  public boolean authenticate(String username, String password) {\n    // 認証ロジック\n    return true;\n  }\n}\n```',
  order: 1
})

CREATE (diagram:DocumentationComponent {
  id: 'DOC-COMP-002',
  title: '認証シーケンス図',
  content_type: 'diagram',
  content: '```mermaid\nsequenceDiagram\n  Client->>Server: Login Request\n  Server->>AuthService: Authenticate\n  AuthService->>Database: Verify Credentials\n  Database-->>AuthService: Credentials Valid\n  AuthService-->>Server: Authentication Success\n  Server-->>Client: Send Token\n```',
  order: 2
})

// セクションと部品の関連付け
CREATE (section2)-[:HAS_COMPONENT]->(codeSample)
CREATE (section2)-[:HAS_COMPONENT]->(diagram)

// ドキュメント部品とコードの関連付け
CREATE (codeSample)-[:REFERS_TO_CODE]->(code1)
CREATE (diagram)-[:REFERS_TO_CODE]->(code1)

// テスト（検証）の作成
CREATE (test1:RequirementVerification {
  id: 'TEST-DOC-001',
  name: 'ユーザー認証テスト',
  description: 'ユーザー認証機能の単体テスト',
  verification_type: 'unit_test'
})

CREATE (test2:RequirementVerification {
  id: 'TEST-DOC-002',
  name: 'パスワード検証テスト',
  description: 'パスワードポリシーの検証テスト',
  verification_type: 'unit_test'
})

// 要件とテストの関連付け
CREATE (req1)-[:VERIFIED_BY]->(test1)
CREATE (req3)-[:VERIFIED_BY]->(test2)

// セクションとテストの関連付け
CREATE (section2)-[:DOCUMENTS_VERIFICATION]->(test1)
CREATE (section2)-[:DOCUMENTS_VERIFICATION]->(test2)

RETURN 
  count(DISTINCT r:RequirementEntity) AS created_requirements,
  count(DISTINCT c:CodeEntity) AS created_code,
  count(DISTINCT t:RequirementVerification) AS created_tests,
  count(DISTINCT s:DocumentationSection) AS created_sections,
  count(DISTINCT dc:DocumentationComponent) AS created_components;

// 特定のプロジェクトの設計書セクションを取得
// @name: get_project_documentation_sections
MATCH (p:ProjectContext {id: $projectId})-[:HAS_SECTION]->(s:DocumentationSection)
RETURN 
  s.id AS section_id,
  s.title AS section_title,
  s.description AS section_description,
  s.order AS section_order,
  s.last_updated AS last_updated
ORDER BY s.order;

// 設計書セクションの詳細と関連コンポーネントを取得
// @name: get_section_content
MATCH (s:DocumentationSection {id: $sectionId})
OPTIONAL MATCH (s)-[:HAS_COMPONENT]->(c:DocumentationComponent)
WITH s, c
ORDER BY c.order

RETURN 
  s.id AS section_id,
  s.title AS section_title,
  s.description AS section_description,
  s.last_updated AS last_updated,
  collect({
    id: c.id,
    title: c.title,
    content_type: c.content_type,
    content: c.content,
    order: c.order
  }) AS components;

// 特定のセクションが文書化している要件を取得
// @name: get_section_requirements
MATCH (s:DocumentationSection {id: $sectionId})-[:DOCUMENTS_REQUIREMENT]->(r:RequirementEntity)
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
WITH s, r, collect(DISTINCT c.name) AS implementations

RETURN 
  s.id AS section_id,
  s.title AS section_title,
  r.id AS requirement_id,
  r.title AS requirement_title,
  r.description AS requirement_description,
  r.priority AS requirement_priority,
  r.status AS requirement_status,
  implementations
ORDER BY r.priority, r.id;

// 特定のセクションが文書化しているテストを取得
// @name: get_section_verifications
MATCH (s:DocumentationSection {id: $sectionId})-[:DOCUMENTS_VERIFICATION]->(v:RequirementVerification)
OPTIONAL MATCH (v)-[:VERIFICATION_IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r:RequirementEntity)-[:VERIFIED_BY]->(v)
WITH s, v, collect(DISTINCT c.name) AS implementations, collect(DISTINCT r.id) AS requirement_ids

RETURN 
  s.id AS section_id,
  s.title AS section_title,
  v.id AS verification_id,
  v.name AS verification_name,
  v.description AS verification_description,
  v.verification_type AS verification_type,
  implementations,
  requirement_ids
ORDER BY v.id;

// コードの変更による設計書セクションの特定（修正が必要なドキュメントを特定）
// @name: identify_affected_documentation
MATCH (c:CodeEntity {persistent_id: $codeId})

// コードサンプルを通じて参照しているセクション
OPTIONAL MATCH (c)<-[:REFERS_TO_CODE]-(comp:DocumentationComponent)<-[:HAS_COMPONENT]-(s1:DocumentationSection)

// 要件を通じて関連するセクション
OPTIONAL MATCH (c)<-[:IS_IMPLEMENTED_BY]-(r:RequirementEntity)<-[:DOCUMENTS_REQUIREMENT]-(s2:DocumentationSection)

// テストを通じて関連するセクション
OPTIONAL MATCH (c)<-[:VERIFICATION_IS_IMPLEMENTED_BY]-(v:RequirementVerification)<-[:DOCUMENTS_VERIFICATION]-(s3:DocumentationSection)

WITH 
  c,
  collect(DISTINCT s1) AS direct_sections,
  collect(DISTINCT s2) AS requirement_sections,
  collect(DISTINCT s3) AS verification_sections

RETURN 
  c.persistent_id AS code_id,
  c.name AS code_name,
  [section IN direct_sections | {id: section.id, title: section.title, reason: 'direct_reference'}] AS direct_references,
  [section IN requirement_sections | {id: section.id, title: section.title, reason: 'via_requirement'}] AS requirement_references,
  [section IN verification_sections | {id: section.id, title: section.title, reason: 'via_verification'}] AS verification_references;

// 要件の変更による設計書セクションの特定
// @name: identify_affected_sections_by_requirement
MATCH (r:RequirementEntity {id: $requirementId})

// 直接文書化しているセクション
OPTIONAL MATCH (r)<-[:DOCUMENTS_REQUIREMENT]-(s1:DocumentationSection)

// 検証を通じて関連するセクション
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(v:RequirementVerification)<-[:DOCUMENTS_VERIFICATION]-(s2:DocumentationSection)

WITH 
  r,
  collect(DISTINCT s1) AS direct_sections,
  collect(DISTINCT s2) AS verification_sections

RETURN 
  r.id AS requirement_id,
  r.title AS requirement_title,
  [section IN direct_sections | {id: section.id, title: section.title, reason: 'direct_documentation'}] AS direct_references,
  [section IN verification_sections | {id: section.id, title: section.title, reason: 'via_verification'}] AS verification_references;

// ドキュメントの依存関係を分析（どのドキュメントが最も多くの要素に依存しているか）
// @name: analyze_documentation_dependencies
MATCH (s:DocumentationSection)

// 要件への依存
OPTIONAL MATCH (s)-[:DOCUMENTS_REQUIREMENT]->(r:RequirementEntity)

// 検証への依存
OPTIONAL MATCH (s)-[:DOCUMENTS_VERIFICATION]->(v:RequirementVerification)

// コンポーネントを通じたコードへの依存
OPTIONAL MATCH (s)-[:HAS_COMPONENT]->(comp:DocumentationComponent)-[:REFERS_TO_CODE]->(c:CodeEntity)

WITH 
  s,
  count(DISTINCT r) AS requirement_dependencies,
  count(DISTINCT v) AS verification_dependencies,
  count(DISTINCT c) AS code_dependencies

RETURN 
  s.id AS section_id,
  s.title AS section_title,
  requirement_dependencies,
  verification_dependencies,
  code_dependencies,
  requirement_dependencies + verification_dependencies + code_dependencies AS total_dependencies
ORDER BY total_dependencies DESC;

// 整合性チェック - ドキュメントの更新が必要な要素を特定
// @name: check_documentation_consistency
// ドキュメントで言及されていない要件を検出
MATCH (r:RequirementEntity)
WHERE NOT EXISTS { MATCH (s:DocumentationSection)-[:DOCUMENTS_REQUIREMENT]->(r) }

WITH collect(r) AS undocumented_requirements

// ドキュメントで言及されていないテストを検出
MATCH (v:RequirementVerification)
WHERE NOT EXISTS { MATCH (s:DocumentationSection)-[:DOCUMENTS_VERIFICATION]->(v) }

WITH undocumented_requirements, collect(v) AS undocumented_verifications

// 古いドキュメント（最終更新から30日以上経過）を検出
MATCH (s:DocumentationSection)
WHERE datetime(s.last_updated) < datetime() - duration('P30D')

WITH undocumented_requirements, undocumented_verifications, collect(s) AS outdated_sections

// 要件は実装されているがドキュメントで言及されていないコードを検出
MATCH (c:CodeEntity)<-[:IS_IMPLEMENTED_BY]-(r:RequirementEntity)<-[:DOCUMENTS_REQUIREMENT]-(s:DocumentationSection)
WHERE NOT EXISTS { MATCH (s)-[:HAS_COMPONENT]->(:DocumentationComponent)-[:REFERS_TO_CODE]->(c) }

RETURN 
  [req IN undocumented_requirements | {id: req.id, title: req.title}] AS undocumented_requirements,
  [v IN undocumented_verifications | {id: v.id, name: v.name}] AS undocumented_verifications,
  [s IN outdated_sections | {id: s.id, title: s.title, last_updated: s.last_updated}] AS outdated_sections,
  count(DISTINCT c) AS undocumented_code_count;