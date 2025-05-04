// 階層型トレーサビリティモデル - レガシーサンプルデータ

// ===== LocationURIデータ =====
CREATE (loc1:LocationURI {uri_id: 'loc1', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/service', fragment: '', query: ''});
CREATE (loc2:LocationURI {uri_id: 'loc2', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/controller', fragment: '', query: ''});
CREATE (loc3:LocationURI {uri_id: 'loc3', scheme: 'file', authority: 'project', path: '/src/test/java/com/example/service', fragment: '', query: ''});
CREATE (loc4:LocationURI {uri_id: 'loc4', scheme: 'requirement', authority: 'project', path: '/functional/user-management', fragment: '', query: ''});
CREATE (loc5:LocationURI {uri_id: 'loc5', scheme: 'requirement', authority: 'project', path: '/non-functional/security', fragment: '', query: ''});

// ===== RequirementEntityデータ =====
CREATE (req1:RequirementEntity {id: 'REQ-001', title: 'ユーザー登録機能', description: 'システムはユーザー情報を登録できること', priority: 'HIGH', requirement_type: 'functional'});
CREATE (req2:RequirementEntity {id: 'REQ-002', title: 'ユーザー認証機能', description: 'システムはユーザー認証を行えること', priority: 'HIGH', requirement_type: 'functional'});
CREATE (req3:RequirementEntity {id: 'REQ-003', title: 'パスワードポリシー', description: 'パスワードは8文字以上で、英数字と特殊文字を含むこと', priority: 'MEDIUM', requirement_type: 'security'});
CREATE (req4:RequirementEntity {id: 'REQ-004', title: 'アカウントロック機能', description: '連続5回の認証失敗でアカウントをロックすること', priority: 'MEDIUM', requirement_type: 'security'});

// ===== CodeEntityデータ =====
CREATE (code1:CodeEntity {persistent_id: 'CODE-001', name: 'UserService', type: 'class', signature: 'public class UserService', complexity: 5, start_position: 100, end_position: 500});
CREATE (code2:CodeEntity {persistent_id: 'CODE-002', name: 'registerUser', type: 'function', signature: 'public User registerUser(UserDTO userDTO)', complexity: 3, start_position: 150, end_position: 250});
CREATE (code3:CodeEntity {persistent_id: 'CODE-003', name: 'authenticateUser', type: 'function', signature: 'public boolean authenticateUser(String username, String password)', complexity: 4, start_position: 300, end_position: 400});
CREATE (code4:CodeEntity {persistent_id: 'CODE-004', name: 'UserController', type: 'class', signature: 'public class UserController', complexity: 2, start_position: 600, end_position: 900});
CREATE (code5:CodeEntity {persistent_id: 'CODE-005', name: 'UserServiceTest', type: 'test', signature: 'public class UserServiceTest', complexity: 1, start_position: 1000, end_position: 1200});
CREATE (code6:CodeEntity {persistent_id: 'CODE-006', name: 'validatePassword', type: 'function', signature: 'private boolean validatePassword(String password)', complexity: 2, start_position: 420, end_position: 480});
CREATE (code7:CodeEntity {persistent_id: 'CODE-007', name: 'lockAccount', type: 'function', signature: 'private void lockAccount(String username)', complexity: 3, start_position: 480, end_position: 520});
