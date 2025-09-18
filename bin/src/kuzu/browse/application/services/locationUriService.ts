/**
 * LocationURI機能用高階関数サービス
 * CONVENTION.yaml準拠: 関数カリー化による依存性注入
 */

import type { NodeData } from '../../domain/coreTypes';
import type { 
  LocationUrisInput,
  LocationUrisResult
} from '../types/locationUriTypes';
import type { LocationUriDependencies } from '../types/dependencies';
import { createError, createLocationUrisSuccess } from '../../common/errorHandler';
import { isErrorResult } from '../../common/typeGuards';

/**
 * LocationURIサービス生成関数（高階関数）
 * 規約準拠: 依存性注入による純粋関数化
 */
export function createLocationUriService(deps: LocationUriDependencies) {
  /**
   * LocationURI取得とツリー構築の高階関数
   */
  return function processLocationUriWithOptions(options: any) {
    return async function fetchLocationUrisCore(input: LocationUrisInput): Promise<LocationUrisResult> {
      if (!input.dbConnection) {
        return createError('DATABASE_ERROR', 'データベース接続が確立されていません');
      }

      if (!input.selectedVersionId) {
        return createLocationUrisSuccess([]);
      }

      // 依存性注入されたクエリ実行器を使用
      const result = await deps.queryExecutor.execute(
        input.dbConnection, 
        'list_uris_cumulative', 
        { version_id: input.selectedVersionId }
      );
      
      if (isErrorResult(result)) {
        return result;
      }
      
      const queryResult = await result.data.getAllObjects();
      const locationUris = transformLocationUrisData(queryResult);
      
      // オプションに基づくフィルタリング
      const filteredUris = applyLocationUriFilters(locationUris, options);
      
      return createLocationUrisSuccess(filteredUris);
    };
  };
}

/**
 * データ変換用純粋関数
 */
function transformLocationUrisData(queryResult: any[]): any[] {
  return queryResult.map(row => ({
    uri_id: row.uri_id || row.id,
    scheme: row.scheme || '',
    authority: row.authority || '',
    path: row.path || '',
    fragment: row.fragment || '',
    query: row.query || '',
    from_version: row.from_version,
    version_description: row.version_description
  }));
}

/**
 * フィルタリング用純粋関数
 */
function applyLocationUriFilters(locationUris: any[], options: any): any[] {
  if (!options) return locationUris;
  
  let filtered = locationUris;
  
  if (options.schemeFilter) {
    filtered = filtered.filter(uri => 
      options.schemeFilter.includes(uri.scheme)
    );
  }
  
  if (options.pathPattern) {
    filtered = filtered.filter(uri => 
      uri.path.includes(options.pathPattern)
    );
  }
  
  return filtered;
}
