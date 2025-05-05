// プロジェクト要件と関連オブジェクトのテストデータ

// @name: create_project_requirements
// モジュール定義
CREATE (modSystem:LocationURI {
  uri_id: 'system',
  scheme: 'component',
  path: 'system',
  authority: 'project'
})

CREATE (modAuth:LocationURI {
  uri_id: 'auth-module',
  scheme: 'component',
  path: 'system/auth',
  authority: 'project'
})

CREATE (modUser:LocationURI {
  uri_id: 'user-module',
  scheme: 'component',
  path: 'system/user',
  authority: 'project'
})

CREATE (modAdmin:LocationURI {
  uri_id: 'admin-module',
  scheme: 'component',
  path: 'system/admin',
  authority: 'project'
})

// モジュール階層を設定
CREATE (modSystem)-[:CONTAINS_LOCATION {relation_type: 'component'}]->(modAuth)
CREATE (modSystem)-[:CONTAINS_LOCATION {relation_type: 'component'}]->(modUser)
CREATE (modSystem)-[:CONTAINS_LOCATION {relation_type: 'component'}]->(modAdmin)

// 認証モジュールの要件
CREATE (req1:RequirementEntity {
  id: 'REQ-AUTH-001',
  title: 'ユーザーログイン機能',
  description: 'ユーザー名とパスワードによるログイン機能',
  priority: 'high',
  requirement_type: 'functional'
})

CREATE (req2:RequirementEntity {
  id: 'REQ-AUTH-002',
  title: 'パスワードリセット機能',
  description: 'ユーザーがパスワードをリセットできる機能',
  priority: 'medium',
  requirement_type: 'functional'
})

CREATE (req3:RequirementEntity {
  id: 'REQ-AUTH-003',
  title: '二要素認証機能',
  description: '二要素認証によるセキュリティ強化',
  priority: 'medium',
  requirement_type: 'functional'
})

// ユーザーモジュールの要件
CREATE (req4:RequirementEntity {
  id: 'REQ-USER-001',
  title: 'ユーザー登録機能',
  description: '新規ユーザーの登録処理',
  priority: 'high',
  requirement_type: 'functional'
})

CREATE (req5:RequirementEntity {
  id: 'REQ-USER-002',
  title: 'ユーザープロファイル編集',
  description: 'ユーザーが自身のプロファイルを編集できる機能',
  priority: 'medium',
  requirement_type: 'functional'
})

CREATE (req6:RequirementEntity {
  id: 'REQ-USER-003',
  title: 'ユーザー検索機能',
  description: 'ユーザーの検索機能',
  priority: 'low',
  requirement_type: 'functional'
})

// 管理モジュールの要件
CREATE (req7:RequirementEntity {
  id: 'REQ-ADMIN-001',
  title: 'ユーザー管理機能',
  description: '管理者によるユーザー管理機能',
  priority: 'high',
  requirement_type: 'functional'
})

CREATE (req8:RequirementEntity {
  id: 'REQ-ADMIN-002',
  title: 'システム設定管理',
  description: '管理者によるシステム設定管理',
  priority: 'medium',
  requirement_type: 'functional'
})

CREATE (req9:RequirementEntity {
  id: 'REQ-ADMIN-003',
  title: 'ログ管理機能',
  description: '管理者によるシステムログ管理',
  priority: 'low',
  requirement_type: 'functional'
})

// モジュールと要件の関連付け
CREATE (req1)-[:REQUIREMENT_HAS_LOCATION]->(modAuth)
CREATE (req2)-[:REQUIREMENT_HAS_LOCATION]->(modAuth)
CREATE (req3)-[:REQUIREMENT_HAS_LOCATION]->(modAuth)
CREATE (req4)-[:REQUIREMENT_HAS_LOCATION]->(modUser)
CREATE (req5)-[:REQUIREMENT_HAS_LOCATION]->(modUser)
CREATE (req6)-[:REQUIREMENT_HAS_LOCATION]->(modUser)
CREATE (req7)-[:REQUIREMENT_HAS_LOCATION]->(modAdmin)
CREATE (req8)-[:REQUIREMENT_HAS_LOCATION]->(modAdmin)
CREATE (req9)-[:REQUIREMENT_HAS_LOCATION]->(modAdmin)

