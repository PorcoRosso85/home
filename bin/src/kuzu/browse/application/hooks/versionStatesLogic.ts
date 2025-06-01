import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';
import type { VersionState } from '../../domain/coreTypes';
import type { 
  VersionStatesInput,
  VersionStatesResult
} from '../types/versionTypes';
import { createError, createVersionStatesSuccess } from '../../common/errorHandler';
import { isErrorResult } from '../../common/typeGuards';
import * as logger from '../../../common/infrastructure/logger';

/**
 * バージョン状態取得のCore関数（Pure Logic）
 * CONVENTION.yaml準拠: Result型使用禁止、個別Tagged Union使用
 * React依存なし、テスト可能な純粋関数
 */
export const fetchVersionsCore = async (input: VersionStatesInput): Promise<VersionStatesResult> => {
  // Core層：入力検証
  if (!input.dbConnection) {
    logger.debug('dbConnectionがnullのため、バージョン取得をスキップ');
    return createError('DATABASE_ERROR', 'データベース接続が確立されていません');
  }

  logger.debug('バージョン一覧の取得を開始');

  // Core層：ビジネスロジック実行（try/catch除去済み）
  const result = await executeDQLQuery(input.dbConnection, 'list_versions_all', {});
  logger.debug('クエリ実行結果:', result);
  
  // クエリ実行でエラーが発生した場合の明示的分岐
  if (isErrorResult(result)) {
    return result; // エラー結果をそのまま返す
  }
  
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
  
  return createVersionStatesSuccess(versionList);
};
