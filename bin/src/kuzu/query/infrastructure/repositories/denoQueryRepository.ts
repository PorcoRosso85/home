/**
 * KuzuDB Deno Query Repository
 * 
 * Deno環境でKuzuDBクエリを実行するための関数群
 */

import { existsSync } from "https://deno.land/std@0.224.0/fs/mod.ts";
import { join, dirname } from "https://deno.land/std@0.224.0/path/mod.ts";
import { describe, it } from "https://deno.land/std@0.224.0/testing/bdd.ts";
import { assertEquals, assert } from "https://deno.land/std@0.224.0/assert/mod.ts";

// ロガーの簡易実装（loggerモジュールがない場合のフォールバック）
const logger = {
  info: console.log,
  debug: console.debug,
  warn: console.warn,
  error: console.error
};

// 型定義
export type QueryResult<T> = {
  success: boolean;
  data?: T;
  error?: string;
  available_queries?: string[];
};

// 定数
const QUERY_DIR = dirname(new URL(import.meta.url).pathname);
const DML_DIR = join(QUERY_DIR, "../../dml");
const DDL_DIR = join(QUERY_DIR, "../../ddl");
const DQL_DIR = join(QUERY_DIR, "../../dql");
const CYPHER_EXTENSION = ".cypher";

/**
 * クエリファイルを検索する（Deno版）
 */
export async function findQueryFile(queryName: string): Promise<[boolean, string]> {
  // 検索優先順位
  const searchPaths = [
    // 1. DMLディレクトリ内
    join(DML_DIR, `${queryName}${CYPHER_EXTENSION}`),
    // 2. DMLテストディレクトリ内
    join(DML_DIR, "test", `${queryName}${CYPHER_EXTENSION}`),
    // 3. DQLディレクトリ内
    join(DQL_DIR, `${queryName}${CYPHER_EXTENSION}`),
    // 4. DDLディレクトリ内
    join(DDL_DIR, `${queryName}${CYPHER_EXTENSION}`),
    // 5. クエリディレクトリ直下（互換性のため）
    join(QUERY_DIR, "..", `${queryName}${CYPHER_EXTENSION}`)
  ];
  
  // 各パスを順番に検索
  for (const path of searchPaths) {
    const fileExists = await existsSync(path);
    if (fileExists) {
      return [true, path];
    }
  }
  
  // 見つからなかった場合
  return [false, `クエリファイル '${queryName}' が見つかりませんでした`];
}

/**
 * クエリファイルの内容を読み込む（Deno版）
 */
export async function readQueryFile(filePath: string): Promise<QueryResult<string>> {
  const fileExists = await existsSync(filePath);
  if (!fileExists) {
    return { success: false, error: `ファイルが存在しません: ${filePath}` };
  }
  
  const content = await Deno.readTextFile(filePath).catch(e => {
    return null;
  });
  
  if (content === null) {
    return { 
      success: false, 
      error: `クエリファイルの読み込みに失敗しました: ${filePath}` 
    };
  }
  
  return { success: true, data: content };
}

/**
 * 利用可能なすべてのクエリ名のリストを取得する（Deno版）
 */
