/**
 * DuckLakeバージョンをkuzu-wasmへ挿入するユースケース
 * Phase 1の動作確認用（一時的な実装）
 */
import * as logger from '../../../common/infrastructure/logger';
import { executeDMLQuery } from '../../infrastructure/repository/queryExecutor';
import { createDuckApiClient } from '../../infrastructure/repository/duckApiClient';
import { env } from '../../infrastructure/config/variables';

// エラー型定義（規約準拠）
type InsertError = {
  code: string;
  message: string;
};

type InsertSuccess = {
  insertedCount: number;
};

type InsertResult = InsertSuccess | InsertError;

// エラー判定関数
function isInsertError(result: InsertResult): result is InsertError {
  return 'code' in result && 'message' in result;
}

/**
 * DuckLakeバージョンをVersionStateノードとして挿入
 */
export async function insertDuckVersions(conn: any): Promise<InsertResult> {
  logger.info('[insertDuckVersions] Starting DuckLake version insertion');
  
  // Duck APIクライアント作成
  const duckApiClient = createDuckApiClient({
    host: env.DUCK_API_HOST,
    port: env.DUCK_API_PORT
  });
  
  // バージョン一覧取得
  const versionsResult = await duckApiClient.fetchVersions();
  
  if ('code' in versionsResult) {
    logger.error('[insertDuckVersions] Failed to fetch versions:', versionsResult);
    return {
      code: 'FETCH_ERROR',
      message: `[DuckLake Fetch Error] ${versionsResult.message}`
    };
  }
  
  logger.info(`[insertDuckVersions] Fetched ${versionsResult.versions.length} versions from DuckLake`);
  
  // デバッグ: DuckLakeから返されたデータを確認
  logger.info('[insertDuckVersions] DuckLake versions raw data:', JSON.stringify(versionsResult.versions, null, 2));
  
  // 各バージョンのデータ構造を確認
  versionsResult.versions.forEach((v, index) => {
    logger.info(`[insertDuckVersions] Version[${index}] structure:`, {
      hasVersion: 'version' in v,
      versionValue: v.version,
      versionType: typeof v.version,
      hasTimestamp: 'timestamp' in v,
      timestampValue: v.timestamp,
      allKeys: Object.keys(v)
    });
  });
  
  // トランザクション開始
  await conn.query("BEGIN TRANSACTION");
  
  try {
    let insertedCount = 0;
    
    // 各バージョンをVersionStateとして挿入
    for (const duckVersion of versionsResult.versions) {
      // デバッグ: 現在処理中のバージョンデータ
      logger.info(`[insertDuckVersions] Processing version data:`, JSON.stringify(duckVersion));
      
      // NULL値チェック（versionIdを生成する前に）
      if (!duckVersion.version || !duckVersion.timestamp) {
        logger.error(`[insertDuckVersions] Missing required fields:`, {
          version: duckVersion.version,
          timestamp: duckVersion.timestamp,
          fullData: JSON.stringify(duckVersion)
        });
        continue;
      }
      
      const versionId = `ducklake-v${duckVersion.version}`;
      logger.info(`[insertDuckVersions] Generated versionId: ${versionId}`);
      
      // 既存チェック
      logger.info(`[insertDuckVersions] Checking existence of ${versionId}`);
      let checkResult;
      try {
        checkResult = await conn.query(
          `MATCH (v:VersionState {id: '${versionId}'}) RETURN v`
        );
      } catch (checkError) {
        logger.error(`[insertDuckVersions] Error in existence check for ${versionId}:`, checkError);
        throw checkError;
      }
      const checkData = await checkResult.getAllObjects();
      await checkResult.close();
      logger.info(`[insertDuckVersions] Existence check result: ${checkData.length} found`);
      
      if (checkData.length === 0) {
        // パラメータ作成
        const params = {
          versionId: versionId,
          timestamp: duckVersion.timestamp || new Date().toISOString(),
          description: `DuckLake v${duckVersion.version}: ${duckVersion.description || 'No description'}`,
          change_reason: `Rows: ${duckVersion.row_count || 0}, Changes: +${duckVersion.changes?.inserts || 0} -${duckVersion.changes?.deletes || 0}`,
          progress_percentage: 100.0
        };
        logger.info(`[insertDuckVersions] Creating VersionState for ${versionId}`);
        
        // VersionStateノード作成
        logger.info(`[insertDuckVersions] Executing CREATE query for ${versionId}`);
        let createResult;
        try {
          // 文字列エスケープ処理
          const escapedId = versionId.replace(/'/g, "''");
          const escapedTimestamp = params.timestamp.replace(/'/g, "''");
          const escapedDescription = params.description.replace(/'/g, "''");
          const escapedReason = params.change_reason.replace(/'/g, "''");
          
          const createQuery = `CREATE (v:VersionState {
            id: '${escapedId}',
            timestamp: '${escapedTimestamp}',
            description: '${escapedDescription}',
            change_reason: '${escapedReason}',
            progress_percentage: ${params.progress_percentage}
          })`;
          
          logger.info(`[insertDuckVersions] Query: ${createQuery}`);
          
          createResult = await conn.query(createQuery);
        } catch (createError) {
          logger.error(`[insertDuckVersions] Error in CREATE for ${versionId}:`, createError);
          logger.error(`[insertDuckVersions] Query params were:`, JSON.stringify(params, null, 2));
          logger.error(`[insertDuckVersions] Raw duckVersion data:`, JSON.stringify(duckVersion, null, 2));
          throw createError;
        }
        await createResult.close();
        
        insertedCount++;
        logger.info(`[insertDuckVersions] Successfully inserted version: ${versionId}`);
      } else {
        logger.info(`[insertDuckVersions] Version already exists: ${versionId}`);
      }
    }
    
    // FOLLOWS関係作成（バージョン番号順）
    const sortedVersions = [...versionsResult.versions].sort((a, b) => a.version - b.version);
    for (let i = 1; i < sortedVersions.length; i++) {
      const fromId = `ducklake-v${sortedVersions[i - 1].version}`;
      const toId = `ducklake-v${sortedVersions[i].version}`;
      
      // 既存の関係チェック
      const followsCheckResult = await conn.query(
        `MATCH (v1:VersionState {id: '${fromId}'})-[:FOLLOWS]->(v2:VersionState {id: '${toId}'}) RETURN count(*) as count`
      );
      const followsCheckData = await followsCheckResult.getAllObjects();
      await followsCheckResult.close();
      
      if (followsCheckData[0].count === 0) {
        const followsResult = await conn.query(
          `MATCH (v1:VersionState {id: '${fromId}'}), (v2:VersionState {id: '${toId}'}) CREATE (v1)-[:FOLLOWS]->(v2)`
        );
        await followsResult.close();
        logger.info(`[insertDuckVersions] Created FOLLOWS: ${fromId} -> ${toId}`);
      }
    }
    
    await conn.query("COMMIT");
    logger.info(`[insertDuckVersions] Successfully inserted ${insertedCount} DuckLake versions`);
    
    return { insertedCount };
  } catch (error) {
    logger.error('[insertDuckVersions] Error during insertion:', error);
    
    try {
      await conn.query("ROLLBACK");
      logger.info('[insertDuckVersions] Transaction rolled back');
    } catch (rollbackError) {
      logger.error('[insertDuckVersions] Rollback error:', rollbackError);
    }
    
    return {
      code: 'INSERT_ERROR',
      message: `[DuckLake Insert Error] ${error instanceof Error ? error.message : String(error)}`
    };
  }
}
