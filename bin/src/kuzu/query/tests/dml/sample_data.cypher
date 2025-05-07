// 階層型トレーサビリティモデル - 基本サンプルデータ

// ===== LocationURIデータ =====

// ファイル位置情報
CREATE (loc1:LocationURI {uri_id: 'loc_service', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/service', fragment: '', query: ''});
CREATE (loc2:LocationURI {uri_id: 'loc_controller', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/controller', fragment: '', query: ''});
CREATE (loc3:LocationURI {uri_id: 'loc_test', scheme: 'file', authority: 'project', path: '/src/test/java/com/example/service', fragment: '', query: ''});
CREATE (loc4:LocationURI {uri_id: 'loc_repository', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/repository', fragment: '', query: ''});

// 要件位置情報
CREATE (loc5:LocationURI {uri_id: 'loc_func_req', scheme: 'requirement', authority: 'project', path: '/functional/user-management', fragment: '', query: ''});
CREATE (loc6:LocationURI {uri_id: 'loc_security_req', scheme: 'requirement', authority: 'project', path: '/non-functional/security', fragment: '', query: ''});
CREATE (loc7:LocationURI {uri_id: 'loc_perf_req', scheme: 'requirement', authority: 'project', path: '/non-functional/performance', fragment: '', query: ''});

// 位置情報の階層関係
CREATE (loc_root:LocationURI {uri_id: 'loc_root', scheme: 'file', authority: 'project', path: '/', fragment: '', query: ''});
CREATE (loc_src:LocationURI {uri_id: 'loc_src', scheme: 'file', authority: 'project', path: '/src', fragment: '', query: ''});
CREATE (loc_main:LocationURI {uri_id: 'loc_main', scheme: 'file', authority: 'project', path: '/src/main', fragment: '', query: ''});
CREATE (loc_test_root:LocationURI {uri_id: 'loc_test_root', scheme: 'file', authority: 'project', path: '/src/test', fragment: '', query: ''});
CREATE (loc_java:LocationURI {uri_id: 'loc_java', scheme: 'file', authority: 'project', path: '/src/main/java', fragment: '', query: ''});
CREATE (loc_test_java:LocationURI {uri_id: 'loc_test_java', scheme: 'file', authority: 'project', path: '/src/test/java', fragment: '', query: ''});
CREATE (loc_com:LocationURI {uri_id: 'loc_com', scheme: 'file', authority: 'project', path: '/src/main/java/com', fragment: '', query: ''});
CREATE (loc_test_com:LocationURI {uri_id: 'loc_test_com', scheme: 'file', authority: 'project', path: '/src/test/java/com', fragment: '', query: ''});
CREATE (loc_example:LocationURI {uri_id: 'loc_example', scheme: 'file', authority: 'project', path: '/src/main/java/com/example', fragment: '', query: ''});
CREATE (loc_test_example:LocationURI {uri_id: 'loc_test_example', scheme: 'file', authority: 'project', path: '/src/test/java/com/example', fragment: '', query: ''});

// 要件階層構造
CREATE (loc_req_root:LocationURI {uri_id: 'loc_req_root', scheme: 'requirement', authority: 'project', path: '/', fragment: '', query: ''});
CREATE (loc_functional:LocationURI {uri_id: 'loc_functional', scheme: 'requirement', authority: 'project', path: '/functional', fragment: '', query: ''});
CREATE (loc_non_functional:LocationURI {uri_id: 'loc_non_functional', scheme: 'requirement', authority: 'project', path: '/non-functional', fragment: '', query: ''});

// ===== RequirementEntityデータ =====
CREATE (req1:RequirementEntity {id: 'REQ-001', title: 'ユーザー登録機能', description: 'システムはユーザー情報を登録できること', priority: 'HIGH', requirement_type: 'functional'});
CREATE (req2:RequirementEntity {id: 'REQ-002', title: 'ユーザー認証機能', description: 'システムはユーザー認証を行えること', priority: 'HIGH', requirement_type: 'functional'});
CREATE (req3:RequirementEntity {id: 'REQ-003', title: 'パスワードポリシー', description: 'パスワードは8文字以上で、英数字と特殊文字を含むこと', priority: 'MEDIUM', requirement_type: 'security'});
CREATE (req4:RequirementEntity {id: 'REQ-004', title: 'アカウントロック機能', description: '連続5回の認証失敗でアカウントをロックすること', priority: 'MEDIUM', requirement_type: 'security'});
CREATE (req5:RequirementEntity {id: 'REQ-005', title: 'ユーザー検索性能', description: 'ユーザー検索は0.5秒以内に完了すること', priority: 'MEDIUM', requirement_type: 'performance'});

// ===== RequirementVerificationデータ =====
CREATE (ver1:RequirementVerification {id: 'TEST-001', name: 'ユーザー登録テスト', description: 'ユーザー登録機能の検証', verification_type: 'unit-test'});
CREATE (ver2:RequirementVerification {id: 'TEST-002', name: '認証テスト', description: 'ユーザー認証機能の検証', verification_type: 'integration'});
CREATE (ver3:RequirementVerification {id: 'TEST-003', name: 'パスワード検証テスト', description: 'パスワードポリシーの検証', verification_type: 'unit-test'});
CREATE (ver4:RequirementVerification {id: 'TEST-004', name: 'アカウントロックテスト', description: 'アカウントロック機能の検証', verification_type: 'integration'});
CREATE (ver5:RequirementVerification {id: 'TEST-005', name: '検索性能テスト', description: 'ユーザー検索の性能検証', verification_type: 'performance'});

// ===== CodeEntityデータ =====
CREATE (code1:CodeEntity {persistent_id: 'CODE-001', name: 'UserService', type: 'class', signature: 'public class UserService', complexity: 5, start_position: 100, end_position: 500});
CREATE (code2:CodeEntity {persistent_id: 'CODE-002', name: 'registerUser', type: 'function', signature: 'public User registerUser(UserDTO userDTO)', complexity: 3, start_position: 150, end_position: 250});
CREATE (code3:CodeEntity {persistent_id: 'CODE-003', name: 'authenticateUser', type: 'function', signature: 'public boolean authenticateUser(String username, String password)', complexity: 4, start_position: 300, end_position: 400});
CREATE (code4:CodeEntity {persistent_id: 'CODE-004', name: 'UserController', type: 'class', signature: 'public class UserController', complexity: 2, start_position: 600, end_position: 900});
CREATE (code5:CodeEntity {persistent_id: 'CODE-005', name: 'UserServiceTest', type: 'test', signature: 'public class UserServiceTest', complexity: 1, start_position: 1000, end_position: 1200});
CREATE (code6:CodeEntity {persistent_id: 'CODE-006', name: 'validatePassword', type: 'function', signature: 'private boolean validatePassword(String password)', complexity: 2, start_position: 420, end_position: 480});
CREATE (code7:CodeEntity {persistent_id: 'CODE-007', name: 'lockAccount', type: 'function', signature: 'private void lockAccount(String username)', complexity: 3, start_position: 480, end_position: 520});
CREATE (code8:CodeEntity {persistent_id: 'CODE-008', name: 'UserRepository', type: 'class', signature: 'public class UserRepository', complexity: 4, start_position: 1300, end_position: 1800});
CREATE (code9:CodeEntity {persistent_id: 'CODE-009', name: 'findUserById', type: 'function', signature: 'public User findUserById(Long id)', complexity: 2, start_position: 1350, end_position: 1400});

// ===== ReferenceEntityデータ =====
// DEPRECATED: ReferenceEntityからuriプロパティとurlプロパティは削除されました
// 外部参照先のURLは別の方法で管理してください
CREATE (ref1:ReferenceEntity {id: 'REF-001', description: 'Spring Security API', type: 'api', source_type: 'external'});
CREATE (ref2:ReferenceEntity {id: 'REF-002', description: 'OWASP Password Guidelines', type: 'document', source_type: 'external'});

// ===== VersionStateデータ =====
CREATE (vs1:VersionState {id: 'v1.0.0', timestamp: '2023-01-15T10:00:00Z', commit_id: 'a1b2c3d4', branch_name: 'main'});
CREATE (vs2:VersionState {id: 'v1.1.0', timestamp: '2023-02-20T14:30:00Z', commit_id: 'e5f6g7h8', branch_name: 'main'});

// ===== EntityAggregationViewデータ =====
CREATE (view1:EntityAggregationView {id: 'VIEW-001', view_type: 'coverage'});
CREATE (view2:EntityAggregationView {id: 'VIEW-002', view_type: 'progress'});
