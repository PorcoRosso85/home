/**
 * Duck API クライアント
 * 高階関数による依存性注入（規約準拠）
 */
import * as logger from '../../../common/infrastructure/logger';

// Duck API設定型
type DuckApiConfig = {
  host: string;
  port: string;
};

// DuckLakeバージョン情報型
type DuckLakeVersion = {
  version: number;
  timestamp: string;
  description: string;
  row_count: number;
  changes: {
    total: number;
    inserts: number;
    deletes: number;
    updates: number;
  };
};

// API レスポンス型
type VersionsResponse = {
  versions: DuckLakeVersion[];
};

// エラー型（規約準拠: 共用体型）
type ApiError = {
  code: string;
  message: string;
};

type FetchVersionsResult = VersionsResponse | ApiError;

// エラー判定関数
function isApiError(result: FetchVersionsResult): result is ApiError {
  return 'code' in result && 'message' in result;
}

/**
 * Duck APIクライアントを作成する高階関数
 */
export function createDuckApiClient(config: DuckApiConfig) {
  const baseUrl = `http://${config.host}:${config.port}`;
  
  return {
    /**
     * DuckLakeバージョン一覧を取得
     */
    fetchVersions: async (): Promise<FetchVersionsResult> => {
      const url = `${baseUrl}/api/versions`;
      logger.info(`[DuckAPI] Fetching versions from: ${url}`);
      
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          logger.error(`[DuckAPI] HTTP error: ${response.status}`, errorText);
          
          // エラーレスポンスがJSONの場合はパース
          try {
            const errorJson = JSON.parse(errorText);
            return {
              code: errorJson.code || 'HTTP_ERROR',
              message: errorJson.message || `HTTP ${response.status}: ${response.statusText}`
            };
          } catch {
            return {
              code: 'HTTP_ERROR',
              message: `HTTP ${response.status}: ${response.statusText}`
            };
          }
        }
        
        const data = await response.json() as VersionsResponse;
        logger.info(`[DuckAPI] Fetched ${data.versions.length} versions`);
        
        // デバッグ: レスポンスの詳細を確認
        logger.info('[DuckAPI] Response data:', JSON.stringify(data, null, 2));
        
        return data;
      } catch (error) {
        logger.error('[DuckAPI] Network error:', error);
        return {
          code: 'NETWORK_ERROR',
          message: `[DuckAPI Network Error] ${error instanceof Error ? error.message : String(error)}`
        };
      }
    }
  };
}
