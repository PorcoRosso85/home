// 階層型トレーサビリティモデル - テスト実行結果と要件の紐付け関連クエリ

// テスト対象の要件、検証、コードを作成
// @name: create_test_result_data
// 要件の作成
CREATE (req1:RequirementEntity {
  id: 'REQ-TEST-001',
  title: 'ユーザー登録機能',
  description: 'ユーザーはメールアドレスとパスワードで新規登録できる',
  priority: 'high',
  requirement_type: 'functional'
})

CREATE (req2:RequirementEntity {
  id: 'REQ-TEST-002',
  title: 'ユーザーログイン機能',
  description: 'ユーザーはメールアドレスとパスワードでログインできる',
  priority: 'high',
  requirement_type: 'functional'
})

CREATE (req3:RequirementEntity {
  id: 'REQ-TEST-003',
  title: 'パスワードリセット機能',
  description: 'ユーザーはパスワードを忘れた場合にリセットできる',
  priority: 'medium',
  requirement_type: 'functional'
})

// 検証（テスト）の作成
CREATE (test1:RequirementVerification {
  id: 'TEST-001',
  name: 'ユーザー登録テスト',
  description: 'ユーザー登録機能の単体テスト',
  verification_type: 'unit_test'
})

CREATE (test2:RequirementVerification {
  id: 'TEST-002',
  name: 'ユーザーログインテスト',
  description: 'ユーザーログイン機能の単体テスト',
  verification_type: 'unit_test'
})

CREATE (test3:RequirementVerification {
  id: 'TEST-003',
  name: 'パスワードリセットテスト',
  description: 'パスワードリセット機能の単体テスト',
  verification_type: 'unit_test'
})

CREATE (test4:RequirementVerification {
  id: 'TEST-004',
  name: '認証フロー統合テスト',
  description: '登録、ログイン、パスワードリセットを含む統合テスト',
  verification_type: 'integration_test'
})

// コード実装の作成
CREATE (code1:CodeEntity {
  persistent_id: 'CODE-TEST-001',
  name: 'UserRegistrationService',
  type: 'class',
  signature: 'class UserRegistrationService',
  complexity: 6,
  start_position: 100,
  end_position: 1000
})

CREATE (code2:CodeEntity {
  persistent_id: 'CODE-TEST-002',
  name: 'UserLoginService',
  type: 'class',
  signature: 'class UserLoginService',
  complexity: 5,
  start_position: 1100,
  end_position: 2000
})

CREATE (code3:CodeEntity {
  persistent_id: 'CODE-TEST-003',
  name: 'PasswordResetService',
  type: 'class',
  signature: 'class PasswordResetService',
  complexity: 7,
  start_position: 2100,
  end_position: 3000
})

// 関連付け（要件と検証）
CREATE (req1)-[:VERIFIED_BY]->(test1)
CREATE (req2)-[:VERIFIED_BY]->(test2)
CREATE (req3)-[:VERIFIED_BY]->(test3)
CREATE (req1)-[:VERIFIED_BY]->(test4)
CREATE (req2)-[:VERIFIED_BY]->(test4)
CREATE (req3)-[:VERIFIED_BY]->(test4)

// 関連付け（要件と実装）
CREATE (req1)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code1)
CREATE (req2)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code2)
CREATE (req3)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code3)

// 関連付け（検証と実装）
CREATE (test1)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'junit_test'}]->(code1)
CREATE (test2)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'junit_test'}]->(code2)
CREATE (test3)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'junit_test'}]->(code3)

RETURN 3 AS created_requirements, 4 AS created_tests, 3 AS created_code;

// テスト実行結果のノードの作成
// @name: create_test_execution_results
// テスト実行のセッションを作成
CREATE (session:TestExecutionSession {
  id: 'SESSION-001',
  timestamp: '2024-05-01T10:00:00Z',
  executor: 'CI Server',
  environment: 'test',
  build_id: 'BUILD-123'
})

