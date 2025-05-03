#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - テストデータ定義と初期化
 * 
 * このファイルはテスト用のデータ定義と初期化処理を提供します。
 * - スキーマ定義
 * - サンプルデータ生成
 * - テストデータの種類別の提供
 */

/**
 * データベーススキーマを作成する関数
 * @param conn データベース接続オブジェクト
 */
export async function createSchema(conn: any): Promise<void> {
  // LocationURIノード
  await conn.query(`
    CREATE NODE TABLE LocationURI (
      uri_id STRING PRIMARY KEY,
      scheme STRING,
      authority STRING,
      path STRING,
      fragment STRING,
      query STRING
    )
  `);
  
  // CodeEntityノード
  await conn.query(`
    CREATE NODE TABLE CodeEntity (
      persistent_id STRING PRIMARY KEY,
      name STRING,
      type STRING,
      signature STRING,
      complexity INT64,
      start_position INT64,
      end_position INT64
    )
  `);
  
  // RequirementEntityノード
  await conn.query(`
    CREATE NODE TABLE RequirementEntity (
      id STRING PRIMARY KEY,
      title STRING,
      description STRING,
      priority STRING,
      requirement_type STRING
    )
  `);
  
  // CodeEntity → LocationURI 関係
  await conn.query(`
    CREATE REL TABLE HAS_LOCATION_URI (
      FROM CodeEntity TO LocationURI
    )
  `);
  
  // RequirementEntity → LocationURI 関係
  await conn.query(`
    CREATE REL TABLE REQUIREMENT_HAS_LOCATION_URI (
      FROM RequirementEntity TO LocationURI
    )
  `);
  
  // CodeEntity → RequirementEntity 実装関係
  await conn.query(`
    CREATE REL TABLE IMPLEMENTS (
      FROM CodeEntity TO RequirementEntity,
      implementation_type STRING
    )
  `);
  
  // CodeEntity → CodeEntity 含有関係
  await conn.query(`
    CREATE REL TABLE CONTAINS (
      FROM CodeEntity TO CodeEntity
    )
  `);
}

/**
 * サンプルデータを挿入する関数
 * @param conn データベース接続オブジェクト 
 */
