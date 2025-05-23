/**
 * データベース接続管理のカスタムフック
 */
import { useState, useEffect } from 'react';
import { onDatabaseReady } from './databaseEvent';
import * as logger from '../../../../common/infrastructure/logger';

type DatabaseConnectionState = {
  dbConnection: any | null;
  isConnected: boolean;
  error: Error | null;
}

export function useDatabaseConnection(): DatabaseConnectionState {
  const [dbConnection, setDbConnection] = useState<any | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const handleDatabaseReady = async () => {
      try {
        logger.debug('database-ready イベントを受信しました');
        
        // グローバルconnectionを確認
        if (!window.conn) {
          throw new Error('データベース接続が初期化されていません');
        }
        
        setDbConnection(window.conn);
        setIsConnected(true);
        setError(null);
      } catch (err) {
        logger.error('データベース接続エラー:', err);
        const errorObj = err instanceof Error ? err : new Error('Unknown error');
        setError(errorObj);
      }
    };

    // database-readyイベントにリスナーを設定
    const cleanup = onDatabaseReady(handleDatabaseReady);

    return cleanup;
  }, []);

  return { dbConnection, isConnected, error };
}
