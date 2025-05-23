import * as logger from '../../../../common/infrastructure/logger';
import { executeQuery } from '../../infrastructure/repository/queryExecutor';
import { LocationURI, VersionState } from '../../domain/types';

/**
 * 特定バージョンのLocationURI一覧を取得する
 */
export async function getVersionedLocationUris(
  conn: any, 
  versionId: string
): Promise<{ version: VersionState; locations: LocationURI[] } | null> {
  try {
    logger.debug(`バージョン ${versionId} のLocationURI取得中...`);
    
    // 特定バージョンのLocationURIを取得するDQL実行
    const result = await executeQuery(conn, 'locationuris_by_version', { 
      version_id: versionId 
    });
    
    if (!result.success || !result.data) {
      logger.error(`バージョン ${versionId} のデータ取得失敗:`, result.error);
      return null;
    }
    
    const queryResult = await result.data.getAllObjects();
    
    if (queryResult.length === 0) {
      logger.debug(`バージョン ${versionId} のデータが見つかりません`);
      return null;
    }
    
    // 結果を整形
    const versionInfo: VersionState = {
      id: queryResult[0].version_id,
      timestamp: queryResult[0].version_timestamp,
      description: queryResult[0].version_description
    };
    
    const locations: LocationURI[] = queryResult.map(row => ({
      uri_id: row.uri_id,
      scheme: row.scheme,
      authority: row.authority || '',
      path: row.path,
      fragment: row.fragment || '',
      query: row.query || ''
    }));
    
    logger.debug(`バージョン ${versionId} のLocationURI数: ${locations.length}`);
    
    return {
      version: versionInfo,
      locations: locations
    };
  } catch (error) {
    logger.error(`getVersionedLocationUris エラー:`, error);
    // throw文を削除し、nullを返す
    return null;
  }
}

/**
 * 全バージョンの一覧を取得する（FOLLOWS関係を考慮した順序）
 */
export async function getVersionHistory(conn: any): Promise<VersionState[]> {
  try {
    logger.debug('バージョン履歴取得中...');
    
    const result = await executeQuery(conn, 'version_state_history', {});
    
    if (!result.success || !result.data) {
      logger.error('バージョン履歴取得失敗:', result.error);
      return [];
    }
    
    const queryResult = await result.data.getAllObjects();
    
    const versions: VersionState[] = queryResult.map(row => ({
      id: row.version_id,
      timestamp: row.timestamp,
      description: row.description
    }));
    
    logger.debug(`取得したバージョン数: ${versions.length}`);
    
    return versions;
  } catch (error) {
    logger.error('getVersionHistory エラー:', error);
    // throw文を削除し、空配列を返す
    return [];
  }
}

/**
 * 2つのバージョン間でのLocationURI差分を取得する
 */
export async function getVersionDiff(
  conn: any,
  fromVersionId: string,
  toVersionId: string
): Promise<{
  added: LocationURI[];
  removed: LocationURI[];
  modified: LocationURI[];
}> {
  try {
    logger.debug(`バージョン差分分析: ${fromVersionId} → ${toVersionId}`);
    
    const result = await executeQuery(conn, 'version_diff_analysis', {
      from_version_id: fromVersionId,
      to_version_id: toVersionId
    });
    
    if (!result.success || !result.data) {
      logger.error('バージョン差分分析失敗:', result.error);
      return { added: [], removed: [], modified: [] };
    }
    
    const queryResult = await result.data.getAllObjects();
    
    // 結果を分類
    const added: LocationURI[] = [];
    const removed: LocationURI[] = [];
    const modified: LocationURI[] = [];
    
    for (const row of queryResult) {
      const location: LocationURI = {
        uri_id: row.uri_id,
        scheme: row.scheme,
        authority: row.authority || '',
        path: row.path,
        fragment: row.fragment || '',
        query: row.query || ''
      };
      
      switch (row.change_type) {
        case 'added':
          added.push(location);
          break;
        case 'removed':
          removed.push(location);
          break;
        case 'modified':
          modified.push(location);
          break;
      }
    }
    
    logger.debug(`差分結果: 追加=${added.length}, 削除=${removed.length}, 修正=${modified.length}`);
    
    return { added, removed, modified };
  } catch (error) {
    logger.error('getVersionDiff エラー:', error);
    // throw文を削除し、空の差分結果を返す
    return { added: [], removed: [], modified: [] };
  }
}
