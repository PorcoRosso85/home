/**
 * CONVENTION.yaml準拠 高階関数による依存性注入サービス
 * 規約: 関数のみで実装、高階関数による依存性注入
 */

import type { VersionState } from '../../domain/coreTypes';
import type { 
  VersionStatesInput,
  VersionStatesResult
} from '../types/versionTypes';
import type { VersionDependencies } from '../types/dependencies';
import { createError, createVersionStatesSuccess } from '../../common/errorHandler';
import { isErrorResult } from '../../common/typeGuards';

/**
 * バージョンサービス生成関数（高階関数）
 * 規約準拠: 依存性注入による純粋関数化
 */
export function createVersionService(deps: VersionDependencies) {
  /**
   * バージョン取得Core関数（Pure Logic）
   * 依存性が注入された純粋関数
   */
  return async function fetchVersionsCore(input: VersionStatesInput): Promise<VersionStatesResult> {
    // 入力検証
    if (!input.dbConnection) {
      deps.logger.debug('dbConnectionがnullのため、バージョン取得をスキップ');
      return createError('DATABASE_ERROR', 'データベース接続が確立されていません');
    }

    deps.logger.debug('バージョン一覧の取得を開始');

    // 依存性注入されたクエリ実行器を使用
    const result = await deps.queryExecutor.execute(input.dbConnection, 'list_versions_all', {});
    deps.logger.debug('クエリ実行結果:', result);
    
    // エラーの明示的分岐
    if (isErrorResult(result)) {
      return result;
    }
    
    const queryResult = await result.data.getAllObjects();
    deps.logger.debug('getAllObjects結果:', queryResult);
    
    // データ変換ロジック
    const versionList: VersionState[] = queryResult.map(row => ({
      id: row.version_id,
      timestamp: row.timestamp,
      description: row.description,
      change_reason: row.change_reason
    }));
    
    deps.logger.debug('変換後のバージョンリスト:', versionList);
    
    return createVersionStatesSuccess(versionList);
  };
}
