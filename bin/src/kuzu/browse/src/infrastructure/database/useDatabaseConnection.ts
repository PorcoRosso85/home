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
      logger.debug('database-ready イベントを受信しました');
      
      // グローバルconnectionを確認
      if (!window.conn) {
        logger.error('データベース接続が初期化されていません');
        const errorObj = new Error('データベース接続が初期化されていません');
        setError(errorObj);
        return;
      }
      
      setDbConnection(window.conn);
      setIsConnected(true);
      setError(null);
    };

    // database-readyイベントにリスナーを設定
    const cleanup = onDatabaseReady(handleDatabaseReady);

    return cleanup;
  }, []);

  return { dbConnection, isConnected, error };
}
