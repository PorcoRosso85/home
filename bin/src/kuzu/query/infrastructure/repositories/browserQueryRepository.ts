/**
 * KuzuDB Browser Query Repository
 * 
 * ブラウザ環境でKuzuDBクエリを実行するための関数群
 */

import * as logger from '../../../common/infrastructure/logger';

// 型定義
export type QueryResult<T> = {
  success: boolean;
  data?: T;
  error?: string;
  available_queries?: string[];
};

/**
 * クエリファイルを検索する（ブラウザ版）
 * @param queryName クエリファイル名（拡張子なし）
 * @param directory ディレクトリを明示的に指定（ddl, dml, dql）
 */
export async function findQueryFile(queryName: string, directory: 'ddl' | 'dml' | 'dql'): Promise<[boolean, string]> {
  // 指定されたディレクトリのみを検索
  const searchPath = `/${directory}/${queryName}.cypher`;
  
  try {
    const response = await fetch(searchPath);
    if (response.ok) {
      return [true, searchPath];
    }
  } catch (e) {
    // 無視
  }
  
  // 見つからなかった場合は即エラー
  return [false, `クエリファイル '${queryName}' が見つかりませんでした（${searchPath}を検索）`];
}

/**
 * クエリファイルの内容を読み込む（ブラウザ版）
 */
export async function readQueryFile(filePath: string): Promise<QueryResult<string>> {
  try {
    const response = await fetch(filePath);
    if (!response.ok) {
      return { success: false, error: `ファイルの読み込みに失敗しました: ${filePath} (${response.status})` };
    }
    
    const content = await response.text();
    return { success: true, data: content };
  } catch (e) {
    return { 
      success: false, 
      error: `クエリファイルの読み込みに失敗しました: ${filePath} - ${e instanceof Error ? e.message : String(e)}` 
    };
  }
}

/**
 * 利用可能なすべてのクエリ名のリストを取得する（ブラウザ版）
 */
export async function getAvailableQueries(): Promise<string[]> {
  const queryFiles: string[] = [];
  const directories = ['ddl', 'dml', 'dql'];
  
  for (const dir of directories) {
    try {
      const response = await fetch(`/${dir}/`);
      if (response.ok) {
        const files = await response.json();
        for (const file of files) {
          if (typeof file === 'string' && file.endsWith('.cypher')) {
            queryFiles.push(file.replace('.cypher', ''));
          }
        }
      }
    } catch (e) {
      // ディレクトリが存在しないか読み込みエラー
      logger.warn(`ディレクトリ ${dir} の読み込みに失敗しました:`, e);
    }
  }
  
  // 重複を削除してソート
  return [...new Set(queryFiles)].sort();
}

/**
 * クエリ名に対応するCypherクエリを取得する（ブラウザ版）
 * @param queryName クエリファイル名（拡張子なし）
 * @param directory ディレクトリを明示的に指定（ddl, dml, dql）
 */
export async function getQuery(queryName: string, directory: 'ddl' | 'dml' | 'dql'): Promise<QueryResult<string>> {
  // 指定されたディレクトリでクエリファイルを検索
  const [found, filePath] = await findQueryFile(queryName, directory);
  if (!found) {
    const available = await getAvailableQueries();
    throw new Error(`クエリ '${queryName}' が見つかりません（${directory}を検索）。利用可能なクエリ: ${available.join(', ')}`);
  }
  
  // ファイルを読み込む
  const result = await readQueryFile(filePath);
  if (!result.success) {
    throw new Error(result.error);
  }
  
  return result;
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
 * クエリ名に対応するCypherクエリを実行する（ブラウザ版）
 * @param connection データベース接続
 * @param queryName クエリファイル名（拡張子なし）
 * @param directory ディレクトリを明示的に指定（ddl, dml, dql）
 * @param params クエリパラメータ
 */
export async function executeQuery(
  connection: any, 
  queryName: string,
  directory: 'ddl' | 'dml' | 'dql',
  params: Record<string, any> = {}
): Promise<QueryResult<any>> {
  logger.debug(`executeQuery called: queryName=${queryName}, directory=${directory}, params=`, params);
  
  // クエリを取得
  try {
    const queryResult = await getQuery(queryName, directory);
    const query = queryResult.data!;
    logger.debug(`Query to execute: "${query}"`);
    logger.debug(`Query params:`, params);
    
    // パラメータを含むクエリを構築
    const parameterizedQuery = buildParameterizedQuery(query, params);
    logger.debug(`Query after parameter substitution: "${parameterizedQuery}"`);
    
    // クエリを実行
    const result = await connection.query(parameterizedQuery);
    logger.debug(`Query executed successfully:`, result);
    return { success: true, data: result };
  } catch (e) {
    logger.error(`Query execution failed:`, e);
    throw new Error(`クエリ '${queryName}' の実行に失敗しました: ${e instanceof Error ? e.message : String(e)}`);
  }
}

/**
 * 成功判定ヘルパー関数
 */
export function getSuccess<T>(result: QueryResult<T>): boolean {
  return result.success === true;
}

// validateDMLParameters: Phase 2で統合バリデーションシステムに移行済み
// 新しいバリデーションは integratedValidationRepository.ts を使用

/**
 * DDL系クエリを実行する関数
 */
export async function executeDDLQuery(
  connection: any,
  queryName: string,
  params: Record<string, any> = {}
): Promise<QueryResult<any>> {
  return executeQuery(connection, queryName, 'ddl', params);
}

/**
 * DML系クエリを実行する関数
 */
export async function executeDMLQuery(
  connection: any,
  queryName: string,
  params: Record<string, any> = {}
): Promise<QueryResult<any>> {
  // 新しい統合バリデーションシステムを使用
  const { validateTemplateParameters, handleValidationResult } = await import('./integratedValidationRepository');
  
  const validationResult = await validateTemplateParameters(queryName, params);
  handleValidationResult(validationResult);
  
  return executeQuery(connection, queryName, 'dml', params);
}

/**
 * DQL系クエリを実行する関数
 */
export async function executeDQLQuery(
  connection: any,
  queryName: string,
  params: Record<string, any> = {}
): Promise<QueryResult<any>> {
  return executeQuery(connection, queryName, 'dql', params);
}
