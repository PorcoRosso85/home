/**
 * Query Repository Interface
 * 
 * クエリ実行に関するリポジトリの抽象化
 */

import type { QueryResult } from '../entities/queryResult';

/**
 * クエリリポジトリのインターフェース
 */
export type QueryRepository = {
  /**
   * クエリファイルを検索する
   */
  findQueryFile: (queryName: string) => Promise<[boolean, string]> | [boolean, string];
  
  /**
   * クエリファイルの内容を読み込む
   */
  readQueryFile: (filePath: string) => Promise<QueryResult<string>> | QueryResult<string>;
  
  /**
   * 利用可能なすべてのクエリ名のリストを取得する
   */
  getAvailableQueries: () => Promise<string[]> | string[];
  
  /**
   * クエリ名に対応するCypherクエリを取得する
   */
  getQuery: (queryName: string, fallbackQuery?: string) => Promise<QueryResult<string>> | QueryResult<string>;
  
  /**
   * クエリを実行する
   */
  executeQuery: (connection: any, queryName: string, params?: Record<string, any>) => Promise<QueryResult<any>>;
  
  /**
   * 成功判定ヘルパー関数
   */
  getSuccess: <T>(result: QueryResult<T>) => boolean;
};

/**
 * クエリビルダーの関数型
 */
export type QueryBuilder = (template: string, params: Record<string, any>) => string;

/**
 * クエリパラメータのビルダーインターフェース
 */
export type QueryParameterBuilder = {
  /**
   * パラメータを含むクエリを構築する
   */
  buildParameterizedQuery: (query: string, params: Record<string, any>) => string;
  
  /**
   * パラメータの型チェックを行う
   */
  validateParameters: (params: Record<string, any>) => { isValid: boolean; error?: string };
};

/**
 * クエリ実行オプション
 */
export type QueryExecutionOptions = {
  /**
   * タイムアウト時間（ミリ秒）
   */
  timeout?: number;
  
  /**
   * リトライ回数
   */
  retries?: number;
  
  /**
   * リトライ間隔（ミリ秒）
   */
  retryDelay?: number;
  
  /**
   * クエリ実行前のバリデーション
   */
  validateBeforeExecution?: boolean;
};

/**
 * 拡張クエリリポジトリのインターフェース
 */
export type ExtendedQueryRepository = QueryRepository & {
  /**
   * クエリ実行オプション付きで実行する
   */
  executeQueryWithOptions: (
    connection: any,
    queryName: string,
    params: Record<string, any>,
    options: QueryExecutionOptions
  ) => Promise<QueryResult<any>>;
  
  /**
   * バッチでクエリを実行する
   */
  executeBatchQueries: (
    connection: any,
    queries: Array<{ queryName: string; params: Record<string, any> }>
  ) => Promise<QueryResult<any[]>>;
  
  /**
   * キャッシュを利用したクエリ実行
   */
  executeQueryWithCache: (
    connection: any,
    queryName: string,
    params: Record<string, any>,
    cacheTTL?: number
  ) => Promise<QueryResult<any>>;
};
