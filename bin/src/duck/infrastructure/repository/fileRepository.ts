/**
 * File Repository
 * ファイルシステム操作を提供
 */

import type { FileInfo } from "../../domain/types.ts";

// リポジトリインターフェース
export type FileRepository = {
  listParquetFiles: () => Promise<FileInfo[]>;
  getFileCount: () => Promise<number>;
  getTotalSize: () => Promise<number>;
  cleanupTempDirectory: (path: string) => Promise<boolean>;
};

// 高階関数による依存性注入
export function createFileRepository(dataPath: string): FileRepository {
  
  async function listParquetFiles(): Promise<FileInfo[]> {
    const files: FileInfo[] = [];
    
    // DenoのファイルシステムAPIを使用
    const entries = [];
    for await (const entry of Deno.readDir(dataPath)) {
      if (entry.isFile && entry.name.endsWith('.parquet')) {
        entries.push(entry);
      }
    }
    
    // 各ファイルの詳細情報を取得
    for (const entry of entries) {
      const filePath = `${dataPath}/${entry.name}`;
      const stat = await Deno.stat(filePath).catch(() => null);
      
      if (stat) {
        files.push({
          path: filePath,
          size: stat.size,
          type: entry.name.includes('delete') ? 'delete' : 'data',
          createdAt: stat.mtime?.toISOString() || new Date().toISOString()
        });
      }
    }
    
    return files;
  }
  
  async function getFileCount(): Promise<number> {
    const files = await listParquetFiles();
    return files.length;
  }
  
  async function getTotalSize(): Promise<number> {
    const files = await listParquetFiles();
    return files.reduce((total, file) => total + file.size, 0);
  }
  
  async function cleanupTempDirectory(path: string): Promise<boolean> {
    const result = await Deno.remove(path, { recursive: true })
      .then(() => true)
      .catch(() => false);
    return result;
  }
  
  return {
    listParquetFiles,
    getFileCount,
    getTotalSize,
    cleanupTempDirectory
  };
}

// テスト用のモックリポジトリ作成関数
export function createMockFileRepository(mockFiles: FileInfo[] = []): FileRepository {
  return {
    listParquetFiles: async () => mockFiles,
    getFileCount: async () => mockFiles.length,
    getTotalSize: async () => mockFiles.reduce((sum, f) => sum + f.size, 0),
    cleanupTempDirectory: async () => true
  };
}
