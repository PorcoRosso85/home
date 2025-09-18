import { onDatabaseReady } from '../../infrastructure/database/databaseEvent';
import type { 
  DatabaseConnectionInput,
  DatabaseConnectionOutput,
  DatabaseConnectionError
} from '../../domain/types';
import { createError } from '../../common/errorHandler';
import * as logger from '../../../common/infrastructure/logger';

export const setupDatabaseConnectionCore = (
  input: DatabaseConnectionInput,
  onConnectionReady: (connection: any) => void,
  onConnectionError: (error: DatabaseConnectionError) => void
): (() => void) => {
  
  const handleDatabaseReady = async () => {
    logger.debug('database-ready イベントを受信しました');
    
    // Core層：データベース接続の検証（try/catch除去）
    if (!window.conn) {
      logger.error('データベース接続が初期化されていません');
      const error = createError('INITIALIZATION_ERROR', 'データベース接続が初期化されていません');
      onConnectionError(error);
      return;
    }
    
    // Core層：接続成功時のコールバック
    onConnectionReady(window.conn);
  };

  return onDatabaseReady(handleDatabaseReady);
};
