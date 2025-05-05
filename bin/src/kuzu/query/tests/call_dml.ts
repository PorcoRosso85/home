/**
 * 階層型トレーサビリティモデル - DML呼び出しユーティリティ
 * 
 * このファイルはDMLファイル（.cypher）を名前で呼び出し、必要なパラメータを渡すための
 * ユーティリティ関数を提供します。
 */

import * as path from "https://deno.land/std@0.177.0/path/mod.ts";
import {
  QueryType,
  QueryResult,
  isError,
  getNamedQuery,
  executeQueryFile,
  listAvailableQueries,
  applyParamsToQuery,
  extractNamedQuery,
  DML_DIR_NAME,
  QUERIES_DIR_NAME,
  BASE_QUERY_DIR,
  QUERY_FILE_EXTENSION
} from "../mod.ts";

/**
 * 名前付きDMLクエリを実行する関数
 * @param conn データベース接続オブジェクト
 * @param dmlFileName 実行するDMLファイル名（.cypherを含む）
 * @param queryName 実行するクエリ名
 * @param params クエリに渡すパラメータ
 * @returns クエリ実行結果
 */
export async function callNamedDml(
  conn: any,
  dmlFileName: string,
  queryName: string,
  params: Record<string, any> = {}
): Promise<any> {
  try {
    console.log(`名前付きDMLクエリ実行: ${dmlFileName} -> ${queryName}`);
    
    // 優先順位順にクエリタイプを試行
    const queryTypes: QueryType[] = ["dml", "dql"];
    let result: QueryResult<any> | null = null;
    
    for (const type of queryTypes) {
      result = await getNamedQuery(dmlFileName, queryName, type);
      if (!isError(result)) {
        break;
      }
    }
    
    // いずれのタイプでもクエリが見つからなかった場合
    if (!result || isError(result)) {
      // queries（旧）ディレクトリを最後に試す（互換性のため）
      const queriesPath = path.resolve(
        Deno.cwd(),
        `${BASE_QUERY_DIR}/${QUERIES_DIR_NAME}/${dmlFileName}`
      );
      
      try {
        await Deno.stat(queriesPath);
        const content = await Deno.readTextFile(queriesPath);
        const query = extractNamedQuery(content, queryName);
        
        if (!query) {
          throw new Error(`クエリ名 "${queryName}" は見つかりませんでした: ${dmlFileName}`);
        }
        
        result = query;
      } catch (error) {
        throw new Error(`DMLファイルが見つかりません: ${dmlFileName}`);
      }
    }
    
    if (isError(result)) {
      throw new Error(`クエリの取得に失敗しました: ${result.message}`);
    }
    
    // パラメータを適用
    const processedQuery = applyParamsToQuery(result, params);
    
    // クエリを実行
    console.log(`クエリを実行: ${processedQuery}`);
    const queryResult = await conn.query(processedQuery);
    
    console.log(`クエリの実行が完了しました: ${queryName}`);
    return queryResult;
    
  } catch (error) {
    console.error(`名前付きDMLクエリの実行中にエラーが発生しました: ${error.message}`);
    throw error;
  }
}

/**
 * DMLファイルを実行する関数
 * @param conn データベース接続オブジェクト
 * @param dmlFileName 実行するDMLファイル名（.cypherを含む）
 * @param params クエリに渡すパラメータ
 * @returns クエリ実行結果
 */
export async function callDml(
  conn: any,
  dmlFileName: string,
  params: Record<string, any> = {}
): Promise<any> {
  const result = await executeQueryFile(conn, dmlFileName, "dml", params);
  
  if (isError(result)) {
    console.error(`DMLファイルの実行中にエラーが発生しました: ${result.message}`);
    throw new Error(result.message);
  }
  
  return result;
}

/**
 * 特定のパスからすべてのDMLファイルを取得する関数
 * @returns 利用可能なDMLファイル名の配列
 */
export async function listAvailableDmls(): Promise<string[]> {
  const availableQueries = await listAvailableQueries("dml");
  return availableQueries.map(query => `${query}${QUERY_FILE_EXTENSION}`);
}
