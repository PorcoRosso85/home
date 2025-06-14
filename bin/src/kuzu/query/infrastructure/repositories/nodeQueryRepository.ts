/**
 * KuzuDB Node.js Query Repository
 * 
 * Node.js環境でKuzuDBクエリを実行するための関数群
 */

import { readFileSync, existsSync, readdirSync } from "fs";
import { join, parse, dirname } from "path";
import * as logger from '../../../common/infrastructure/logger';

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
 * クエリファイルを検索する（Node.js版）
 */
export function findQueryFile(queryName: string): [boolean, string] {
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
    if (existsSync(path)) {
      return [true, path];
    }
  }
  
  // 見つからなかった場合
  return [false, `クエリファイル '${queryName}' が見つかりませんでした`];
}

/**
 * クエリファイルの内容を読み込む（Node.js版）
 */
export function readQueryFile(filePath: string): QueryResult<string> {
  try {
    if (!existsSync(filePath)) {
      return { success: false, error: `ファイルが存在しません: ${filePath}` };
    }
    
    const content = readFileSync(filePath, { encoding: "utf-8" });
    return { success: true, data: content };
  } catch (e) {
    return { 
      success: false, 
      error: `クエリファイルの読み込みに失敗しました: ${filePath} - ${e instanceof Error ? e.message : String(e)}` 
    };
  }
}

/**
 * 利用可能なすべてのクエリ名のリストを取得する（Node.js版）
 */
export function getAvailableQueries(): string[] {
  const queryFiles: string[] = [];
  
  // DMLディレクトリを検索
  if (existsSync(DML_DIR)) {
    readdirSync(DML_DIR)
      .filter(file => file.endsWith(CYPHER_EXTENSION))
      .forEach(file => {
        queryFiles.push(parse(file).name);
      });
  }
  
  // DQLディレクトリを検索
  if (existsSync(DQL_DIR)) {
    readdirSync(DQL_DIR)
      .filter(file => file.endsWith(CYPHER_EXTENSION))
      .forEach(file => {
        queryFiles.push(parse(file).name);
      });
  }
  
  // DDLディレクトリを検索
  if (existsSync(DDL_DIR)) {
    readdirSync(DDL_DIR)
      .filter(file => file.endsWith(CYPHER_EXTENSION))
      .forEach(file => {
        queryFiles.push(parse(file).name);
      });
  }
  
  // クエリディレクトリ直下を検索（互換性のため）
  const queryRootDir = join(QUERY_DIR, "..");
  readdirSync(queryRootDir)
    .filter(file => file.endsWith(CYPHER_EXTENSION) && existsSync(join(queryRootDir, file)))
    .forEach(file => {
      queryFiles.push(parse(file).name);
    });
  
  // 重複を削除してソート
  return [...new Set(queryFiles)].sort();
}

/**
 * クエリ名に対応するCypherクエリを取得する（Node.js版）
 */
export function getQuery(queryName: string, fallbackQuery?: string): QueryResult<string> {
  // 通常のクエリファイル検索
  const [found, filePath] = findQueryFile(queryName);
  if (!found) {
    if (fallbackQuery !== undefined) {
      logger.info(`クエリ '${queryName}' が見つからないため、フォールバッククエリを使用します`);
      return { success: true, data: fallbackQuery };
    }
    const available = getAvailableQueries();
    return {
      success: false,
      error: `クエリ '${queryName}' が見つかりません`,
      available_queries: available
    };
  }
  
  // ファイルを読み込む
  return readQueryFile(filePath);
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
 * クエリ名に対応するCypherクエリを実行する（Node.js版）
 */
export async function executeQuery(
  connection: any, 
  queryName: string, 
  params: Record<string, any> = {}
): Promise<QueryResult<any>> {
  logger.debug(`executeQuery called: queryName=${queryName}, params=`, params);
  
  // クエリを取得
  const queryResult = getQuery(queryName);
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
    // Node.js環境での実行を想定
    const result = await connection.executeQuery(parameterizedQuery);
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
