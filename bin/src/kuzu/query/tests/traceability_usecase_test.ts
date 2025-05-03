#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - 主要ユースケースPOC
 * 
 * このファイルは階層型トレーサビリティモデルの2つの主要ユースケースを実装:
 * 1. コードから要件への逆引き (code_to_requirements_mapping)
 * 2. 要件の実装状況追跡 (requirement_implementation_status)
 * 
 * 実行方法: 
 * LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib/":$LD_LIBRARY_PATH \
 * deno run --allow-all traceability_usecase_test.ts
 */

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";
import { ensureDir, loadKuzuModule } from "../mod.ts";

// テストDB用のディレクトリ
const TEST_DB_DIR = "./test_db/traceability_db";

// 現在の作業ディレクトリからの相対パスを絶対パスに変換
const TEST_DB_PATH = path.resolve(Deno.cwd(), TEST_DB_DIR);

// 型定義
interface RequirementResult {
  requirement_id: string;
  requirement_title: string;
  requirement_type: string;
  requirement_priority: string;
  implementation_type: string;
  requirement_location: string;
  relation_type: string;
}

interface ImplementationResult {
  requirement_id: string;
  requirement_title: string;
  requirement_type: string;
  code_id: string;
  code_name: string;
  code_type: string;
  implementation_type: string;
  code_location: string;
}

interface UnimplementedResult {
  requirement_id: string;
  title: string;
}

// 既存のDBを削除してクリーンな状態から始める
async function cleanDatabase(dbPath: string) {
  try {
    await Deno.remove(dbPath, { recursive: true });
    console.log(`既存のデータベースを削除しました: ${dbPath}`);
  } catch (error) {
    if (!(error instanceof Deno.errors.NotFound)) {
      console.warn(`データベース削除時の警告: ${error.message}`);
    }
  }
}

/**
 * データベーススキーマを作成する関数
 */
