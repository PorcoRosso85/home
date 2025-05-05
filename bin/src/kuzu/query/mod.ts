/**
 * 階層型トレーサビリティモデル 基本モジュール
 */

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";

// 定数の抽象化
export const DML_DIR_NAME = "dml";  // DMLクエリのディレクトリ名
export const DQL_DIR_NAME = "dql";  // DQLクエリのディレクトリ名
export const DDL_DIR_NAME = "ddl";  // DDLクエリのディレクトリ名
export const QUERIES_DIR_NAME = "queries";  // 旧クエリディレクトリ名
export const QUERY_FILE_EXTENSION = ".cypher";  // クエリファイルの拡張子
export const BASE_QUERY_DIR = "/home/nixos/bin/src/kuzu/query/tests";  // クエリベースディレクトリ

// 型定義
export interface LocationURI {
  uri_id: string;
  scheme: string;
  authority: string;
  path: string;
  fragment: string;
  query: string;
}

export interface CodeEntity {
  persistent_id: string;
  name: string;
  type: string;
  signature: string;
  complexity: number;
  start_position: number;
  end_position: number;
}

export interface RequirementEntity {
  id: string;
  title: string;
  description: string;
  priority: string;
  requirement_type: string;
}

// クエリタイプの型定義
export type QueryType = 'dml' | 'dql' | 'ddl';

// エラー型の定義
export interface FileNotFoundError {
  code: "FILE_NOT_FOUND";
  message: string;
  filePath?: string;
  availableFiles?: string[];
}

export interface QueryNotFoundError {
  code: "QUERY_NOT_FOUND";
  message: string;
  queryName: string;
  fileName: string;
  availableQueries?: string[];
}

export interface InvalidQueryTypeError {
  code: "INVALID_QUERY_TYPE";
  message: string;
  queryType: string;
  validTypes: QueryType[];
}

export interface QueryExecutionError {
  code: "QUERY_EXECUTION_ERROR";
  message: string;
  query?: string;
  details?: string;
}

// 共用体型として定義（成功時は直接型、失敗時はエラー型）
export type QueryResult<T> = T | FileNotFoundError | QueryNotFoundError | InvalidQueryTypeError | QueryExecutionError;

// KuzuDBモジュールをロード
export async function loadKuzuModule() {
  try {
    console.log("KuzuDBモジュールをロード試行中...");
    const module = await import("kuzu");
    return module;
  } catch (error) {
    console.error("KuzuDBモジュールのロード失敗:", error);
    return null;
  }
}

// ディレクトリ存在確認・作成
export async function ensureDir(dir: string): Promise<void> {
  try {
    const stat = await Deno.stat(dir);
    if (!stat.isDirectory) {
      throw new Error(`${dir}はディレクトリではありません`);
    }
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      console.log(`${dir}ディレクトリを作成します`);
      await Deno.mkdir(dir, { recursive: true });
    } else {
      throw error;
    }
  }
}

// エラー判定関数
export function isError(result: any): result is FileNotFoundError | QueryNotFoundError | InvalidQueryTypeError | QueryExecutionError {
  return result && typeof result === 'object' && 'code' in result;
}

/**
 * 特定のディレクトリからすべてのクエリファイルを取得する関数
 * @param dirPath ディレクトリパス
 * @returns クエリファイル名の配列
 */
export async function listFilesInDir(dirPath: string): Promise<string[]> {
  try {
    const files = [];
    try {
      await Deno.stat(dirPath);
    } catch (error) {
      return []; // ディレクトリが存在しない場合は空配列を返す
    }
    
    for await (const entry of Deno.readDir(dirPath)) {
      if (entry.isFile && entry.name.endsWith(QUERY_FILE_EXTENSION)) {
        files.push(entry.name);
      }
    }
    return files;
  } catch (error) {
    console.error(`ファイルの一覧取得中にエラーが発生しました: ${error.message}`);
    return [];
  }
}

/**
 * 指定したタイプの利用可能なクエリファイルを一覧取得する
 * @param queryType クエリタイプ
 * @returns クエリファイル名のリスト
 */