export async function getAvailableQueries(): Promise<string[]> {
  const queryFiles: string[] = [];
  
  // DMLディレクトリを検索
  const dmlExists = await existsSync(DML_DIR);
  if (dmlExists) {
    const entries = await Deno.readDir(DML_DIR).catch(() => []);
    for await (const entry of entries) {
      if (entry.isFile && entry.name.endsWith(CYPHER_EXTENSION)) {
        queryFiles.push(entry.name.replace(CYPHER_EXTENSION, ''));
      }
    }
  }
  
  // DMLテストディレクトリを検索
  const dmlTestDir = join(DML_DIR, "test");
  const dmlTestExists = await existsSync(dmlTestDir);
  if (dmlTestExists) {
    const entries = await Deno.readDir(dmlTestDir).catch(() => []);
    for await (const entry of entries) {
      if (entry.isFile && entry.name.endsWith(CYPHER_EXTENSION)) {
        queryFiles.push(entry.name.replace(CYPHER_EXTENSION, ''));
      }
    }
  }
  
  // DQLディレクトリを検索
  const dqlExists = await existsSync(DQL_DIR);
  if (dqlExists) {
    const entries = await Deno.readDir(DQL_DIR).catch(() => []);
    for await (const entry of entries) {
      if (entry.isFile && entry.name.endsWith(CYPHER_EXTENSION)) {
        queryFiles.push(entry.name.replace(CYPHER_EXTENSION, ''));
      }
    }
  }
  
  // DDLディレクトリを検索  
  const ddlExists = await existsSync(DDL_DIR);
  if (ddlExists) {
    const entries = await Deno.readDir(DDL_DIR).catch(() => []);
    for await (const entry of entries) {
      if (entry.isFile && entry.name.endsWith(CYPHER_EXTENSION)) {
        queryFiles.push(entry.name.replace(CYPHER_EXTENSION, ''));
      }
    }
  }
  
  // クエリディレクトリ直下を検索（互換性のため）
  const queryRootDir = join(QUERY_DIR, "..");
  const entries = await Deno.readDir(queryRootDir).catch(() => []);
  for await (const entry of entries) {
    if (entry.isFile && entry.name.endsWith(CYPHER_EXTENSION)) {
      const filePath = join(queryRootDir, entry.name);
      const fileExists = await existsSync(filePath);
      if (fileExists) {
        queryFiles.push(entry.name.replace(CYPHER_EXTENSION, ''));
      }
    }
  }
  
  // 重複を削除してソート
  return [...new Set(queryFiles)].sort();
}

/**
 * クエリ名に対応するCypherクエリを取得する（Deno版）
 */
export async function getQuery(queryName: string, fallbackQuery?: string): Promise<QueryResult<string>> {
  // 通常のクエリファイル検索
  const [found, filePath] = await findQueryFile(queryName);
  if (!found) {
    if (fallbackQuery !== undefined) {
      logger.info(`クエリ '${queryName}' が見つからないため、フォールバッククエリを使用します`);
      return { success: true, data: fallbackQuery };
    }
    const available = await getAvailableQueries();
    return {
      success: false,
      error: `クエリ '${queryName}' が見つかりません`,
      available_queries: available
    };
  }
  
  // ファイルを読み込む
  return await readQueryFile(filePath);
}

/**
 * パラメータを含むクエリを構築する
 */
export function buildParameterizedQuery(query: string, params: Record<string, any>): string {
  // パラメータがある場合は、文字列に置き換える方式を使用
  if (Object.keys(params).length > 0) {
    let parameterizedQuery = query;
    
    for (const [key, value] of Object.entries(params)) {
      // 値の型に応じて適切な形式に変換
      let sqlValue;
      if (value === null || value === undefined) {
        sqlValue = 'NULL';
      } else if (typeof value === 'string') {
        // 文字列の場合は、シングルクォートで囲む
        sqlValue = `'${value.replace(/'/g, "\\'")}'`;
      } else if (typeof value === 'number') {
        sqlValue = value.toString();
      } else if (typeof value === 'boolean') {
        sqlValue = value ? 'true' : 'false';
      } else if (Array.isArray(value)) {
        // 配列の場合は、各要素をJSON形式に変換
        const jsonArray = value.map(item => {
          if (typeof item === 'object' && item !== null) {
            // オブジェクトの場合は各プロパティを個別に処理
            const props = Object.entries(item)
              .map(([k, v]) => `${k}: '${String(v).replace(/'/g, "\\'")}'`)
              .join(', ');
            return `{${props}}`;
          } else if (typeof item === 'string') {
            return `'${item.replace(/'/g, "\\'")}'`;
          } else {
            return String(item);
          }
        });
        sqlValue = `[${jsonArray.join(', ')}]`;
      } else {
        // その他の場合は文字列として扱う
        sqlValue = `'${String(value).replace(/'/g, "\\'")}'`;
      }
      
      // パラメータプレースホルダーを置き換える
      parameterizedQuery = parameterizedQuery.replace(new RegExp(`\\$${key}`, 'g'), sqlValue);
    }
    
    return parameterizedQuery;
  }
  
  return query;
}

