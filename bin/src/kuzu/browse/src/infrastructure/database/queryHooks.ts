/**
 * クエリ実行と結果取得のためのフック関数群
 * 
 * TODO: クラスベースではなく関数ベースで実装
 */

import { useState, useCallback } from 'react';
import { executeDQLQuery } from '../repository/queryExecutor';
import * as logger from '../../../../common/infrastructure/logger';

/**
 * 単一クエリを実行するためのフック
 */
export function useQuery<T = any>() {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const executeQuery = useCallback(async (
    connection: any,
    queryName: string,
    params: Record<string, any> = {}
  ): Promise<{ success: boolean; data: T | null; error: string | null }> => {
    if (!connection) {
      const errorMsg = 'データベース接続がありません';
      setError(errorMsg);
      return { success: false, data: null, error: errorMsg };
    }
    
    try {
      setLoading(true);
      setError(null);
      
      logger.debug(`クエリ実行中: ${queryName}`, params);
      
      const result = await executeDQLQuery(connection, queryName, params);
      
      if (!result.success || !result.data) {
        const errorMsg = result.error || 'クエリ実行に失敗しました';
        setError(errorMsg);
        return { success: false, data: null, error: errorMsg };
      }
      
      const queryResult = await result.data.getAllObjects();
      const typedResult = queryResult as unknown as T;
      
      setData(typedResult);
      
      return { success: true, data: typedResult, error: null };
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '不明なエラーが発生しました';
      logger.error(`クエリ実行エラー: ${errorMsg}`);
      setError(errorMsg);
      return { success: false, data: null, error: errorMsg };
    } finally {
      setLoading(false);
    }
  }, []);
  
  return { data, loading, error, executeQuery };
}

/**
 * 複数クエリを連続して実行するためのフック
 */
export function useMultiQuery<T = any>() {
  const [results, setResults] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  
  const executeQueries = useCallback(async (
    connection: any,
    queries: Array<{ name: string; params: Record<string, any> }>
  ): Promise<{ success: boolean; data: T[]; errors: string[] }> => {
    if (!connection) {
      const errorMsg = 'データベース接続がありません';
      setErrors([errorMsg]);
      return { success: false, data: [], errors: [errorMsg] };
    }
    
    try {
      setLoading(true);
      setErrors([]);
      
      const queryResults: T[] = [];
      const queryErrors: string[] = [];
      
      for (const query of queries) {
        try {
          logger.debug(`クエリ実行中: ${query.name}`, query.params);
          
          const result = await executeDQLQuery(connection, query.name, query.params);
          
          if (!result.success || !result.data) {
            const errorMsg = result.error || `${query.name}の実行に失敗しました`;
            queryErrors.push(errorMsg);
            continue;
          }
          
          const resultObjects = await result.data.getAllObjects();
          queryResults.push(resultObjects as unknown as T);
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : '不明なエラーが発生しました';
          logger.error(`クエリ実行エラー: ${errorMsg}`);
          queryErrors.push(errorMsg);
        }
      }
      
      setResults(queryResults);
      setErrors(queryErrors);
      
      return { 
        success: queryErrors.length === 0, 
        data: queryResults, 
        errors: queryErrors 
      };
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '不明なエラーが発生しました';
      logger.error(`複数クエリ実行エラー: ${errorMsg}`);
      setErrors([errorMsg]);
      return { success: false, data: [], errors: [errorMsg] };
    } finally {
      setLoading(false);
    }
  }, []);
  
  return { results, loading, errors, executeQueries };
}