// 検証ケースの作成
CREATE (test1:RequirementVerification {
  id: 'TEST-AUTH-001',
  name: 'ログインテスト',
  description: 'ユーザーログイン機能のテスト',
  verification_type: 'automated_test'
})

CREATE (test2:RequirementVerification {
  id: 'TEST-AUTH-002',
  name: 'パスワードリセットテスト',
  description: 'パスワードリセット機能のテスト',
  verification_type: 'automated_test'
})

CREATE (test3:RequirementVerification {
  id: 'TEST-USER-001',
  name: 'ユーザー登録テスト',
  description: 'ユーザー登録機能のテスト',
  verification_type: 'automated_test'
})

CREATE (test4:RequirementVerification {
  id: 'TEST-USER-002',
  name: 'プロファイル編集テスト',
  description: 'ユーザープロファイル編集機能のテスト',
  verification_type: 'automated_test'
})

CREATE (test5:RequirementVerification {
  id: 'TEST-ADMIN-001',
  name: 'ユーザー管理テスト',
  description: '管理者によるユーザー管理機能のテスト',
  verification_type: 'manual_test'
})

// 要件と検証ケースの関連付け
CREATE (req1)-[:VERIFIED_BY]->(test1)
CREATE (req2)-[:VERIFIED_BY]->(test2)
CREATE (req4)-[:VERIFIED_BY]->(test3)
CREATE (req5)-[:VERIFIED_BY]->(test4)
CREATE (req7)-[:VERIFIED_BY]->(test5)

// コード実装の作成
CREATE (code1:CodeEntity {
  persistent_id: 'CODE-AUTH-001',
  name: 'AuthenticationService',
  type: 'class',
  signature: 'class AuthenticationService',
  complexity: 5,
  start_position: 100,
  end_position: 500
})

CREATE (code2:CodeEntity {
  persistent_id: 'CODE-AUTH-002',
  name: 'PasswordResetService',
  type: 'class',
  signature: 'class PasswordResetService',
  complexity: 4,
  start_position: 600,
  end_position: 900
})

CREATE (code3:CodeEntity {
  persistent_id: 'CODE-AUTH-003',
  name: 'TwoFactorAuthService',
  type: 'class',
  signature: 'class TwoFactorAuthService',
  complexity: 6,
  start_position: 1000,
  end_position: 1500
})

CREATE (code4:CodeEntity {
  persistent_id: 'CODE-USER-001',
  name: 'UserRegistrationService',
  type: 'class',
  signature: 'class UserRegistrationService',
  complexity: 5,
  start_position: 1600,
  end_position: 2000
})

CREATE (code5:CodeEntity {
  persistent_id: 'CODE-USER-002',
  name: 'UserProfileService',
  type: 'class',
  signature: 'class UserProfileService',
  complexity: 4,
  start_position: 2100,
  end_position: 2500
})

CREATE (code6:CodeEntity {
  persistent_id: 'CODE-ADMIN-001',
  name: 'UserManagementService',
  type: 'class',
  signature: 'class UserManagementService',
  complexity: 7,
  start_position: 2600,
  end_position: 3100
})

// 実装コードと要件の関連付け
CREATE (req1)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code1)
CREATE (req2)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code2)
CREATE (req3)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code3)
CREATE (req4)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code4)
CREATE (req5)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code5)
CREATE (req7)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code6)

// テストケースと実装コードの関連付け
CREATE (test1)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'unit_test'}]->(code1)
CREATE (test2)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'unit_test'}]->(code2)
CREATE (test3)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'unit_test'}]->(code4)
CREATE (test4)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'unit_test'}]->(code5)
CREATE (test5)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'integration_test'}]->(code6)

RETURN count(*) AS created_nodes;