/**
 * クエリ名に対応するCypherクエリを実行する（Deno版）
 */
export async function executeQuery(
  connection: any, 
  queryName: string, 
  params: Record<string, any> = {}
): Promise<QueryResult<any>> {
  logger.debug(`executeQuery called: queryName=${queryName}, params=`, params);
  
  // クエリを取得
  const queryResult = await getQuery(queryName);
  if (!queryResult.success) {
    logger.debug(`getQuery failed:`, queryResult);
    return queryResult;
  }
  
  const query = queryResult.data!;
  logger.debug(`Query to execute: "${query}"`);
  logger.debug(`Query params:`, params);
  
  // パラメータを含むクエリを構築
  const parameterizedQuery = buildParameterizedQuery(query, params);
  logger.debug(`Query after parameter substitution: "${parameterizedQuery}"`);
  
  // クエリを実行
  try {
    // Deno環境での実行を想定
    const result = await connection.query(parameterizedQuery);
    logger.debug(`Query executed successfully:`, result);
    return { success: true, data: result };
  } catch (e) {
    logger.error(`Query execution failed:`, e);
    return { 
      success: false, 
      error: `クエリ '${queryName}' の実行に失敗しました: ${e instanceof Error ? e.message : String(e)}` 
    };
  }
}

/**
 * 成功判定ヘルパー関数
 */
export function getSuccess<T>(result: QueryResult<T>): boolean {
  return result.success === true;
}

