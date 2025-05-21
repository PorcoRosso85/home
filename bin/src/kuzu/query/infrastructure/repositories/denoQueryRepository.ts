/**
 * KuzuDB Deno Query Repository
 * 
 * Deno環境でKuzuDBクエリを実行するための関数群
 */

import { existsSync } from "https://deno.land/std@0.224.0/fs/mod.ts";
import { join, dirname } from "https://deno.land/std@0.224.0/path/mod.ts";

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
    try {
      if (await existsSync(path)) {
        return [true, path];
      }
    } catch {
      continue;
    }
  }
  
  // 見つからなかった場合
  return [false, `クエリファイル '${queryName}' が見つかりませんでした`];
}

/**
 * クエリファイルの内容を読み込む（Deno版）
 */
export async function readQueryFile(filePath: string): Promise<QueryResult<string>> {
  try {
    if (!await existsSync(filePath)) {
      return { success: false, error: `ファイルが存在しません: ${filePath}` };
    }
    
    const content = await Deno.readTextFile(filePath);
    return { success: true, data: content };
  } catch (e) {
    return { 
      success: false, 
      error: `クエリファイルの読み込みに失敗しました: ${filePath} - ${e instanceof Error ? e.message : String(e)}` 
    };
  }
}

/**
 * 利用可能なすべてのクエリ名のリストを取得する（Deno版）
 */
export async function getAvailableQueries(): Promise<string[]> {
  const queryFiles: string[] = [];
  
  // DMLディレクトリを検索
  try {
    if (await existsSync(DML_DIR)) {
      for await (const entry of Deno.readDir(DML_DIR)) {
        if (entry.isFile && entry.name.endsWith(CYPHER_EXTENSION)) {
          queryFiles.push(entry.name.replace(CYPHER_EXTENSION, ''));
        }
      }
    }
  } catch (e) {
    logger.warn(`ディレクトリ読み込み失敗: ${DML_DIR}`, e);
  }
  
  // DQLディレクトリを検索
  try {
    if (await existsSync(DQL_DIR)) {
      for await (const entry of Deno.readDir(DQL_DIR)) {
        if (entry.isFile && entry.name.endsWith(CYPHER_EXTENSION)) {
          queryFiles.push(entry.name.replace(CYPHER_EXTENSION, ''));
        }
      }
    }
  } catch (e) {
    logger.warn(`ディレクトリ読み込み失敗: ${DQL_DIR}`, e);
  }
  
  // DDLディレクトリを検索
  try {
    if (await existsSync(DDL_DIR)) {
      for await (const entry of Deno.readDir(DDL_DIR)) {
        if (entry.isFile && entry.name.endsWith(CYPHER_EXTENSION)) {
          queryFiles.push(entry.name.replace(CYPHER_EXTENSION, ''));
        }
      }
    }
  } catch (e) {
    logger.warn(`ディレクトリ読み込み失敗: ${DDL_DIR}`, e);
  }
  
  // クエリディレクトリ直下を検索（互換性のため）
  try {
    const queryRootDir = join(QUERY_DIR, "..");
    for await (const entry of Deno.readDir(queryRootDir)) {
      if (entry.isFile && entry.name.endsWith(CYPHER_EXTENSION)) {
        const filePath = join(queryRootDir, entry.name);
        if (await existsSync(filePath)) {
          queryFiles.push(entry.name.replace(CYPHER_EXTENSION, ''));
        }
      }
    }
  } catch (e) {
    logger.warn(`クエリルートディレクトリ読み込み失敗`, e);
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
  // インメモリKuzuDBでの直接クエリテスト
  Deno.test("インメモリKuzuDBでの直接クエリテスト", async () => {
    // KuzuDBモジュールをインポート
    const kuzu = await import("npm:kuzu@0.9.0");
    
    // インメモリデータベースを作成
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      // スキーマ作成
      await conn.query("CREATE NODE TABLE User(name STRING, age INT64, PRIMARY KEY (name))");
      
      // データ挿入
      await conn.query("CREATE (u:User {name: 'Alice', age: 30})");
      
      // クエリ実行
      const result = await conn.query("MATCH (u:User) RETURN u.name, u.age");
      const rows = await result.getAll();
      
      // 結果確認
      console.assert(rows.length > 0, "クエリ結果が存在すべき");
      
      // 後処理
      await conn.close();
      await db.close();
    } catch (e) {
      console.error("テストエラー:", e);
      throw e;
    }
  });
  
  // JSON拡張機能の動作確認テスト
  Deno.test("KuzuDB JSON拡張機能テスト", async () => {
    // KuzuDBモジュールをインポート
    const kuzu = await import("npm:kuzu@0.9.0");
    
    // インメモリデータベースを作成
    const db = new kuzu.Database(":memory:");
    const conn = new kuzu.Connection(db);
    
    try {
      // JSON拡張機能のセットアップ
      await conn.query("INSTALL json");
      await conn.query("LOAD json");
      
      // JSON型を使ったNodeテーブルの作成
      await conn.query(`
        CREATE NODE TABLE Entity(
          id STRING, 
          data JSON,
          PRIMARY KEY (id)
        )
      `);
      
      // テストデータの挿入
      await conn.query(`
        CREATE (e:Entity {
          id: '1', 
          data: to_json({name: 'テスト', values: [1, 2, 3]})
        })
      `);
      
      // データの確認
      const result = await conn.query('MATCH (e:Entity) RETURN e.id, e.data');
      const rows = await result.getAll();
      
      // 後処理
      await conn.close();
      await db.close();
    } catch (e) {
      console.error('JSON拡張機能テストエラー:', e);
      throw e;
    }
  });
}
