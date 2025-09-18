/**
 * DuckLakeから任意のテーブルデータをParquet形式で取得してKuzuにロードする汎用ユースケース
 * 並列取得対応版
 */
import * as logger from '../../../common/infrastructure/logger';
import { env } from '../../infrastructure/config/variables';

// エラー型定義（規約準拠）
type LoadError = {
  code: string;
  message: string;
  table?: string;
};

type LoadSuccess = {
  loadedCount: number;
  version: number;
  table: string;
};

type LoadResult = LoadSuccess | LoadError;

// テーブルごとの結果型
type TableLoadResult = {
  table: string;
  result: LoadResult;
};

// エラー判定関数
function isLoadError(result: LoadResult): result is LoadError {
  return 'code' in result && 'message' in result;
}

/**
 * Duck APIから指定テーブルのParquetスナップショットを取得（リトライ付き）
 */
async function fetchTableSnapshot(version: number, tableName: string): Promise<Uint8Array | LoadError> {
  const url = `http://${env.DUCK_API_HOST}:${env.DUCK_API_PORT}/api/snapshot/${version}/${tableName}`;
  const maxRetries = parseInt(env.DUCKLAKE_MAX_RETRIES);
  const retryDelayMs = parseInt(env.DUCKLAKE_RETRY_DELAY_MS);
  
  let lastError: LoadError | null = null;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      logger.info(`[fetchTableSnapshot] Fetching ${tableName} snapshot for version ${version} (attempt ${attempt + 1}/${maxRetries})`);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        logger.error(`[fetchTableSnapshot] HTTP error: ${response.status}`, errorText);
        
        try {
          const errorJson = JSON.parse(errorText);
          lastError = {
            code: errorJson.code || 'HTTP_ERROR',
            message: errorJson.message || `HTTP ${response.status}: ${response.statusText}`,
            table: tableName
          };
          
          // TABLE_NOT_FOUNDエラーの場合はリトライしない
          if (errorJson.code === 'TABLE_NOT_FOUND') {
            return lastError;
          }
        } catch {
          lastError = {
            code: 'HTTP_ERROR',
            message: `HTTP ${response.status}: ${response.statusText}`,
            table: tableName
          };
        }
        
        // リトライ前に待機
        if (attempt < maxRetries - 1) {
          logger.info(`[fetchTableSnapshot] Retrying after ${retryDelayMs}ms...`);
          await new Promise(resolve => setTimeout(resolve, retryDelayMs * (attempt + 1)));
          continue;
        }
      } else {
        // 成功時
        const arrayBuffer = await response.arrayBuffer();
        logger.info(`[fetchTableSnapshot] Downloaded ${tableName}: ${arrayBuffer.byteLength} bytes`);
        return new Uint8Array(arrayBuffer);
      }
    } catch (error) {
      logger.error(`[fetchTableSnapshot] Network error for ${tableName}:`, error);
      lastError = {
        code: 'NETWORK_ERROR',
        message: `[Network Error] ${error instanceof Error ? error.message : String(error)}`,
        table: tableName
      };
      
      // ネットワークエラーの場合、リトライ前に待機
      if (attempt < maxRetries - 1) {
        logger.info(`[fetchTableSnapshot] Retrying after ${retryDelayMs}ms...`);
        await new Promise(resolve => setTimeout(resolve, retryDelayMs * (attempt + 1)));
      }
    }
  }
  
  return lastError || {
    code: 'UNKNOWN_ERROR',
    message: '[Unknown Error] Failed to fetch snapshot after all retries',
    table: tableName
  };
}
/**
 * DuckLakeの指定テーブルデータをKuzuにロード（汎用版）
 */