export async function listAvailableQueries(queryType: QueryType): Promise<string[]> {
  let dirPath: string;
  
  switch (queryType) {
    case "dml":
      dirPath = path.resolve(Deno.cwd(), `${BASE_QUERY_DIR}/${DML_DIR_NAME}`);
      break;
    case "dql":
      dirPath = path.resolve(Deno.cwd(), `${BASE_QUERY_DIR}/${DQL_DIR_NAME}`);
      break;
    case "ddl":
      dirPath = path.resolve(Deno.cwd(), `${BASE_QUERY_DIR}/${DDL_DIR_NAME}`);
      break;
    default:
      return [];
  }
  
  const files = await listFilesInDir(dirPath);
  // 拡張子を除去してファイル名のみを返す
  return files.map(file => file.replace(QUERY_FILE_EXTENSION, ""));
}

/**
 * クエリファイルを取得する
 * @param fileName ファイル名（拡張子なし）
 * @param queryType クエリタイプ
 * @returns ファイル内容（成功時）またはエラー情報（失敗時）
 */
export async function getQueryFile(fileName: string, queryType: QueryType): Promise<QueryResult<string>> {
  const validTypes: QueryType[] = ["dml", "dql", "ddl"];
  if (!validTypes.includes(queryType)) {
    return {
      code: "INVALID_QUERY_TYPE",
      message: `無効なクエリタイプです: ${queryType}`,
      queryType,
      validTypes
    };
  }
  
  // 拡張子がなければ追加
  if (!fileName.endsWith(QUERY_FILE_EXTENSION)) {
    fileName += QUERY_FILE_EXTENSION;
  }
  
  // クエリタイプに基づいてパスを決定
  let filePath: string;
  switch (queryType) {
    case "dml":
      filePath = path.resolve(Deno.cwd(), `${BASE_QUERY_DIR}/${DML_DIR_NAME}/${fileName}`);
      break;
    case "dql":
      filePath = path.resolve(Deno.cwd(), `${BASE_QUERY_DIR}/${DQL_DIR_NAME}/${fileName}`);
      break;
    case "ddl":
      filePath = path.resolve(Deno.cwd(), `${BASE_QUERY_DIR}/${DDL_DIR_NAME}/${fileName}`);
      break;
  }
  
  try {
    // ファイルの存在確認
    try {
      await Deno.stat(filePath);
    } catch (error) {
      // 利用可能なファイル一覧を取得
      const availableFiles = await listAvailableQueries(queryType);
      return {
        code: "FILE_NOT_FOUND",
        message: `ファイルが見つかりません: ${filePath}`,
        filePath,
        availableFiles
      };
    }
    
    // ファイル読み込み
    const content = await Deno.readTextFile(filePath);
    return content;
  } catch (error) {
    return {
      code: "QUERY_EXECUTION_ERROR", 
      message: `ファイルの読み込みに失敗しました: ${error.message}`,
      details: error.stack
    };
  }
}

/**
 * DMLファイル内の名前付きクエリをすべて取得する関数
 * @param fileName ファイル名（拡張子を含む）
 * @param queryType クエリタイプ
 * @returns クエリ名の配列
 */
export async function listNamedQueries(fileName: string, queryType: QueryType): Promise<QueryResult<string[]>> {
  const validTypes: QueryType[] = ["dml", "dql", "ddl"];
  if (!validTypes.includes(queryType)) {
    return {
      code: "INVALID_QUERY_TYPE",
      message: `無効なクエリタイプです: ${queryType}`,
      queryType,
      validTypes
    };
  }
  
  // ファイルの取得
  const fileResult = await getQueryFile(fileName, queryType);
  if (isError(fileResult)) {
    return fileResult;
  }
  
  const content = fileResult;
  const lines = content.split("\n");
  const queryNames = [];
  
  const namePattern = /\/\/\s*@name:\s*(\w+)/;
  
  for (const line of lines) {
    const match = line.match(namePattern);
    if (match && match[1]) {
      queryNames.push(match[1]);
    }
  }
  
  return queryNames;
}

/**
 * 名前付きクエリを取得する
 * @param fileName ファイル名（拡張子なし）
 * @param queryName クエリ名
 * @param queryType クエリタイプ
 * @returns クエリ内容（成功時）またはエラー情報（失敗時）
 */
export async function getNamedQuery(
  fileName: string,
  queryName: string,
  queryType: QueryType
): Promise<QueryResult<string>> {
  // ファイルの取得
  const fileResult = await getQueryFile(fileName, queryType);
  if (isError(fileResult)) {
    return fileResult;
  }
  
  const content = fileResult;
  
  // クエリの抽出
  const query = extractNamedQuery(content, queryName);
  
  if (!query) {
    // 利用可能なクエリ名一覧を取得
    const queryNamesResult = await listNamedQueries(fileName, queryType);
    const availableQueries = isError(queryNamesResult) ? [] : queryNamesResult;
    
    return {
      code: "QUERY_NOT_FOUND",
      message: `クエリ名 "${queryName}" は見つかりませんでした: ${fileName}`,
      queryName,
      fileName,
      availableQueries
    };
  }
  
  return query;
}

