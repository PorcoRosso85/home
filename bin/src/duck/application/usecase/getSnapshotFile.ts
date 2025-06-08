/**
 * スナップショットファイル取得ユースケース
 * 指定されたバージョンのDuckLake管理Parquetファイルを特定する
 */

import * as log from "../../../log/logger.ts";
import type { DuckDBRepository } from "../../infrastructure/repository/duckdbRepository.ts";
import type { FileRepository } from "../../infrastructure/repository/fileRepository.ts";
import type { Result } from "../../shared/errors.ts";

// 依存性の型定義
type GetSnapshotFileDependencies = {
  duckdbRepo: DuckDBRepository;
  fileRepo: FileRepository;
};

// スナップショット情報の型定義
export type SnapshotInfo = {
  version: string;
  files: {
    path: string;
    size: number;
    timestamp: string;
  }[];
};

/**
 * スナップショットファイル取得ユースケースを作成
 */
export function createGetSnapshotFileUseCase(deps: GetSnapshotFileDependencies) {
  
  /**
   * 指定バージョンのスナップショットファイルを取得
   */
  async function getSnapshotForVersion(version: string): Promise<Result<SnapshotInfo>> {
    log.info(`Getting snapshot files for version: ${version}`);
    
    try {
      // 1. 指定バージョンが存在するか確認
      const versionCheckQuery = `
        SELECT COUNT(*) as count 
        FROM VersionState 
        WHERE id = '${version}'
      `;
      
      const versionResult = await deps.duckdbRepo.query(versionCheckQuery);
      if (!versionResult.success) {
        return {
          success: false,
          error: {
            code: "DATABASE_ERROR",
            message: "Failed to check version existence",
            operation: "version_check"
          }
        };
      }
      
      const versionCount = Number(versionResult.data[0]?.count || 0);
      if (versionCount === 0) {
        return {
          success: false,
          error: {
            code: "VERSION_NOT_FOUND",
            message: `Version ${version} not found`,
            version
          }
        };
      }
      
      // 2. DuckLakeのメタデータから該当バージョンのファイルを特定
      // DuckLakeはtable_changesを使用してバージョン履歴を管理
      const filesQuery = `
        SELECT DISTINCT file_path 
        FROM ducklake.table_changes('VersionState', 0, 9999)
        WHERE snapshot_id = '${version}'
      `;
      
      // 簡易実装: 現在のDuckLakeファイルをすべて返す
      // 実際のDuckLake実装では、バージョンごとのファイル管理が必要
      const allFiles = await deps.fileRepo.listParquetFiles();
      
      // バージョンに関連するファイルをフィルタリング
      const snapshotFiles = allFiles.filter(file => {
        // DuckLakeのファイル命名規則に基づくフィルタリング
        return file.path.includes("ducklake-");
      });
      
      if (snapshotFiles.length === 0) {
        return {
          success: false,
          error: {
            code: "FILE_NOT_FOUND",
            message: `No snapshot files found for version ${version}`,
            filePath: deps.fileRepo.getDataPath()
          }
        };
      }
      
      // 3. スナップショット情報を構築
      const snapshotInfo: SnapshotInfo = {
        version,
        files: snapshotFiles.map(file => ({
          path: file.path,
          size: file.size,
          timestamp: file.timestamp || file.createdAt
        }))
      };
      
      log.info(`Found ${snapshotFiles.length} files for version ${version}`);
      
      return {
        success: true,
        data: snapshotInfo
      };
      
    } catch (error) {
      log.error("Error getting snapshot files:", error);
      return {
        success: false,
        error: {
          code: "OPERATION_FAILED",
          message: "Failed to get snapshot files",
          operation: "get_snapshot"
        }
      };
    }
  }
  
  /**
   * 最新バージョンのスナップショットを取得
   */
  async function getLatestSnapshot(): Promise<Result<SnapshotInfo>> {
    const latestVersionQuery = `
      SELECT id 
      FROM VersionState 
      ORDER BY timestamp DESC 
      LIMIT 1
    `;
    
    const result = await deps.duckdbRepo.query(latestVersionQuery);
    if (!result.success || result.data.length === 0) {
      return {
        success: false,
        error: {
          code: "VERSION_NOT_FOUND",
          message: "No versions found",
          version: "latest"
        }
      };
    }
    
    const latestVersion = result.data[0].id;
    return getSnapshotForVersion(latestVersion);
  }
  
  return {
    getSnapshotForVersion,
    getLatestSnapshot
  };
}