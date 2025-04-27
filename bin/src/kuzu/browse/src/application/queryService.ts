/**
 * データベースクエリサービス
 * 
 * データベースへのクエリ処理を一元管理するサービス
 */

import { DatabaseError } from '../infrastructure/database/databaseService';
// dbモジュールのヘルパー関数は直接importできないため、実行時に動的にロード
// 注: 相対パスでのimportがエラーを起こすため、この方法を使用します

/**
 * クエリ結果型
 */
export interface QueryResult {
  rows?: any[];
  [key: string]: any;
}

/**
 * クエリサービスの結果型
 */
export type QueryServiceResult = QueryResult | DatabaseError;

/**
 * クエリタイプ - ユースケースを表す
 */
export enum QueryType {
  GET_TABLE_LIST = 'GET_TABLE_LIST',
  GET_TABLE_DATA = 'GET_TABLE_DATA',
}

/**
 * クエリパラメータ型
 */
export interface QueryParams {
  tableName?: string;
  limit?: number;
  [key: string]: any;
}

/**
 * データベースクエリを実行する
 * 
 * @param connection データベース接続
 * @param queryType クエリタイプ（ユースケース）
 * @param params クエリパラメータ
 * @returns クエリ結果または実行エラー
 */
export const executeQuery = async (
  connection: any,
  queryType: QueryType,
  params: QueryParams = {}
): Promise<{ result: QueryServiceResult; query: string }> => {
  // クエリの組み立て
  let query = '';
  
  switch (queryType) {
    case QueryType.GET_TABLE_LIST:
      // ラベル一覧を取得する代替クエリ（Cypherの以前のバージョン用）
      query = 'MATCH (n) RETURN DISTINCT labels(n) AS tableName;';
      break;
      
    case QueryType.GET_TABLE_DATA:
      if (!params.tableName) {
        return {
          result: {
            code: 'INVALID_PARAMS',
            message: 'テーブル名が指定されていません'
          },
          query
        };
      }
      const limit = params.limit || 100;
      // 修正: プロパティアクセスはラベルごとに異なる場合があるため
      query = `MATCH (n:${params.tableName}) RETURN n LIMIT ${limit};`;
      break;
      
    default:
      return {
        result: {
          code: 'UNKNOWN_QUERY_TYPE',
          message: `不明なクエリタイプです: ${queryType}`
        },
        query
      };
  }
  
  try {
    // 直接Cypherクエリを実行する方式に戻します
    
    // 直接Cypherクエリを実行
    console.log(`クエリ実行: ${query}`);
    const queryResult = await connection.query(query);
    
    // 結果の取得と変換
    let resultJson;
    if (queryResult.table) {
      // tableプロパティを持つ場合
      const resultTable = queryResult.table.toString();
      resultJson = JSON.parse(resultTable);
    } else if (queryResult.getAllObjects) {
      // getAllObjects()メソッドを持つ場合
      resultJson = await queryResult.getAllObjects();
    } else {
      // その他の場合はオブジェクトとして扱う
      resultJson = queryResult;
    }
    
    return { result: resultJson, query };
  } catch (error) {
    console.error('クエリ実行エラー:', error);
    return {
      result: {
        code: 'QUERY_EXECUTION_ERROR',
        message: `クエリ実行エラー: ${error.message}`,
        stack: error.stack
      },
      query
    };
  }
};