/**
 * クエリを実行する
 * @param conn データベース接続オブジェクト
 * @param fileName ファイル名（拡張子なし）
 * @param queryName クエリ名
 * @param queryType クエリタイプ
 * @param params クエリパラメータ
 * @returns 実行結果（成功時）またはエラー情報（失敗時）
 */
export async function executeNamedQuery(
  conn: any,
  fileName: string,
  queryName: string,
  queryType: QueryType,
  params: Record<string, any> = {}
): Promise<QueryResult<any>> {
  // クエリの取得
  const queryResult = await getNamedQuery(fileName, queryName, queryType);
  if (isError(queryResult)) {
    return queryResult;
  }
  
  const query = queryResult;
  
  // パラメータを適用
  const processedQuery = applyParamsToQuery(query, params);
  
  // クエリの実行
  try {
    console.log(`クエリを実行: ${processedQuery}`);
    
    // Denoでワーカーの問題を回避するため、実行方法を調整
    let result;
    if (typeof conn.querySync === 'function') {
      // 同期APIを試す（存在する場合）
      console.log("同期APIでクエリを実行します");
      result = conn.querySync(processedQuery);
    } else if (typeof conn.querySingleThreaded === 'function') {
      // シングルスレッドAPIを試す（存在する場合）
      console.log("シングルスレッドAPIでクエリを実行します");
      result = await conn.querySingleThreaded(processedQuery);
    } else {
      // 標準のqueryメソッドを使用
      console.log("標準APIでクエリを実行します");
      result = await conn.query(processedQuery);
    }
    
    console.log(`クエリの実行が完了しました: ${queryName}`);
    return result;
  } catch (error) {
    console.error(`クエリ実行エラー: ${error}`);
    return {
      code: "QUERY_EXECUTION_ERROR",
      message: `クエリの実行に失敗しました: ${error.message}`,
      query: processedQuery,
      details: error.stack
    };
  }
}

/**
 * クエリファイル全体を実行する
 * @param conn データベース接続オブジェクト
 * @param fileName ファイル名（拡張子なし）
 * @param queryType クエリタイプ
 * @param params クエリパラメータ
 * @returns 実行結果（成功時）またはエラー情報（失敗時）
 */
export async function executeQueryFile(
  conn: any,
  fileName: string,
  queryType: QueryType,
  params: Record<string, any> = {}
): Promise<QueryResult<any>> {
  // ファイルの取得
  const fileResult = await getQueryFile(fileName, queryType);
  if (isError(fileResult)) {
    return fileResult;
  }
  
  const content = fileResult;
  
  // パラメータを適用したクエリを作成
  const processedQueries = processQueriesWithParams(content, params);
  
  console.log(`クエリを実行中... (${processedQueries.length}個のクエリ)`);
  
  // クエリの実行
  try {
    const results = [];
    // シングルスレッドで連続的に実行（ワーカーを使わない）
    for (const query of processedQueries) {
      try {
        // Denoでワーカーの問題を回避するため、実行方法を調整
        let result;
        if (typeof conn.querySync === 'function') {
          // 同期APIを試す（存在する場合）
          console.log("同期APIでクエリを実行します");
          result = conn.querySync(query);
        } else if (typeof conn.querySingleThreaded === 'function') {
          // シングルスレッドAPIを試す（存在する場合）
          console.log("シングルスレッドAPIでクエリを実行します");
          result = await conn.querySingleThreaded(query);
        } else {
          // 標準のqueryメソッドを使用
          console.log("標準APIでクエリを実行します");
          result = await conn.query(query);
        }
        results.push(result);
      } catch (error) {
        console.error(`クエリ実行エラー: ${error}`);
        return {
          code: "QUERY_EXECUTION_ERROR",
          message: `クエリの実行に失敗しました: ${error.message}`,
          query,
          details: error.stack
        };
      }
    }
    
    console.log(`クエリファイルの実行が完了しました: ${fileName}`);
    
    // 複数のクエリがある場合は結果の配列、1つの場合は単一の結果を返す
    return results.length === 1 ? results[0] : results;
  } catch (error) {
    return {
      code: "QUERY_EXECUTION_ERROR",
      message: `クエリファイルの実行中にエラーが発生しました: ${error.message}`,
      details: error.stack
    };
  }
}

