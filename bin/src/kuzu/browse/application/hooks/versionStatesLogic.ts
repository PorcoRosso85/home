import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';
import type { 
  VersionState, 
  VersionStatesInput, 
  VersionStatesOutput,
  VersionStatesError 
} from '../../domain/types';
import * as logger from '../../../common/infrastructure/logger';

/**
 * バージョン状態取得のCore関数（Pure Logic）
 * React依存なし、テスト可能な純粋関数
 */
export const fetchVersionsCore = async (input: VersionStatesInput): Promise<VersionStatesOutput> => {
  // Core層：入力検証
  if (!input.dbConnection) {
    logger.debug('dbConnectionがnullのため、バージョン取得をスキップ');
    return {
      success: false,
      error: {
        type: 'DATABASE_ERROR',
        message: 'データベース接続が確立されていません',
        originalError: null
      }
    };
  }

  logger.debug('バージョン一覧の取得を開始');

  try {
    // Core層：ビジネスロジック実行
    const result = await executeDQLQuery(input.dbConnection, 'list_versions_all', {});
    logger.debug('クエリ実行結果:', result);
    
    const queryResult = await result.data.getAllObjects();
    logger.debug('getAllObjects結果:', queryResult);
    
    // Core層：データ変換ロジック
    const versionList: VersionState[] = queryResult.map(row => ({
      id: row.version_id,
      timestamp: row.timestamp,
      description: row.description,
      change_reason: row.change_reason
    }));
    
    logger.debug('変換後のバージョンリスト:', versionList);
    
    return {
      success: true,
      data: versionList
    };
    
  } catch (error) {
    // Core層：エラー分類・構造化
    logger.error('バージョン取得エラー:', error);
    
    const errorMessage = error instanceof Error ? error.message : '不明なエラー';
    let errorType: VersionStatesError['type'] = 'UNKNOWN_ERROR';
    
    if (errorMessage.includes('query') || errorMessage.includes('Query')) {
      errorType = 'QUERY_ERROR';
    } else if (errorMessage.includes('database') || errorMessage.includes('connection')) {
      errorType = 'DATABASE_ERROR';
    } else if (errorMessage.includes('transform') || errorMessage.includes('map')) {
      errorType = 'TRANSFORM_ERROR';
    }
    
    return {
      success: false,
      error: {
        type: errorType,
        message: `バージョン取得でエラーが発生しました: ${errorMessage}`,
        originalError: error
      }
    };
  }
};
