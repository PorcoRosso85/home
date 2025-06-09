/**
 * DuckLakeからLocationURIデータをParquet形式で取得してKuzuにロードするユースケース
 * 公式ドキュメント準拠の最小構成実装
 */
import * as logger from '../../../common/infrastructure/logger';
import { env } from '../../infrastructure/config/variables';

// エラー型定義（規約準拠）
type LoadError = {
  code: string;
  message: string;
};

type LoadSuccess = {
  loadedCount: number;
  version: number;
};

type LoadResult = LoadSuccess | LoadError;

// エラー判定関数
function isLoadError(result: LoadResult): result is LoadError {
  return 'code' in result && 'message' in result;
}

/**
 * Duck APIからParquetスナップショットを取得
 */
async function fetchLocationUriSnapshot(version: number): Promise<Uint8Array | LoadError> {
  const url = `http://${env.DUCK_API_HOST}:${env.DUCK_API_PORT}/api/snapshot/${version}`;
  
  try {
    logger.info(`[fetchLocationUriSnapshot] Fetching snapshot for version ${version}`);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      logger.error(`[fetchLocationUriSnapshot] HTTP error: ${response.status}`, errorText);
      
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
    
    const arrayBuffer = await response.arrayBuffer();
    logger.info(`[fetchLocationUriSnapshot] Downloaded ${arrayBuffer.byteLength} bytes`);
    
    return new Uint8Array(arrayBuffer);
  } catch (error) {
    logger.error('[fetchLocationUriSnapshot] Network error:', error);
    return {
      code: 'NETWORK_ERROR',
      message: `[Network Error] ${error instanceof Error ? error.message : String(error)}`
    };
  }
}

/**
 * DuckLakeのLocationURIデータをKuzuにロード
 * 公式ドキュメント準拠の実装
 */
export async function loadLocationUrisFromDuck(conn: any, version: number): Promise<LoadResult> {
  logger.info(`[loadLocationUrisFromDuck] Starting LocationURI load for version ${version}`);
  
  // 1. Duck APIからParquetスナップショットを取得
  const snapshotResult = await fetchLocationUriSnapshot(version);
  
  if (isLoadError(snapshotResult)) {
    return snapshotResult;
  }
  
  // 2. kuzu-wasmのファイルシステムにParquetファイルを書き込む
  // 公式ドキュメント準拠: シンプルなパスを使用
  const filePath = `/locationuri_v${version}.parquet`;
  
  // グローバルのkuzuオブジェクトを取得
  const kuzu = (window as any).kuzu;
  if (!kuzu || !kuzu.FS) {
    return {
      code: 'KUZU_NOT_READY',
      message: '[Kuzu Error] Kuzu-wasm file system not available'
    };
  }
  
  try {
    // 公式ドキュメント準拠: kuzu.FS.writeFileを使用
    kuzu.FS.writeFile(filePath, snapshotResult);
    logger.info(`[loadLocationUrisFromDuck] Wrote ${snapshotResult.byteLength} bytes to ${filePath}`);
  } catch (error) {
    logger.error('[loadLocationUrisFromDuck] FS write error:', error);
    return {
      code: 'FS_WRITE_ERROR',
      message: `[FS Write Error] ${error instanceof Error ? error.message : String(error)}`
    };
  }
  
  try {
    // 3. 既存のLocationURIデータをクリア（トランザクション内）
    logger.info('[loadLocationUrisFromDuck] Clearing existing LocationURI data');
    
    await conn.query("BEGIN TRANSACTION");
    
    // まず関係を削除
    const clearRelResult = await conn.query("MATCH (:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(:LocationURI) DELETE r");
    await clearRelResult.close();
    
    // 次にノードを削除
    const clearNodeResult = await conn.query("MATCH (l:LocationURI) DELETE l");
    await clearNodeResult.close();
    
    await conn.query("COMMIT");
    
    // 4. ParquetファイルからLocationURIをロード（自動トランザクションモード）
    logger.info(`[loadLocationUrisFromDuck] Loading LocationURI from ${filePath}`);
    
    // 公式ドキュメント準拠: COPY FROMでファイルパスを指定
    const copyQuery = `COPY LocationURI FROM '${filePath}';`;
    logger.debug(`[loadLocationUrisFromDuck] Executing: ${copyQuery}`);
    
    const copyResult = await conn.query(copyQuery);
    await copyResult.close();
    
    // 5. ロードされた件数を確認
    const countResult = await conn.query("MATCH (l:LocationURI) RETURN count(l) as count");
    const countData = await countResult.getAllObjects();
    await countResult.close();
    const loadedCount = countData[0]?.count || 0;
    
    logger.info(`[loadLocationUrisFromDuck] Loaded ${loadedCount} LocationURI nodes`);
    
    // 6. VersionStateとの関係を作成（別トランザクション）
    await conn.query("BEGIN TRANSACTION");
    
    const versionId = `ducklake-v${version}`;
    const relQuery = `
      MATCH (v:VersionState {id: '${versionId}'}), (l:LocationURI)
      CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l)
    `;
    const relResult = await conn.query(relQuery);
    await relResult.close();
    
    logger.info(`[loadLocationUrisFromDuck] Created TRACKS_STATE_OF_LOCATED_ENTITY relationships`);
    
    await conn.query("COMMIT");
    
    // 7. 一時ファイルをクリーンアップ
    try {
      kuzu.FS.unlink(filePath);
    } catch (e) {
      logger.debug('[loadLocationUrisFromDuck] Failed to cleanup temp file:', e);
    }
    
    return { loadedCount, version };
  } catch (error) {
    logger.error('[loadLocationUrisFromDuck] Error during load:', error);
    
    // クリーンアップ
    try {
      kuzu.FS.unlink(filePath);
    } catch (e) {
      // エラーを無視
    }
    
    return {
      code: 'LOAD_ERROR',
      message: `[LocationURI Load Error] ${error instanceof Error ? error.message : String(error)}`
    };
  }
}