// テスト1の実行結果（成功）
CREATE (result1:TestExecutionResult {
  id: 'RESULT-001',
  test_id: 'TEST-001',
  status: 'passed',
  execution_time: 1.25,
  timestamp: '2024-05-01T10:01:00Z'
})

// テスト2の実行結果（成功）
CREATE (result2:TestExecutionResult {
  id: 'RESULT-002',
  test_id: 'TEST-002',
  status: 'passed',
  execution_time: 0.95,
  timestamp: '2024-05-01T10:02:00Z'
})

// テスト3の実行結果（失敗）
CREATE (result3:TestExecutionResult {
  id: 'RESULT-003',
  test_id: 'TEST-003',
  status: 'failed',
  execution_time: 1.35,
  timestamp: '2024-05-01T10:03:00Z',
  error_message: 'パスワードリセットメール送信に失敗しました',
  stack_trace: 'at PasswordResetService.sendEmail (line 42)'
})

// テスト4の実行結果（失敗）
CREATE (result4:TestExecutionResult {
  id: 'RESULT-004',
  test_id: 'TEST-004',
  status: 'failed',
  execution_time: 3.25,
  timestamp: '2024-05-01T10:05:00Z',
  error_message: 'パスワードリセット後のログインに失敗しました',
  stack_trace: 'at AuthenticationFlow.verifyResetAndLogin (line 89)'
})

// セッションとテスト結果の関連付け
CREATE (session)-[:CONTAINS_RESULT]->(result1)
CREATE (session)-[:CONTAINS_RESULT]->(result2)
CREATE (session)-[:CONTAINS_RESULT]->(result3)
CREATE (session)-[:CONTAINS_RESULT]->(result4)

// テストと実行結果の関連付け
WITH result1, result2, result3, result4
MATCH (test1:RequirementVerification {id: 'TEST-001'})
MATCH (test2:RequirementVerification {id: 'TEST-002'})
MATCH (test3:RequirementVerification {id: 'TEST-003'})
MATCH (test4:RequirementVerification {id: 'TEST-004'})

CREATE (test1)-[:HAS_EXECUTION_RESULT]->(result1)
CREATE (test2)-[:HAS_EXECUTION_RESULT]->(result2)
CREATE (test3)-[:HAS_EXECUTION_RESULT]->(result3)
CREATE (test4)-[:HAS_EXECUTION_RESULT]->(result4)

RETURN 1 AS created_sessions, 4 AS created_results;

// テスト実行結果から要件の充足状況を確認
// @name: check_requirement_satisfaction
MATCH (req:RequirementEntity)-[:VERIFIED_BY]->(test:RequirementVerification)-[:HAS_EXECUTION_RESULT]->(result:TestExecutionResult)
WITH req, test, result
ORDER BY req.id, test.id

RETURN 
  req.id AS requirement_id,
  req.title AS requirement_title,
  test.id AS test_id,
  test.name AS test_name,
  result.id AS result_id,
  result.status AS test_status,
  result.error_message AS error_message
ORDER BY req.id, test.id;

// テスト実行セッションの詳細を取得
// @name: get_test_session_details
MATCH (session:TestExecutionSession {id: $sessionId})
OPTIONAL MATCH (session)-[:CONTAINS_RESULT]->(result:TestExecutionResult)
WITH session, count(result) AS total_results,
     count(CASE WHEN result.status = 'passed' THEN 1 ELSE null END) AS passed_count,
     count(CASE WHEN result.status = 'failed' THEN 1 ELSE null END) AS failed_count

RETURN 
  session.id AS session_id,
  session.timestamp AS timestamp,
  session.executor AS executor,
  session.environment AS environment,
  session.build_id AS build_id,
  total_results,
  passed_count,
  failed_count,
  CASE WHEN failed_count = 0 THEN true ELSE false END AS is_successful,
  CASE WHEN total_results > 0 THEN 1.0 * passed_count / total_results * 100 ELSE 0.0 END AS success_rate_pct;

// 要件ごとの充足状況を集計
// @name: summarize_requirement_satisfaction
MATCH (req:RequirementEntity)
OPTIONAL MATCH (req)-[:VERIFIED_BY]->(test:RequirementVerification)
OPTIONAL MATCH (test)-[:HAS_EXECUTION_RESULT]->(result:TestExecutionResult)