export async function insertSampleData(conn: any): Promise<void> {
  // LocationURIデータ
  await conn.query("CREATE (loc1:LocationURI {uri_id: 'loc1', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/service', fragment: '', query: ''})");
  await conn.query("CREATE (loc2:LocationURI {uri_id: 'loc2', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/controller', fragment: '', query: ''})");
  await conn.query("CREATE (loc3:LocationURI {uri_id: 'loc3', scheme: 'file', authority: 'project', path: '/src/test/java/com/example/service', fragment: '', query: ''})");
  await conn.query("CREATE (loc4:LocationURI {uri_id: 'loc4', scheme: 'requirement', authority: 'project', path: '/functional/user-management', fragment: '', query: ''})");
  await conn.query("CREATE (loc5:LocationURI {uri_id: 'loc5', scheme: 'requirement', authority: 'project', path: '/non-functional/security', fragment: '', query: ''})");
  
  // RequirementEntityデータ
  await conn.query("CREATE (req1:RequirementEntity {id: 'REQ-001', title: 'ユーザー登録機能', description: 'システムはユーザー情報を登録できること', priority: 'HIGH', requirement_type: 'functional'})");
  await conn.query("CREATE (req2:RequirementEntity {id: 'REQ-002', title: 'ユーザー認証機能', description: 'システムはユーザー認証を行えること', priority: 'HIGH', requirement_type: 'functional'})");
  await conn.query("CREATE (req3:RequirementEntity {id: 'REQ-003', title: 'パスワードポリシー', description: 'パスワードは8文字以上で、英数字と特殊文字を含むこと', priority: 'MEDIUM', requirement_type: 'security'})");
  await conn.query("CREATE (req4:RequirementEntity {id: 'REQ-004', title: 'アカウントロック機能', description: '連続5回の認証失敗でアカウントをロックすること', priority: 'MEDIUM', requirement_type: 'security'})");
  
  // CodeEntityデータ
  await conn.query("CREATE (code1:CodeEntity {persistent_id: 'CODE-001', name: 'UserService', type: 'class', signature: 'public class UserService', complexity: 5, start_position: 100, end_position: 500})");
  await conn.query("CREATE (code2:CodeEntity {persistent_id: 'CODE-002', name: 'registerUser', type: 'function', signature: 'public User registerUser(UserDTO userDTO)', complexity: 3, start_position: 150, end_position: 250})");
  await conn.query("CREATE (code3:CodeEntity {persistent_id: 'CODE-003', name: 'authenticateUser', type: 'function', signature: 'public boolean authenticateUser(String username, String password)', complexity: 4, start_position: 300, end_position: 400})");
  await conn.query("CREATE (code4:CodeEntity {persistent_id: 'CODE-004', name: 'UserController', type: 'class', signature: 'public class UserController', complexity: 2, start_position: 600, end_position: 900})");
  await conn.query("CREATE (code5:CodeEntity {persistent_id: 'CODE-005', name: 'UserServiceTest', type: 'test', signature: 'public class UserServiceTest', complexity: 1, start_position: 1000, end_position: 1200})");
  await conn.query("CREATE (code6:CodeEntity {persistent_id: 'CODE-006', name: 'validatePassword', type: 'function', signature: 'private boolean validatePassword(String password)', complexity: 2, start_position: 420, end_position: 480})");
  await conn.query("CREATE (code7:CodeEntity {persistent_id: 'CODE-007', name: 'lockAccount', type: 'function', signature: 'private void lockAccount(String username)', complexity: 3, start_position: 480, end_position: 520})");
  
  // HAS_LOCATION_URI関係データ
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-001'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-002'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-003'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-004'}), (l:LocationURI {uri_id: 'loc2'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (l:LocationURI {uri_id: 'loc3'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-006'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-007'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  
  // REQUIREMENT_HAS_LOCATION_URI関係データ
  await conn.query("MATCH (r:RequirementEntity {id: 'REQ-001'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (r:RequirementEntity {id: 'REQ-002'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (r:RequirementEntity {id: 'REQ-003'}), (l:LocationURI {uri_id: 'loc5'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (r:RequirementEntity {id: 'REQ-004'}), (l:LocationURI {uri_id: 'loc5'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)");
  
  // IMPLEMENTS関係データ
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-002'}), (r:RequirementEntity {id: 'REQ-001'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-003'}), (r:RequirementEntity {id: 'REQ-002'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (r:RequirementEntity {id: 'REQ-001'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'TESTS'}]->(r)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (r:RequirementEntity {id: 'REQ-002'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'TESTS'}]->(r)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-006'}), (r:RequirementEntity {id: 'REQ-003'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-007'}), (r:RequirementEntity {id: 'REQ-004'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)");
  
  // 親子関係の例 - コードエンティティ間
  await conn.query("MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-002'}) CREATE (c1)-[:CONTAINS]->(c2)");
  await conn.query("MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-003'}) CREATE (c1)-[:CONTAINS]->(c2)");
  await conn.query("MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-006'}) CREATE (c1)-[:CONTAINS]->(c2)");
  await conn.query("MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-007'}) CREATE (c1)-[:CONTAINS]->(c2)");
}

/**
 * 拡張テストデータを挿入する関数
 * より複雑なユースケースのテスト用に追加のデータを提供
 * @param conn データベース接続オブジェクト
 */
export async function insertExtendedTestData(conn: any): Promise<void> {
  // 基本データを挿入
  await insertSampleData(conn);
  
  // 追加のLocationURIデータ
  await conn.query("CREATE (loc6:LocationURI {uri_id: 'loc6', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/repository', fragment: '', query: ''})");
  await conn.query("CREATE (loc7:LocationURI {uri_id: 'loc7', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/config', fragment: '', query: ''})");
  await conn.query("CREATE (loc8:LocationURI {uri_id: 'loc8', scheme: 'requirement', authority: 'project', path: '/non-functional/performance', fragment: '', query: ''})");
  
  // 追加のRequirementEntityデータ
  await conn.query("CREATE (req5:RequirementEntity {id: 'REQ-005', title: 'データ永続化', description: 'システムはユーザーデータを永続化できること', priority: 'HIGH', requirement_type: 'functional'})");
  await conn.query("CREATE (req6:RequirementEntity {id: 'REQ-006', title: 'レスポンスタイム', description: 'ユーザー検索のレスポンスタイムは500ms以下であること', priority: 'MEDIUM', requirement_type: 'performance'})");
  await conn.query("CREATE (req7:RequirementEntity {id: 'REQ-007', title: '設定管理', description: 'システム設定を外部ファイルで管理できること', priority: 'LOW', requirement_type: 'functional'})");
  
  // 追加のCodeEntityデータ
  await conn.query("CREATE (code8:CodeEntity {persistent_id: 'CODE-008', name: 'UserRepository', type: 'class', signature: 'public class UserRepository', complexity: 4, start_position: 1300, end_position: 1800})");
  await conn.query("CREATE (code9:CodeEntity {persistent_id: 'CODE-009', name: 'findUserById', type: 'function', signature: 'public User findUserById(Long id)', complexity: 2, start_position: 1350, end_position: 1400})");
  await conn.query("CREATE (code10:CodeEntity {persistent_id: 'CODE-010', name: 'saveUser', type: 'function', signature: 'public User saveUser(User user)', complexity: 3, start_position: 1450, end_position: 1550})");
  await conn.query("CREATE (code11:CodeEntity {persistent_id: 'CODE-011', name: 'AppConfig', type: 'class', signature: 'public class AppConfig', complexity: 1, start_position: 1900, end_position: 2100})");
  
  // 追加のHAS_LOCATION_URI関係データ
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-008'}), (l:LocationURI {uri_id: 'loc6'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-009'}), (l:LocationURI {uri_id: 'loc6'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-010'}), (l:LocationURI {uri_id: 'loc6'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-011'}), (l:LocationURI {uri_id: 'loc7'}) CREATE (c)-[:HAS_LOCATION_URI]->(l)");
  
  // 追加のREQUIREMENT_HAS_LOCATION_URI関係データ
  await conn.query("MATCH (r:RequirementEntity {id: 'REQ-005'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (r:RequirementEntity {id: 'REQ-006'}), (l:LocationURI {uri_id: 'loc8'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)");
  await conn.query("MATCH (r:RequirementEntity {id: 'REQ-007'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l)");
  
  // 追加のIMPLEMENTS関係データ
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-010'}), (r:RequirementEntity {id: 'REQ-005'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-009'}), (r:RequirementEntity {id: 'REQ-006'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)");
  await conn.query("MATCH (c:CodeEntity {persistent_id: 'CODE-011'}), (r:RequirementEntity {id: 'REQ-007'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r)");
  
  // 追加の親子関係
  await conn.query("MATCH (c1:CodeEntity {persistent_id: 'CODE-008'}), (c2:CodeEntity {persistent_id: 'CODE-009'}) CREATE (c1)-[:CONTAINS]->(c2)");
  await conn.query("MATCH (c1:CodeEntity {persistent_id: 'CODE-008'}), (c2:CodeEntity {persistent_id: 'CODE-010'}) CREATE (c1)-[:CONTAINS]->(c2)");
}