export async function loadTableFromDuck(conn: any, version: number, tableName: string): Promise<LoadResult> {
  logger.info(`[loadTableFromDuck] Starting ${tableName} load for version ${version}`);
  
  // 1. Duck APIからParquetスナップショットを取得
  const snapshotResult = await fetchTableSnapshot(version, tableName);
  
  if (isLoadError(snapshotResult)) {
    return snapshotResult;
  }
  
  // 2. kuzu-wasmのファイルシステムにParquetファイルを書き込む
  const filePath = `/${tableName.toLowerCase()}_v${version}.parquet`;
  
  // グローバルのkuzuオブジェクトを取得
  const kuzu = (window as any).kuzu;
  if (!kuzu || !kuzu.FS) {
    return {
      code: 'KUZU_NOT_READY',
      message: '[Kuzu Error] Kuzu-wasm file system not available',
      table: tableName
    };
  }
  
  try {
    // kuzu.FS.writeFileを使用
    kuzu.FS.writeFile(filePath, snapshotResult);
    logger.info(`[loadTableFromDuck] Wrote ${snapshotResult.byteLength} bytes to ${filePath}`);
  } catch (error) {
    logger.error(`[loadTableFromDuck] FS write error for ${tableName}:`, error);
    return {
      code: 'FS_WRITE_ERROR',
      message: `[FS Write Error] ${error instanceof Error ? error.message : String(error)}`,
      table: tableName
    };
  }
  
  try {
    // 3. 既存のテーブルデータをクリア（トランザクション内）
    logger.info(`[loadTableFromDuck] Clearing existing ${tableName} data`);
    
    await conn.query("BEGIN TRANSACTION");
    
    // テーブルごとの関係削除処理（将来的に拡張可能）
    if (tableName === 'LocationURI') {
      const clearRelResult = await conn.query("MATCH (:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(:LocationURI) DELETE r");
      await clearRelResult.close();
    }
    // TODO: 他のテーブルの関係削除処理を追加
    
    // ノードを削除
    const clearNodeResult = await conn.query(`MATCH (n:${tableName}) DELETE n`);
    await clearNodeResult.close();
    
    await conn.query("COMMIT");
    
    // 4. ParquetファイルからKuzuにロード
    logger.info(`[loadTableFromDuck] Loading ${tableName} from ${filePath}`);
    
    const copyQuery = `COPY ${tableName} FROM '${filePath}';`;
    logger.debug(`[loadTableFromDuck] Executing: ${copyQuery}`);
    
    const copyResult = await conn.query(copyQuery);
    await copyResult.close();
    
    // 5. ロードされた件数を確認
    const countResult = await conn.query(`MATCH (n:${tableName}) RETURN count(n) as count`);
    const countData = await countResult.getAllObjects();
    await countResult.close();
    const loadedCount = countData[0]?.count || 0;
    
    logger.info(`[loadTableFromDuck] Loaded ${loadedCount} ${tableName} nodes`);
    
    // 6. VersionStateとの関係を作成（LocationURIの場合）
    if (tableName === 'LocationURI') {
      await conn.query("BEGIN TRANSACTION");
      
      const versionId = `ducklake-v${version}`;
      const relQuery = `
        MATCH (v:VersionState {id: '${versionId}'}), (l:LocationURI)
        CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(l)
      `;
      const relResult = await conn.query(relQuery);
      await relResult.close();
      
      logger.info(`[loadTableFromDuck] Created TRACKS_STATE_OF_LOCATED_ENTITY relationships`);
      
      await conn.query("COMMIT");
    }
    
    // 7. 一時ファイルをクリーンアップ
    try {
      kuzu.FS.unlink(filePath);
    } catch (e) {
      logger.debug(`[loadTableFromDuck] Failed to cleanup temp file ${filePath}:`, e);
    }
    
    return { loadedCount, version, table: tableName };
  } catch (error) {
    logger.error(`[loadTableFromDuck] Error during ${tableName} load:`, error);
    
    // クリーンアップ
    try {
      kuzu.FS.unlink(filePath);
    } catch (e) {
      // エラーを無視
    }
    
    return {
      code: 'LOAD_ERROR',
      message: `[${tableName} Load Error] ${error instanceof Error ? error.message : String(error)}`,
      table: tableName
    };
  }
}
/**
 * 同時接続数を制限した並列処理ユーティリティ
 */
async function processWithConcurrencyLimit<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  concurrency: number
): Promise<R[]> {
  const results: R[] = [];
  const executing: Promise<void>[] = [];
  
  for (const item of items) {
    const promise = processor(item).then(result => {
      results.push(result);
    });
    
    executing.push(promise);
    
    if (executing.length >= concurrency) {
      await Promise.race(executing);
      const completed = await Promise.allSettled(executing);
      const resolvedIndexes = completed
        .map((result, index) => result.status === 'fulfilled' ? index : -1)
        .filter(index => index >= 0);
      
      for (const index of resolvedIndexes.reverse()) {
        executing.splice(index, 1);
      }
    }
  }
  
  await Promise.all(executing);
  return results;
}

/**
 * 複数テーブルを並列でロード
 * 
 * @param conn - Kuzu接続
 * @param version - スナップショットバージョン
 * @param tableNames - ロードするテーブル名の配列
 * @param onProgress - 進捗コールバック（オプション）
 * @returns 各テーブルのロード結果
 */
export async function loadTablesFromDuck(
  conn: any,
  version: number,
  tableNames: string[],
  onProgress?: (completed: number, total: number) => void
): Promise<TableLoadResult[]> {
  const concurrency = parseInt(env.DUCKLAKE_CONCURRENT_CONNECTIONS);
  
  logger.info(`[loadTablesFromDuck] Loading ${tableNames.length} tables with concurrency ${concurrency}`);
  
  let completed = 0;
  const processor = async (tableName: string): Promise<TableLoadResult> => {
    const result = await loadTableFromDuck(conn, version, tableName);
    completed++;
    
    if (onProgress) {
      onProgress(completed, tableNames.length);
    }
    
    return { table: tableName, result };
  };
  
  const results = await processWithConcurrencyLimit(
    tableNames,
    processor,
    concurrency
  );
  
  // 成功/失敗のサマリーログ
  const successful = results.filter(r => !isLoadError(r.result));
  const failed = results.filter(r => isLoadError(r.result));
  
  logger.info(`[loadTablesFromDuck] Completed: ${successful.length} successful, ${failed.length} failed`);
  
  if (failed.length > 0) {
    logger.warn('[loadTablesFromDuck] Failed tables:', failed.map(f => f.table).join(', '));
  }
  
  return results;
}

/**
 * LocationURIを単独でロード（後方互換性のためのラッパー）
 */
export async function loadLocationUrisFromDuck(conn: any, version: number): Promise<LoadResult> {
  return loadTableFromDuck(conn, version, 'LocationURI');
}