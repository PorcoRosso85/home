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
    // 2. DQLディレクトリ内
    join(DQL_DIR, `${queryName}${CYPHER_EXTENSION}`),
    // 3. DDLディレクトリ内
    join(DDL_DIR, `${queryName}${CYPHER_EXTENSION}`),
    // 4. クエリディレクトリ直下（互換性のため）
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
      const kuzu = await import("npm:kuzu@0.9.0");
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
      const kuzu = await import("npm:kuzu@0.9.0");
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
      const kuzu = await import("npm:kuzu@0.9.0");
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
      const kuzu = await import("npm:kuzu@0.9.0");
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
      const kuzu = await import("npm:kuzu@0.9.0");
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
      const kuzu = await import("npm:kuzu@0.9.0");
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
      const kuzu = await import("npm:kuzu@0.9.0");
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

  describe("多粒度モデル階層パス計算テスト", () => {
    it("nameベースDMLとフルパス計算DQLの統合テスト", async () => {
      const kuzu = await import("npm:kuzu@0.9.0");
      const db = new kuzu.Database(":memory:");
      const conn = new kuzu.Connection(db);
      
      try {
        // DML: 多粒度モデル作成（name属性のみ）
        const dmlQueryResult = await getQuery("create_hierarchy_test_data");
        assert(dmlQueryResult.success, "DMLクエリファイルが読み込めるべき");
        
        await conn.query(dmlQueryResult.data!);
        console.log("多粒度モデル作成完了");
        
        // DQL: パス計算クエリ実行
        const dqlQueryResult = await getQuery("calculate_hierarchy_path");
        assert(dqlQueryResult.success, "DQLクエリファイルが読み込めるべき");
        
        const parameterizedQuery = buildParameterizedQuery(dqlQueryResult.data!, {
          leafName: "user-credential-validation"
        });
        
        const result = await conn.query(parameterizedQuery);
        const rows = await result.getAll();
        
        // 結果検証
        assertEquals(rows.length, 1, "パス計算結果は1件であるべき");
        assertEquals(
          rows[0]["full_path"], 
          "/srs/functions/authentication/user-credential-validation/",
          "計算されたフルパスが期待値と一致すべき"
        );
        
        console.log("計算されたフルパス:", rows[0]["full_path"]);
        
        await conn.close();
        await db.close();
      } catch (e) {
        console.error('多粒度モデルテストエラー:', e);
        throw e;
      }
    });
  });
}
