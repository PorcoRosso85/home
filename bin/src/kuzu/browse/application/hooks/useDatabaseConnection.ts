import { useState, useEffect } from 'react';
import { setupDatabaseConnectionCore } from './databaseConnectionLogic';
import type { DatabaseConnectionState } from '../../domain/types';

/**
 * データベース接続管理のReact Hook（薄いWrapper）
 * Core関数を使用し、React状態管理のみに責務を限定
 */
export const useDatabaseConnection = (): DatabaseConnectionState => {
  const [state, setState] = useState<DatabaseConnectionState>({
    dbConnection: null,
    isConnected: false,
    error: null
  });

  useEffect(() => {
    // Core関数呼び出し（コールバック方式）
    const cleanup = setupDatabaseConnectionCore(
      {}, // 現在は入力パラメータなし
      // 成功時のコールバック
      (connection: any) => {
        setState(prev => ({
          ...prev,
          dbConnection: connection,
          isConnected: true,
          error: null
        }));
      },
      // エラー時のコールバック
      (error) => {
        setState(prev => ({
          ...prev,
          dbConnection: null,
          isConnected: false,
          error: error.message // UI表示用メッセージのみ
        }));
      }
    );

    // cleanup関数を返す
    return cleanup;
  }, []);

  return state;
};