async function createSchema(conn: any): Promise<void> {
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
 */
async function insertSampleData(conn: any): Promise<void> {
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
 * ユースケース1: コードエンティティから要件への逆引き
 * 指定したコードIDに関連する要件を検索する関数
 */
async function findRequirementsForCode(conn: any, codeId: string): Promise<RequirementResult[]> {
  // 直接実装している要件を検索するクエリ
  const query = `
    MATCH (c:CodeEntity)-[impl:IMPLEMENTS]->(r:RequirementEntity)
    WHERE c.persistent_id = '${codeId}'
    OPTIONAL MATCH (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(loc:LocationURI)
    RETURN r.id as requirement_id, 
           r.title as requirement_title,
           r.requirement_type as requirement_type,
           r.priority as requirement_priority,
           impl.implementation_type as implementation_type,
           loc.scheme + '://' + loc.authority + loc.path as requirement_location,
           'direct' as relation_type
  `;
  
  const response = await conn.query(query);
  const rows = await response.getAll();
  const results: RequirementResult[] = [];
  
  for (const row of rows) {
    results.push({
      requirement_id: row.requirement_id || "",
      requirement_title: row.requirement_title || "",
      requirement_type: row.requirement_type || "",
      requirement_priority: row.requirement_priority || "",
      implementation_type: row.implementation_type || "",
      requirement_location: row.requirement_location || "",
      relation_type: row.relation_type || ""
    });
  }
  
  // 親コードエンティティの場合、子コードが実装している要件も検索
  const queryIndirect = `
    MATCH (parent:CodeEntity)-[:CONTAINS]->(child:CodeEntity)-[impl:IMPLEMENTS]->(r:RequirementEntity)
    WHERE parent.persistent_id = '${codeId}'
    OPTIONAL MATCH (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(loc:LocationURI)
    RETURN r.id as requirement_id, 
           r.title as requirement_title,
           r.requirement_type as requirement_type,
           r.priority as requirement_priority,
           impl.implementation_type as implementation_type,
           loc.scheme + '://' + loc.authority + loc.path as requirement_location,
           'via_child_' + child.name as relation_type
  `;
  
  const responseIndirect = await conn.query(queryIndirect);
  const rowsIndirect = await responseIndirect.getAll();
  
  for (const row of rowsIndirect) {
    // 重複をチェック（既に直接関係で追加されている要件は除外）
    const isDuplicate = results.some(existing => existing.requirement_id === row.requirement_id);
    
    if (!isDuplicate) {
      results.push({
        requirement_id: row.requirement_id || "",
        requirement_title: row.requirement_title || "",
        requirement_type: row.requirement_type || "",
        requirement_priority: row.requirement_priority || "",
        implementation_type: row.implementation_type || "",
        requirement_location: row.requirement_location || "",
        relation_type: row.relation_type || ""
      });
    }
  }
  
  return results;
}

/**
 * コードに関連する要件の結果を整形する関数
 */
function formatRequirementsForCode(results: RequirementResult[]): string {
  if (!results.length) {
    return "指定されたコードに関連する要件は見つかりませんでした。";
  }
  
  const output: string[] = [];
  output.push("\n関連する要件:");
  output.push("=".repeat(80));
  output.push(`${"要件ID".padEnd(10)} ${"タイトル".padEnd(30)} ${"タイプ".padEnd(10)} ${"優先度".padEnd(10)} ${"関連タイプ".padEnd(20)} ${"場所"}`);
  output.push("-".repeat(80));
  
  // 優先度順にソート（HIGH、MEDIUM、LOW）
  const priorityOrder: Record<string, number> = {"HIGH": 0, "MEDIUM": 1, "LOW": 2};
  const sortedResults = [...results].sort((a, b) => {
    return (priorityOrder[a.requirement_priority] || 99) - (priorityOrder[b.requirement_priority] || 99);
  });
  
  for (const result of sortedResults) {
    output.push(`${result.requirement_id.padEnd(10)} ${(result.requirement_title || "").slice(0, 30).padEnd(30)} ` +
               `${(result.requirement_type || "").padEnd(10)} ${(result.requirement_priority || "").padEnd(10)} ` +
               `${(result.relation_type || "").slice(0, 20).padEnd(20)} ${result.requirement_location || ""}`);
  }
  
  return output.join("\n");
}

/**
 * ユースケース2: 要件の実装状況追跡
 * 指定した要件IDの実装状況を追跡する関数
 */
async function trackRequirementImplementation(conn: any, requirementId: string): Promise<ImplementationResult[]> {
  const query = `
    MATCH (r:RequirementEntity)<-[impl:IMPLEMENTS]-(c:CodeEntity)
    WHERE r.id = '${requirementId}'
    OPTIONAL MATCH (c)-[:HAS_LOCATION_URI]->(loc:LocationURI)
    RETURN r.id as requirement_id, 
           r.title as requirement_title,
           r.requirement_type as requirement_type,
           c.persistent_id as code_id, 
           c.name as code_name,
           c.type as code_type,
           impl.implementation_type as implementation_type,
           loc.scheme + '://' + loc.authority + loc.path as code_location
  `;
  
  const response = await conn.query(query);
  const rows = await response.getAll();
  
  const results: ImplementationResult[] = [];
  for (const row of rows) {
    results.push({
      requirement_id: row.requirement_id || "",
      requirement_title: row.requirement_title || "",
      requirement_type: row.requirement_type || "",
      code_id: row.code_id || "",
      code_name: row.code_name || "",
      code_type: row.code_type || "",
      implementation_type: row.implementation_type || "",
      code_location: row.code_location || ""
    });
  }
  
  return results;
}

/**
 * 実装状況結果を整形する関数
 */
function formatImplementationStatus(results: ImplementationResult[]): string {
  if (!results.length) {
    return "指定された要件の実装は見つかりませんでした。";
  }
  
  const output: string[] = [];
  // 要件情報を取得（すべての結果で同じ）
  const reqInfo = results[0];
  output.push(`要件ID: ${reqInfo.requirement_id}`);
  output.push(`タイトル: ${reqInfo.requirement_title}`);
  output.push(`タイプ: ${reqInfo.requirement_type}`);
  output.push("\n実装状況:");
  output.push("=".repeat(80));
  output.push(`${"コードID".padEnd(10)} ${"名前".padEnd(20)} ${"種類".padEnd(10)} ${"実装タイプ".padEnd(20)} ${"場所"}`);
  output.push("-".repeat(80));
  
  for (const result of results) {
    output.push(`${(result.code_id || "").padEnd(10)} ${(result.code_name || "").padEnd(20)} ${(result.code_type || "").padEnd(10)} ` +
              `${(result.implementation_type || "").padEnd(20)} ${result.code_location || ""}`);
  }
  
  return output.join("\n");
}

/**
 * 未実装の要件を検索する関数
 */
async function findUnimplementedRequirements(conn: any): Promise<UnimplementedResult[]> {
  const query = `
    MATCH (r:RequirementEntity)
    WHERE NOT EXISTS {
      MATCH (r)<-[:IMPLEMENTS]-(c:CodeEntity)
      WHERE c.type <> 'test'
    }
    RETURN r.id as requirement_id, r.title as title
  `;
  
  const response = await conn.query(query);
  const rows = await response.getAll();
  
  const results: UnimplementedResult[] = [];
  for (const row of rows) {
    results.push({
      requirement_id: row.requirement_id || "",
      title: row.title || ""
    });
  }
  
  return results;
}

/**
 * 未実装要件の結果を整形する関数
 */
function formatUnimplementedRequirements(results: UnimplementedResult[]): string {
  const output: string[] = [];
  output.push("未実装の要件:");
  
  if (!results.length) {
    output.push("すべての要件が実装されています。");
  } else {
    for (const result of results) {
      output.push(`- ${result.requirement_id}: ${result.title}`);
    }
  }
  
  return output.join("\n");
}

/**
 * トレーサビリティモデルPOCテストを実行する関数
 */
async function runTest(): Promise<void> {
  console.log("階層型トレーサビリティモデルPOCテスト開始");
  console.log(`テストデータベースパス: ${TEST_DB_PATH}`);
  
  // データベースをクリーンな状態から開始する
  await cleanDatabase(TEST_DB_PATH);
  
  // テスト用ディレクトリの作成
  await ensureDir(TEST_DB_PATH);
  
  try {
    // KuzuDBモジュールをロード
    const kuzu = await loadKuzuModule();
    if (!kuzu) {
      console.error("KuzuDBモジュールをロードできませんでした。テストを中止します。");
      return;
    }
    
    // データベースの初期化
    console.log(`データベースを初期化中... パス: ${TEST_DB_PATH}`);
    const db = new kuzu.Database(TEST_DB_PATH);
    const conn = new kuzu.Connection(db);
    console.log("データベース初期化完了");
    
    try {
      // スキーマの作成
      console.log("データベーススキーマを作成中...");
      await createSchema(conn);
      console.log("スキーマ作成完了");
      
      // サンプルデータの挿入
      console.log("サンプルデータを挿入中...");
      await insertSampleData(conn);
      console.log("サンプルデータ挿入完了");
      
      // ユースケース1: コードから要件への逆引き
      console.log("\n==== ユースケース1: 特定コードの対応要件群の確認（逆引き） ====\n");
      
      // validatePassword関数のテスト
      const codeId = 'CODE-006';
      console.log(`コードID '${codeId}' (validatePassword関数) の関連要件:`);
      const results = await findRequirementsForCode(conn, codeId);
      const formattedOutput = formatRequirementsForCode(results);
      console.log(formattedOutput);
      
      console.log("\nUserServiceクラス全体の関連要件:");
      const resultsClass = await findRequirementsForCode(conn, 'CODE-001');
      const formattedOutputClass = formatRequirementsForCode(resultsClass);
      console.log(formattedOutputClass);
      
      // ユースケース2: 要件の実装状況追跡
      console.log("\n==== ユースケース2: 特定要件の実装状況の追跡 ====\n");
      
      // REQ-001の実装状況を確認
      console.log("REQ-001 (ユーザー登録機能) の実装状況:");
      const implementResults = await trackRequirementImplementation(conn, "REQ-001");
      const implementFormattedOutput = formatImplementationStatus(implementResults);
      console.log(implementFormattedOutput);
      
      // REQ-003 (セキュリティ要件) の実装状況を確認
      console.log("\nREQ-003 (パスワードポリシー) の実装状況:");
      const securityResults = await trackRequirementImplementation(conn, "REQ-003");
      const securityFormattedOutput = formatImplementationStatus(securityResults);
      console.log(securityFormattedOutput);
      
      // 未実装要件の特定
      console.log("\n==== 追加機能: 未実装要件の特定 ====\n");
      const unimplementedResults = await findUnimplementedRequirements(conn);
      const unimplementedFormattedOutput = formatUnimplementedRequirements(unimplementedResults);
      console.log(unimplementedFormattedOutput);
    } finally {
      // データベース接続のクローズ
      console.log("\nデータベース接続をクローズ中...");
      await conn.close();
      await db.close();
      console.log("データベース接続をクローズしました");
    }
    
    console.log("\n階層型トレーサビリティモデルPOCテスト完了");
  } catch (error) {
    console.error("テスト実行中にエラーが発生しました:", error);
    console.error("スタックトレース:", error.stack);
    throw error;
  }
}

// メイン実行部分
if (import.meta.main) {
  runTest()
    .then(() => {
      console.log("テスト成功！");
      Deno.exit(0);
    })
    .catch((error) => {
      console.error("テスト失敗:", error);
      Deno.exit(1);
    });
}

export { runTest };
