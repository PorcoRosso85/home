import { onDatabaseReady } from '../../infrastructure/database/databaseEvent';
import type { 
  DatabaseConnectionInput,
  DatabaseConnectionOutput,
  DatabaseConnectionError
} from '../../domain/types';
import * as logger from '../../../common/infrastructure/logger';

export const setupDatabaseConnectionCore = (
  input: DatabaseConnectionInput,
  onConnectionReady: (connection: any) => void,
  onConnectionError: (error: DatabaseConnectionError) => void
): (() => void) => {
  
  const handleDatabaseReady = async () => {
    logger.debug('database-ready イベントを受信しました');
    
    try {
      if (!window.conn) {
        logger.error('データベース接続が初期化されていません');
        
        const error: DatabaseConnectionError = {
          type: 'INITIALIZATION_ERROR',
          message: 'データベース接続が初期化されていません',
          originalError: null
        };
        
        onConnectionError(error);
        return;
      }
      
      onConnectionReady(window.conn);
      
    } catch (error) {
      logger.error('データベース接続処理でエラー:', error);
      
      const errorMessage = error instanceof Error ? error.message : '不明なエラー';
      let errorType: DatabaseConnectionError['type'] = 'UNKNOWN_ERROR';
      
      if (errorMessage.includes('connection')) {
        errorType = 'CONNECTION_ERROR';
      } else if (errorMessage.includes('initialization')) {
        errorType = 'INITIALIZATION_ERROR';
      } else if (errorMessage.includes('event')) {
        errorType = 'EVENT_ERROR';
      }
      
      const connectionError: DatabaseConnectionError = {
        type: errorType,
        message: `データベース接続でエラーが発生しました: ${errorMessage}`,
        originalError: error
      };
      
      onConnectionError(connectionError);
    }
  };

  return onDatabaseReady(handleDatabaseReady);
};