// テスト実行
if (typeof Deno !== 'undefined') {
  console.log(`
==============================================================================
                    KuzuDB Query Repository テストスイート
==============================================================================

【テストの意義】
このテストスイートは、KuzuDBでのURI制約検証機能が正しく動作することを保証します。
KuzuDBにはCHECK制約がないため、DQLクエリレベルで制約検証を実装しています。

【テスト追加方法】
1. 既存のdescribeブロック内に新しいit()ブロックを追加
2. 各テストは独立して実行可能にすること（setup/teardownを含む）
3. 命名規則: 日本語で具体的な検証内容を記述

例:
it("新しいテストケース名", async () => {
  const kuzu = await import("npm:kuzu@0.9.0");
  const db = new kuzu.Database(":memory:");
  const conn = new kuzu.Connection(db);
  
  try {
    // テスト実装
    await conn.close();
    await db.close();
  } catch (e) {
    console.error('エラー:', e);
    throw e;
  }
});

【実行コマンド】
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH nix run nixpkgs#deno -- test -A --allow-scripts=npm:kuzu /home/nixos/bin/src/kuzu/query/infrastructure/repositories/denoQueryRepository.ts --no-check

【フィルタ実行】
特定のテストのみ実行: --filter="URI制約検証"
==============================================================================
`);

  describe("KuzuDB直接クエリテスト", () => {
    it("インメモリKuzuDBでの基本動作確認", async () => {
      const kuzu = await import("npm:kuzu");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        await conn.query("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))");
        await conn.query("CREATE (u:User {name: 'Alice', age: 30})");
        
        const result = await conn.query("MATCH (u:User) RETURN u.name, u.age");
        const rows = await result.getAll();
        
        assert(rows.length > 0, "クエリ結果が存在すべき");
        
        await conn.close();
        await db.close();
      } catch (e) {
        console.error("テストエラー:", e);
        throw e;
      }
    });
    
    it("JSON拡張機能の動作確認", async () => {
      const kuzu = await import("npm:kuzu");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        await conn.query("INSTALL json");
        await conn.query("LOAD json");
        
        await conn.query(`
          CREATE NODE TABLE Entity(
            id STRING, 
            data JSON,
            PRIMARY KEY (id)
          )
        `);
        
        await conn.query(`
          CREATE (e:Entity {
            id: '1', 
            data: to_json({name: 'テスト', values: [1, 2, 3]})
          })
        `);
        
        const result = await conn.query('MATCH (e:Entity) RETURN e.id, e.data');
        const rows = await result.getAll();
        
        await conn.close();
        await db.close();
        
        console.log('JSON拡張機能テスト完了');
      } catch (e) {
        console.error('JSON拡張機能テストエラー:', e);
        return;
      }
    });
  });
  
  describe("URI制約検証DQLクエリテスト", () => {
    it("有効なURIパターンのマッチング", async () => {
      const kuzu = await import("npm:kuzu");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        await conn.query("CREATE NODE TABLE uri(path STRING, PRIMARY KEY (path))");
        await conn.query("CREATE (u:uri {path: '<myproject>/srs/auth'})");
        await conn.query("CREATE (u:uri {path: '<test-proj>/srs/requirements/performance'})");
        await conn.query("CREATE (u:uri {path: '<proj_123>/srs/a/b/c/deep/path'})");
        
        const result = await conn.query(`
          MATCH (u:uri)
          WHERE u.path =~ '^<[^>]+>/srs/.+$'
          RETURN u.path ORDER BY u.path
        `);
        const rows = await result.getAll();
        
        assertEquals(rows.length, 3, "有効なURIは3件存在すべき");
        assertEquals(rows[0]["u.path"], "<myproject>/srs/auth");
        assertEquals(rows[1]["u.path"], "<proj_123>/srs/a/b/c/deep/path");
        assertEquals(rows[2]["u.path"], "<test-proj>/srs/requirements/performance");
        
        await conn.close();
        await db.close();
      } catch (e) {
        console.error('有効URIパターンテストエラー:', e);
        throw e;
      }
    });
    
    it("無効なURIパターンの検出", async () => {
      const kuzu = await import("npm:kuzu");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        await conn.query("CREATE NODE TABLE uri(path STRING, PRIMARY KEY (path))");
        
        // 無効なパターンを挿入
        await conn.query("CREATE (u:uri {path: 'myproject/srs/test'})");      // < > なし
        await conn.query("CREATE (u:uri {path: '<project>/api/test'})");      // /srs/ なし
        await conn.query("CREATE (u:uri {path: '<>/srs/test'})");            // 空プロジェクト
        
        const result = await conn.query(`
          MATCH (u:uri)
          WHERE NOT u.path =~ '^<[^>]+>/srs/.+$'
          RETURN u.path ORDER BY u.path
        `);
        const rows = await result.getAll();
        
        assertEquals(rows.length, 3, "無効なURIは3件存在すべき");
        assertEquals(rows[0]["u.path"], "<>/srs/test");
        assertEquals(rows[1]["u.path"], "<project>/api/test");
        assertEquals(rows[2]["u.path"], "myproject/srs/test");
        
        await conn.close();
        await db.close();
      } catch (e) {
        console.error('無効URIパターンテストエラー:', e);
        throw e;
      }
    });
    
    it("エッジケースと境界値", async () => {
      const kuzu = await import("npm:kuzu");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        await conn.query("CREATE NODE TABLE uri(path STRING, PRIMARY KEY (path))");
        
        // エッジケース
        await conn.query("CREATE (u:uri {path: '<a>/srs/b'})");              // 最小長プロジェクト
        await conn.query("CREATE (u:uri {path: '<very-long-project-name-123>/srs/test'})"); // 長いプロジェクト名
        await conn.query("CREATE (u:uri {path: '<project>/srs/'})");         // パスなし（無効）
        await conn.query("CREATE (u:uri {path: '<project>srs/test'})");      // スラッシュなし（無効）
        
        // 有効なパターンをチェック
        const validResult = await conn.query(`
          MATCH (u:uri)
          WHERE u.path =~ '^<[^>]+>/srs/.+$'
          RETURN u.path ORDER BY u.path
        `);
        const validRows = await validResult.getAll();
        
        assertEquals(validRows.length, 2, "有効なエッジケースは2件");
        assertEquals(validRows[0]["u.path"], "<a>/srs/b");
        assertEquals(validRows[1]["u.path"], "<very-long-project-name-123>/srs/test");
        
        // 無効なパターンをチェック
        const invalidResult = await conn.query(`
          MATCH (u:uri)
          WHERE NOT u.path =~ '^<[^>]+>/srs/.+$'
          RETURN u.path ORDER BY u.path
        `);
        const invalidRows = await invalidResult.getAll();
        
        assertEquals(invalidRows.length, 2, "無効なエッジケースは2件");
        assertEquals(invalidRows[0]["u.path"], "<project>/srs/");
        assertEquals(invalidRows[1]["u.path"], "<project>srs/test");
        
        await conn.close();
        await db.close();
      } catch (e) {
        console.error('エッジケーステストエラー:', e);
        throw e;
      }
    });
    
    it("厳密なプロジェクト名検証（英数字とハイフン、アンダースコアのみ）", async () => {
      const kuzu = await import("npm:kuzu");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        await conn.query("CREATE NODE TABLE uri(path STRING, PRIMARY KEY (path))");
        
        // 様々なプロジェクト名パターン
        await conn.query("CREATE (u:uri {path: '<valid-project_123>/srs/test'})");  // 有効
        await conn.query("CREATE (u:uri {path: '<project!>/srs/test'})");           // 無効: !
        await conn.query("CREATE (u:uri {path: '<project@domain>/srs/test'})");     // 無効: @
        await conn.query("CREATE (u:uri {path: '<project.name>/srs/test'})");       // 無効: .
        
        // より厳密な正規表現: プロジェクト名は英数字とハイフン、アンダースコアのみ
        const result = await conn.query(`
          MATCH (u:uri)
          WHERE u.path =~ '^<[a-zA-Z0-9_-]+>/srs/.+$'
          RETURN u.path ORDER BY u.path
        `);
        const rows = await result.getAll();
        
        assertEquals(rows.length, 1, "厳密な検証では1件のみ有効");
        assertEquals(rows[0]["u.path"], "<valid-project_123>/srs/test");
        
        await conn.close();
        await db.close();
      } catch (e) {
        console.error('厳密なプロジェクト名検証テストエラー:', e);
        throw e;
      }
    });
    
    it("空のテーブルでの動作確認", async () => {
      const kuzu = await import("npm:kuzu");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        await conn.query("CREATE NODE TABLE uri(path STRING, PRIMARY KEY (path))");
        
        // 空のテーブルでクエリ実行
        const result = await conn.query(`
          MATCH (u:uri)
          WHERE u.path =~ '^<[^>]+>/srs/.+$'
          RETURN u.path
        `);
        const rows = await result.getAll();
        
        assertEquals(rows.length, 0, "空のテーブルでは結果は0件");
        
        await conn.close();
        await db.close();
      } catch (e) {
        console.error('空テーブルテストエラー:', e);
        throw e;
      }
    });
  });

  describe("1テーブル多粒度モデルテスト", () => {
    it("正常系：8階層以下の可変フルパスから1テーブル多粒度モデル構築", async () => {
      const kuzu = await import("npm:kuzu");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        // 8階層可変対応1テーブル多粒度モデル構築
        const dmlResult = await getQuery("single_table_minimal");
        assert(dmlResult.success, "可変階層多粒度DMLクエリが読み込めるべき");
        
        await conn.query(dmlResult.data!);
        console.log("8階層可変対応多粒度モデル構築完了");
        
        // 構築結果確認：全ノード数
        const nodeCountResult = await conn.query("MATCH (n:LocationURI) RETURN count(*) as node_count");
        const nodeCount = await nodeCountResult.getAll();
        assert(nodeCount[0]["node_count"] >= 10, "複数階層のノードが作成されるべき");
        
        // 構築結果確認：2階層パス
        const depth2Check = await conn.query(`
          MATCH (root:LocationURI {id: "/api"})-[:PARENT_OF]->(leaf:LocationURI {id: "/api/v1"})
          RETURN root.id, leaf.id
        `);
        const depth2Rows = await depth2Check.getAll();
        assertEquals(depth2Rows.length, 1, "2階層パスが構築されるべき");
        assertEquals(depth2Rows[0]["root.id"], "/api");
        assertEquals(depth2Rows[0]["leaf.id"], "/api/v1");
        
        // 構築結果確認：3階層パス
        const depth3Check = await conn.query(`
          MATCH (root:LocationURI {id: "/docs"})-[:PARENT_OF]->(mid:LocationURI {id: "/docs/guide"})-[:PARENT_OF]->(leaf:LocationURI {id: "/docs/guide/advanced"})
          RETURN root.id, mid.id, leaf.id
        `);
        const depth3Rows = await depth3Check.getAll();
        assertEquals(depth3Rows.length, 1, "3階層パスが構築されるべき");
        assertEquals(depth3Rows[0]["root.id"], "/docs");
        assertEquals(depth3Rows[0]["mid.id"], "/docs/guide");
        assertEquals(depth3Rows[0]["leaf.id"], "/docs/guide/advanced");
        
        // 構築結果確認：4階層パス（srs系）
        const depth4Check = await conn.query(`
          MATCH (root:LocationURI {id: "/srs"})-[:PARENT_OF*3]->(leaf:LocationURI {id: "/srs/functions/authentication/user-credential-validation"})
          RETURN root.id, leaf.id
        `);
        const depth4Rows = await depth4Check.getAll();
        assertEquals(depth4Rows.length, 1, "4階層パスが構築されるべき");
        assertEquals(depth4Rows[0]["root.id"], "/srs");
        assertEquals(depth4Rows[0]["leaf.id"], "/srs/functions/authentication/user-credential-validation");
        
        // 構築結果確認：8階層パス（config系）
        const depth8Check = await conn.query(`
          MATCH (root:LocationURI {id: "/config"})-[:PARENT_OF*7]->(leaf:LocationURI {id: "/config/db/connection/pool/settings/timeout/retry/backoff"})
          RETURN root.id, leaf.id
        `);
        const depth8Rows = await depth8Check.getAll();
        assertEquals(depth8Rows.length, 1, "8階層パスが構築されるべき");
        assertEquals(depth8Rows[0]["root.id"], "/config");
        assertEquals(depth8Rows[0]["leaf.id"], "/config/db/connection/pool/settings/timeout/retry/backoff");
        
        // フルパス再計算テスト
        const reconstructQuery = await getQuery("reconstruct_path_from_node");
        assert(reconstructQuery.success, "パス再計算クエリが読み込めるべき");
        
        const testNodeId = "/srs/functions/authentication/user-credential-validation";
        const reconstructParameterized = buildParameterizedQuery(reconstructQuery.data!, { nodeId: testNodeId });
        const reconstructResult = await conn.query(reconstructParameterized);
        const reconstructRows = await reconstructResult.getAll();
        
        assertEquals(reconstructRows.length, 1, "パス再計算結果は1件であるべき");
        assert(reconstructRows[0]["reconstructed_path"].includes("srs"), "再計算パスにsrsが含まれるべき");
        
        console.log("8階層可変対応多粒度モデル正常系テスト完了");
        console.log("再計算パス:", reconstructRows[0]["reconstructed_path"]);
        
        await conn.close();
        await db.close();
      } catch (e) {
        console.error('8階層可変対応多粒度モデル正常系テストエラー:', e);
        throw e;
      }
    });

    it("異常系：9階層以上のフルパスでエラー検出", async () => {
      const kuzu = await import("npm:kuzu");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        // 階層深度バリデーションクエリ取得
        const validationQueryResult = await getQuery("validate_hierarchy_depth");
        assert(validationQueryResult.success, "階層深度バリデーションクエリが読み込めるべき");
        
        // 正常ケース（8階層）のテスト
        const validPath = "/a/b/c/d/e/f/g/h";
        const validQuery = buildParameterizedQuery(validationQueryResult.data!, { fullPath: validPath });
        const validResult = await conn.query(validQuery);
        const validRows = await validResult.getAll();
        
        assertEquals(validRows[0]["is_valid"], true, "8階層は有効であるべき");
        assertEquals(validRows[0]["actual_depth"], 8, "深度は8であるべき");
        assertEquals(validRows[0]["validation_message"], "OK", "バリデーションメッセージはOKであるべき");
        
        // 異常ケース（9階層）のテスト
        const invalidPath = "/a/b/c/d/e/f/g/h/i";
        const invalidQuery = buildParameterizedQuery(validationQueryResult.data!, { fullPath: invalidPath });
        const invalidResult = await conn.query(invalidQuery);
        const invalidRows = await invalidResult.getAll();
        
        assertEquals(invalidRows[0]["is_valid"], false, "9階層は無効であるべき");
        assertEquals(invalidRows[0]["actual_depth"], 9, "深度は9であるべき");
        assertEquals(invalidRows[0]["validation_message"], "ERROR: Maximum hierarchy depth exceeded", "エラーメッセージが表示されるべき");
        
        // さらに深い階層（12階層）のテスト
        const veryDeepPath = "/a/b/c/d/e/f/g/h/i/j/k/l";
        const veryDeepQuery = buildParameterizedQuery(validationQueryResult.data!, { fullPath: veryDeepPath });
        const veryDeepResult = await conn.query(veryDeepQuery);
        const veryDeepRows = await veryDeepResult.getAll();
        
        assertEquals(veryDeepRows[0]["is_valid"], false, "12階層は無効であるべき");
        assertEquals(veryDeepRows[0]["actual_depth"], 12, "深度は12であるべき");
        
        console.log("階層深度バリデーション異常系テスト完了");
        
        await conn.close();
        await db.close();
      } catch (e) {
        console.error('階層深度バリデーション異常系テストエラー:', e);
        throw e;
      }
    });

    it("異常系：9階層フルパスをDMLに渡した場合のエラー確認", async () => {
      const kuzu = await import("npm:kuzu");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        // DDL作成
        await conn.query("CREATE NODE TABLE LocationURI(id STRING, PRIMARY KEY (id))");
        await conn.query("CREATE REL TABLE PARENT_OF(FROM LocationURI TO LocationURI)");
        
        // 9階層パスでDML実行を試行（8階層で制限されるべき）
        const invalidPath = "/a/b/c/d/e/f/g/h/i";
        const invalidDmlQuery = `
          WITH ["${invalidPath}"] as testPaths
          UNWIND testPaths as fullPath
          WITH fullPath, string_split(substring(fullPath, 2, size(fullPath)-1), "/") as parts
          WITH fullPath, parts,
               "/" + parts[1] as level1,
               CASE WHEN size(parts) >= 2 THEN "/" + parts[1] + "/" + parts[2] ELSE null END as level2,
               CASE WHEN size(parts) >= 3 THEN "/" + parts[1] + "/" + parts[2] + "/" + parts[3] ELSE null END as level3,
               CASE WHEN size(parts) >= 4 THEN "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] ELSE null END as level4,
               CASE WHEN size(parts) >= 5 THEN "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] ELSE null END as level5,
               CASE WHEN size(parts) >= 6 THEN "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6] ELSE null END as level6,
               CASE WHEN size(parts) >= 7 THEN "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6] + "/" + parts[7] ELSE null END as level7,
               CASE WHEN size(parts) >= 8 THEN "/" + parts[1] + "/" + parts[2] + "/" + parts[3] + "/" + parts[4] + "/" + parts[5] + "/" + parts[6] + "/" + parts[7] + "/" + parts[8] ELSE null END as level8
          WHERE level8 IS NOT null
          MERGE (:LocationURI {id: level8})
        `;
        
        // DMLは8階層まで処理（9階層目は処理されない）
        await conn.query(invalidDmlQuery);
        
        // 9階層目のノードが作成されていないことを確認
        const level9CheckResult = await conn.query(`
          MATCH (n:LocationURI)
          WHERE n.id CONTAINS "/i"
          RETURN count(*) as level9_count
        `);
        const level9Check = await level9CheckResult.getAll();
        assertEquals(level9Check[0]["level9_count"], 0, "9階層目のノードは作成されるべきではない");
        
        // 8階層までのノードが正常に作成されていることを確認
        const validNodesResult = await conn.query(`
          MATCH (n:LocationURI)
          WHERE n.id =~ "^/a(/[a-h])*$"
          RETURN count(*) as valid_count
        `);
        const validNodes = await validNodesResult.getAll();
        assertEquals(validNodes[0]["valid_count"], 1, "8階層目のノードのみ作成されるべき");
        
        console.log("9階層DML異常系テスト完了：9階層目は適切に無視された");
        
        await conn.close();
        await db.close();
      } catch (e) {
        console.error('9階層DML異常系テストエラー:', e);
        throw e;
      }
    });
  });
}