WITH 
  req,
  count(DISTINCT test) AS total_tests,
  count(DISTINCT CASE WHEN result.status = 'passed' THEN test ELSE null END) AS passed_tests,
  collect(DISTINCT CASE WHEN result.status = 'failed' THEN test.id ELSE null END) AS failed_test_ids,
  collect(DISTINCT CASE WHEN result.status = 'failed' THEN result.error_message ELSE null END) AS error_messages

RETURN 
  req.id AS requirement_id,
  req.title AS requirement_title,
  req.priority AS requirement_priority,
  total_tests AS total_verifications,
  passed_tests AS passed_verifications,
  total_tests - passed_tests AS failed_verifications,
  CASE WHEN total_tests > 0 THEN
    CASE WHEN passed_tests = total_tests THEN 'satisfied'
         WHEN passed_tests > 0 THEN 'partially_satisfied'
         ELSE 'not_satisfied'
    END
  ELSE 'not_verified'
  END AS satisfaction_status,
  [x IN failed_test_ids WHERE x IS NOT NULL] AS failed_test_ids,
  [x IN error_messages WHERE x IS NOT NULL] AS error_messages
ORDER BY
  CASE satisfaction_status
    WHEN 'not_verified' THEN 0
    WHEN 'not_satisfied' THEN 1
    WHEN 'partially_satisfied' THEN 2
    WHEN 'satisfied' THEN 3
  END,
  req.priority = 'high' DESC,
  req.priority = 'medium' DESC,
  req.priority = 'low' DESC;

// 特定の期間内のテスト実行結果の履歴を取得
// @name: get_test_execution_history
MATCH (test:RequirementVerification {id: $testId})
MATCH (test)-[:HAS_EXECUTION_RESULT]->(result:TestExecutionResult)
WHERE result.timestamp >= $startDate AND result.timestamp <= $endDate
WITH test, result
ORDER BY result.timestamp DESC

RETURN 
  test.id AS test_id,
  test.name AS test_name,
  result.id AS result_id,
  result.status AS status,
  result.execution_time AS execution_time,
  result.timestamp AS timestamp,
  result.error_message AS error_message
ORDER BY result.timestamp DESC;

// 失敗したテストに関連するコードを特定
// @name: identify_problematic_code
MATCH (result:TestExecutionResult)
WHERE result.status = 'failed'
MATCH (test:RequirementVerification)-[:HAS_EXECUTION_RESULT]->(result)
OPTIONAL MATCH (test)-[:VERIFICATION_IS_IMPLEMENTED_BY]->(code:CodeEntity)
OPTIONAL MATCH (req:RequirementEntity)-[:VERIFIED_BY]->(test)

RETURN 
  result.id AS result_id,
  test.id AS test_id,
  test.name AS test_name,
  result.error_message AS error_message,
  code.persistent_id AS code_id,
  code.name AS code_name,
  collect(DISTINCT req.id) AS affected_requirements
ORDER BY test.id;

// テスト失敗に基づく修正優先度の分析
// @name: analyze_fix_priorities
MATCH (req:RequirementEntity)-[:VERIFIED_BY]->(test:RequirementVerification)-[:HAS_EXECUTION_RESULT]->(result:TestExecutionResult)
WHERE result.status = 'failed'
WITH 
  req,
  count(DISTINCT test) AS failed_test_count,
  collect(DISTINCT test.id) AS failed_tests,
  collect(DISTINCT result.error_message) AS error_messages

RETURN 
  req.id AS requirement_id,
  req.title AS requirement_title,
  req.priority AS requirement_priority,
  failed_test_count,
  failed_tests,
  error_messages,
  CASE req.priority
    WHEN 'high' THEN 3
    WHEN 'medium' THEN 2
    WHEN 'low' THEN 1
    ELSE 0
  END * failed_test_count AS fix_priority_score
ORDER BY fix_priority_score DESC, req.priority, req.id;