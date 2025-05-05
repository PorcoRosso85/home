/**
 * 階層型トレーサビリティモデル - DDL呼び出しユーティリティ
 * 
 * このファイルはDDLファイル（.cypher）を名前で呼び出し、必要なパラメータを渡すための
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
  DDL_DIR_NAME,
  QUERY_FILE_EXTENSION,
  BASE_QUERY_DIR
} from "../mod.ts";

/**
 * 名前付きDDLクエリを実行する関数
 * @param conn データベース接続オブジェクト
 * @param ddlFileName 実行するDDLファイル名（.cypherを含む）
 * @param queryName 実行するクエリ名
 * @param params クエリに渡すパラメータ
 * @returns クエリ実行結果
 */
export async function callNamedDdl(
  conn: any,
  ddlFileName: string,
  queryName: string,
  params: Record<string, any> = {}
): Promise<any> {
  try {
    console.log(`名前付きDDLクエリ実行: ${ddlFileName} -> ${queryName}`);
    
    // DDLクエリを取得
    const result = await getNamedQuery(ddlFileName, queryName, "ddl");
    
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
    console.error(`名前付きDDLクエリの実行中にエラーが発生しました: ${error.message}`);
    throw error;
  }
}

/**
 * DDLファイルを実行する関数
 * @param conn データベース接続オブジェクト
 * @param ddlFileName 実行するDDLファイル名（.cypherを含む）
 * @param params クエリに渡すパラメータ
 * @returns クエリ実行結果
 */
export async function callDdl(
  conn: any,
  ddlFileName: string,
  params: Record<string, any> = {}
): Promise<any> {
  const result = await executeQueryFile(conn, ddlFileName, "ddl", params);
  
  if (isError(result)) {
    console.error(`DDLファイルの実行中にエラーが発生しました: ${result.message}`);
    throw new Error(result.message);
  }
  
  return result;
}

/**
 * 特定のパスからすべてのDDLファイルを取得する関数
 * @returns 利用可能なDDLファイル名の配列
 */
export async function listAvailableDdls(): Promise<string[]> {
  const availableQueries = await listAvailableQueries("ddl");
  return availableQueries.map(query => `${query}${QUERY_FILE_EXTENSION}`);
}
