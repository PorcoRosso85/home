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
  getQueryFile,
  executeQueryFile,
  listAvailableQueries,
  applyParamsToQuery,
  extractNamedQuery,
  DML_DIR_NAME,
  QUERIES_DIR_NAME,
  BASE_QUERY_DIR,
  QUERY_FILE_EXTENSION
} from "./mod.ts";

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
    
    // Denoでワーカーの問題を回避するため、実行方法を調整
    let queryResult;
    if (typeof conn.querySafe === 'function') {
      // 安全なクエリメソッドを使用（追加した回避策）
      console.log("安全なクエリAPIでクエリを実行します");
      queryResult = await conn.querySafe(processedQuery);
    } else if (typeof conn.querySync === 'function') {
      // 同期APIを試す（存在する場合）
      console.log("同期APIでクエリを実行します");
      queryResult = conn.querySync(processedQuery);
    } else if (typeof conn.querySingleThreaded === 'function') {
      // シングルスレッドAPIを試す（存在する場合）
      console.log("シングルスレッドAPIでクエリを実行します");
      queryResult = await conn.querySingleThreaded(processedQuery);
    } else if (typeof conn.useWorker === 'boolean') {
      // ワーカーオプションを持つ接続
      console.log("ワーカーオプション付きで実行します");
      // 一時的にワーカーを無効化
      const originalWorkerOption = conn.useWorker;
      conn.useWorker = false;
      try {
        queryResult = await conn.query(processedQuery);
      } finally {
        // 元の設定に戻す
        conn.useWorker = originalWorkerOption;
      }
    } else {
      // 標準のqueryメソッドを使用
      console.log("標準APIでクエリを実行します");
      queryResult = await conn.query(processedQuery);
    }
    
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
  try {
    // ファイルの取得
    const fileResult = await getQueryFile(dmlFileName, "dml");
    if (isError(fileResult)) {
      throw new Error(`ファイルの取得に失敗しました: ${fileResult.message}`);
    }
    
    console.log(`DMLファイルを実行します: ${dmlFileName}`);
    
    // パラメータを適用したクエリを作成
    const content = fileResult;
    // コメント行を除去し、セミコロンで分割
    const queries = content
      .split("\n")
      .filter(line => !line.trim().startsWith("//")) // コメント行を除去
      .join("\n")
      .split(";")
      .map(q => q.trim())
      .filter(q => q !== "");
      
    // 各クエリにパラメータを適用
    const processedQueries = queries.map(query => {
      let processedQuery = query;
      for (const [key, value] of Object.entries(params)) {
        // パラメータ置換のロジック...
        const paramValue = typeof value === 'string' 
          ? `'${value.replace(/'/g, "\\'")}'` 
          : String(value);
        const regex = new RegExp(`\\$${key}\\b`, 'g');
        processedQuery = processedQuery.replace(regex, paramValue);
      }
      return processedQuery;
    });
    
    console.log(`クエリを実行中... (${processedQueries.length}個のクエリ)`);
    
    // クエリの実行
    const results = [];
    // シングルスレッドで連続的に実行（ワーカーを使わない）
    for (const query of processedQueries) {
      try {
        // Denoでワーカーの問題を回避するため、実行方法を調整
        let result;
        if (typeof conn.querySafe === 'function') {
          // 安全なクエリメソッドを使用（追加した回避策）
          console.log("安全なクエリAPIでクエリを実行します");
          result = await conn.querySafe(query);
        } else if (typeof conn.querySync === 'function') {
          // 同期APIを試す（存在する場合）
          console.log("同期APIでクエリを実行します");
          result = conn.querySync(query);
        } else if (typeof conn.querySingleThreaded === 'function') {
          // シングルスレッドAPIを試す（存在する場合）
          console.log("シングルスレッドAPIでクエリを実行します");
          result = await conn.querySingleThreaded(query);
        } else if (typeof conn.useWorker === 'boolean') {
          // ワーカーオプションを持つ接続
          console.log("ワーカーオプション付きで実行します");
          // 一時的にワーカーを無効化
          const originalWorkerOption = conn.useWorker;
          conn.useWorker = false;
          try {
            result = await conn.query(query);
          } finally {
            // 元の設定に戻す
            conn.useWorker = originalWorkerOption;
          }
        } else {
          // 標準のqueryメソッドを使用
          console.log("標準APIでクエリを実行します");
          result = await conn.query(query);
        }
        results.push(result);
      } catch (error) {
        console.error(`クエリ実行エラー: ${error}`);
        throw new Error(`クエリの実行に失敗しました: ${error.message}`);
      }
    }
    
    console.log(`クエリファイルの実行が完了しました: ${dmlFileName}`);
    
    // 複数のクエリがある場合は結果の配列、1つの場合は単一の結果を返す
    return results.length === 1 ? results[0] : results;
  } catch (error) {
    console.error(`DMLファイルの実行中にエラーが発生しました: ${error.message}`);
    throw error;
  }
}

/**
 * 特定のパスからすべてのDMLファイルを取得する関数
 * @returns 利用可能なDMLファイル名の配列
 */
export async function listAvailableDmls(): Promise<string[]> {
  const availableQueries = await listAvailableQueries("dml");
  return availableQueries.map(query => `${query}${QUERY_FILE_EXTENSION}`);
}