/**
 * クエリローダーを作成する
 * @param queryDir クエリディレクトリのベースパス（省略可）
 * @returns クエリ操作関数を含むオブジェクト
 */
export function createQueryLoader(queryDir: string = BASE_QUERY_DIR) {
  // クエリファイルのパスを解決する
  function resolvePath(fileName: string, type: QueryType): string {
    let dirName: string;
    switch (type) {
      case "dml":
        dirName = DML_DIR_NAME;
        break;
      case "dql":
        dirName = DQL_DIR_NAME;
        break;
      case "ddl":
        dirName = DDL_DIR_NAME;
        break;
    }
    
    if (!fileName.endsWith(QUERY_FILE_EXTENSION)) {
      fileName += QUERY_FILE_EXTENSION;
    }
    
    return path.resolve(Deno.cwd(), `${queryDir}/${dirName}/${fileName}`);
  }
  
  // 公開インターフェイスを返す
  return {
    getNamedQuery: async (fileName: string, queryName: string, type: QueryType) => 
      getNamedQuery(fileName, queryName, type),
    
    executeNamedQuery: async (
      conn: any,
      fileName: string,
      queryName: string,
      type: QueryType,
      params: Record<string, any> = {}
    ) => executeNamedQuery(conn, fileName, queryName, type, params),
    
    executeQueryFile: async (
      conn: any,
      fileName: string,
      type: QueryType,
      params: Record<string, any> = {}
    ) => executeQueryFile(conn, fileName, type, params),
    
    listAvailableQueries: async (type: QueryType) => listAvailableQueries(type),
    
    listNamedQueries: async (fileName: string, type: QueryType) =>
      listNamedQueries(fileName, type),
    
    isError,
    
    resolvePath
  };
}

// ヘルパー関数 - ファイル内容からクエリを抽出して前処理する
export function processQueriesWithParams(
  content: string,
  params: Record<string, any>
): string[] {
  // コメント行を除去し、セミコロンで分割
  const queries = content
    .split("\n")
    .filter(line => !line.trim().startsWith("//")) // コメント行を除去
    .join("\n")
    .split(";")
    .map(q => q.trim())
    .filter(q => q !== "");
  
  // 各クエリにパラメータを適用
  return queries.map(query => applyParamsToQuery(query, params));
}

// ヘルパー関数 - クエリにパラメータを適用
export function applyParamsToQuery(
  query: string,
  params: Record<string, any>
): string {
  let processedQuery = query;
  
  for (const [key, value] of Object.entries(params)) {
    // 値の型に応じた処理
    let paramValue: string;
    
    if (value === null) {
      paramValue = "NULL";
    } else if (typeof value === 'string') {
      // 文字列はエスケープ処理してシングルクォートで囲む
      paramValue = `'${value.replace(/'/g, "\\'")}'`;
    } else if (typeof value === 'number' || typeof value === 'boolean') {
      // 数値と真偽値はそのまま文字列化
      paramValue = String(value);
    } else if (Array.isArray(value)) {
      // 配列は各要素を処理して角括弧で囲む
      const elements = value.map(item => {
        if (typeof item === 'string') {
          return `'${item.replace(/'/g, "\\'")}'`;
        }
        return String(item);
      });
      paramValue = `[${elements.join(', ')}]`;
    } else if (typeof value === 'object') {
      // オブジェクトはJSON文字列化
      paramValue = JSON.stringify(value);
    } else {
      // その他の型は文字列化
      paramValue = String(value);
    }
    
    // $param_name プレースホルダを置換
    const regex = new RegExp(`\\$${key}\\b`, 'g');
    processedQuery = processedQuery.replace(regex, paramValue);
  }
  
  return processedQuery;
}

// ヘルパー関数 - 名前付きクエリを抽出
export function extractNamedQuery(
  content: string,
  queryName: string
): string | null {
  const marker = `// @name: ${queryName}`;
  const lines = content.split("\n");
  let queryFound = false;
  let query = "";
  
  for (const line of lines) {
    if (line.trim() === marker) {
      queryFound = true;
      continue;
    }
    
    if (queryFound) {
      // 次のマーカーが見つかったら終了
      if (line.trim().startsWith("// @name:")) {
        break;
      }
      
      // コメント行は無視
      if (!line.trim().startsWith("//")) {
        query += line + "\n";
      }
    }
  }
  
  return queryFound ? query.trim() : null;
}
