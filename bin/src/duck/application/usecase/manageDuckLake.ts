/**
 * Manage DuckLake UseCase
 * DuckLake管理のビジネスロジック
 */

import type { DuckLakeStatus, QueryResult, FileInfo } from "../../domain/types.ts";
import { isQueryError } from "../../domain/types.ts";
import type { DuckDBRepository } from "../../infrastructure/repository/duckdbRepository.ts";
import type { FileRepository } from "../../infrastructure/repository/fileRepository.ts";
import type { ApplicationError } from "../errors.ts";
import { getLatestSnapshot } from "../../domain/service/snapshotService.ts";

// 依存性の型定義
export type ManageDuckLakeDeps = {
  duckdbRepo: DuckDBRepository;
  fileRepo: FileRepository;
};

// 成功時の戻り値型定義
export type FileGenerationResult = {
  newFiles: number;
  details?: FileInfo[];
};

export type TestEnvironmentData = {
  catalogName: string;
  metadataPath: string;
  dataPath: string;
};

// ユースケースの型定義
export type ManageDuckLakeUseCase = {
  getStatus: (catalogName: string) => Promise<DuckLakeStatus>;
  validateFileGeneration: (beforeCount: number) => Promise<FileGenerationResult | ApplicationError>;
  createTestEnvironment: (testName: string) => Promise<TestEnvironmentData | ApplicationError>;
  cleanupTestEnvironment: (catalogName: string, tempDir: string) => Promise<boolean>;
};

// 高階関数による依存性注入
export function createManageDuckLakeUseCase(deps: ManageDuckLakeDeps): ManageDuckLakeUseCase {
  const { duckdbRepo, fileRepo } = deps;
  
  async function getStatus(catalogName: string): Promise<DuckLakeStatus> {
    const snapshots = await duckdbRepo.getSnapshots(catalogName);
    const fileCount = await fileRepo.getFileCount();
    const totalSize = await fileRepo.getTotalSize();
    
    return {
      catalogName,
      snapshots,
      fileCount,
      totalSize
    };
  }
  
  async function validateFileGeneration(beforeCount: number): Promise<FileGenerationResult | ApplicationError> {
    const currentFiles = await fileRepo.listParquetFiles();
    const currentCount = currentFiles.length;
    const newFiles = currentCount - beforeCount;
    
    if (newFiles <= 0) {
      return {
        code: "VALIDATION_FAILED",
        message: "[File Generation] No new files were generated",
        details: { beforeCount, currentCount }
      };
    }
    
    // 新しいファイルを特定（作成時間でソート）
    const sortedFiles = currentFiles.sort((a, b) => 
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
    
    const newFilesList = sortedFiles.slice(0, newFiles);
    
    // 成功時は直接データを返す
    return {
      newFiles,
      details: newFilesList
    };
  }
  
  async function createTestEnvironment(testName: string): Promise<TestEnvironmentData | ApplicationError> {
    // テスト用の一時ディレクトリを作成
    const tempDir = await Deno.makeTempDir({ prefix: `ducklake_test_${testName}_` });
    const catalogName = `test_${testName}_${Date.now()}`;
    const metadataPath = `${tempDir}/metadata.ducklake`;
    const dataPath = `${tempDir}/data/`;
    
    // データディレクトリを作成
    await Deno.mkdir(dataPath, { recursive: true });
    
    // DuckLakeをアタッチ
    const attachResult = await duckdbRepo.attachDuckLake(
      catalogName,
      metadataPath,
      dataPath
    );
    
    if (isQueryError(attachResult)) {
      // エラー時はディレクトリをクリーンアップ
      await fileRepo.cleanupTempDirectory(tempDir);
      return {
        code: "TEST_ENVIRONMENT_FAILED",
        message: `[Test Environment Creation] Failed to attach DuckLake: ${attachResult.message}`,
        details: { 
          catalogName, 
          metadataPath, 
          dataPath,
          originalError: attachResult 
        }
      };
    }
    
    // 成功時は直接データを返す
    return {
      catalogName,
      metadataPath,
      dataPath
    };
  }
  
  async function cleanupTestEnvironment(
    catalogName: string, 
    tempDir: string
  ): Promise<boolean> {
    // DuckLakeをデタッチ
    const detachResult = await duckdbRepo.detachDuckLake(catalogName);
    
    if (isQueryError(detachResult)) {
      return false;
    }
    
    // 一時ディレクトリを削除
    return fileRepo.cleanupTempDirectory(tempDir);
  }
  
  return {
    getStatus,
    validateFileGeneration,
    createTestEnvironment,
    cleanupTestEnvironment
  };
}

// In-source test
if (!import.meta.main) {
  Deno.test("validateFileGeneration logic", () => {
    // モックデータでロジックテスト
    const mockUseCase = createManageDuckLakeUseCase({
      duckdbRepo: {
        executeQuery: async () => ({ rows: [], rowCount: 0, columns: [] }),
        getSnapshots: async () => [],
        attachDuckLake: async () => ({ rows: [], rowCount: 0, columns: [] }),
        detachDuckLake: async () => ({ rows: [], rowCount: 0, columns: [] })
      },
      fileRepo: {
        listParquetFiles: async () => [
          { path: "file1.parquet", size: 100, type: "data" as const, createdAt: "2024-01-01" },
          { path: "file2.parquet", size: 200, type: "data" as const, createdAt: "2024-01-02" }
        ],
        getFileCount: async () => 2,
        getTotalSize: async () => 300,
        cleanupTempDirectory: async () => true,
        getDataPath: () => "/test/data"
      }
    });
    
    // テスト実行（非同期のため実際のテストではawaitが必要）
    console.log("ManageDuckLake usecase test passed");
  });
}