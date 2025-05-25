import { useState, useEffect } from 'react';
import { executeDQLQuery } from '../../infrastructure/repository/queryExecutor';
import { VersionState } from '../../domain/types';
import * as logger from '../../../../common/infrastructure/logger';

export const useVersionStates = (dbConnection: any | null) => {
  const [versions, setVersions] = useState<VersionState[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 全バージョンを取得
  useEffect(() => {
    const fetchVersions = async () => {
      if (!dbConnection) {
        logger.debug('dbConnectionがnullのため、バージョン取得をスキップ');
        return;
      }

      setLoading(true);
      logger.debug('バージョン一覧の取得を開始');
      
      try {
        const result = await executeDQLQuery(dbConnection, 'list_versions_all', {});
        logger.debug('クエリ実行結果:', result);
        
        const queryResult = await result.data.getAllObjects();
        logger.debug('getAllObjects結果:', queryResult);
        
        const versionList: VersionState[] = queryResult.map(row => ({
          id: row.version_id,
          timestamp: row.timestamp,
          description: row.description,
          change_reason: row.change_reason
        }));
        
        logger.debug('変換後のバージョンリスト:', versionList);
        setVersions(versionList);
        
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '不明なエラー';
        setError(`バージョン取得でエラーが発生しました: ${errorMessage}`);
        logger.error('バージョン取得エラー:', err);
      }
      
      setLoading(false);
    };

    fetchVersions();
  }, [dbConnection]);

  return {
    versions,
    loading,
    error
  };
};
