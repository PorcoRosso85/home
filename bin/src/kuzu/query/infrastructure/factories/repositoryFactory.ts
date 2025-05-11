/**
 * Repository Factory
 * 
 * 実行環境に応じて適切なリポジトリ実装を生成する関数群
 */

import type { QueryResult } from '../repositories/browserQueryRepository';

// リポジトリインターフェースの型定義
export type QueryRepository = {
  findQueryFile: (queryName: string) => Promise<[boolean, string]> | [boolean, string];
  readQueryFile: (filePath: string) => Promise<QueryResult<string>> | QueryResult<string>;
  getAvailableQueries: () => Promise<string[]> | string[];
  getQuery: (queryName: string, fallbackQuery?: string) => Promise<QueryResult<string>> | QueryResult<string>;
  executeQuery: (connection: any, queryName: string, params?: Record<string, any>) => Promise<QueryResult<any>>;
  getSuccess: <T>(result: QueryResult<T>) => boolean;
};

// 環境検出用のヘルパー関数
export function detectEnvironment(): 'browser' | 'node' | 'deno' {
  if (typeof Deno !== 'undefined') {
    return 'deno';
  } else if (typeof window !== 'undefined' && typeof document !== 'undefined') {
    return 'browser';
  } else if (typeof process !== 'undefined' && process.versions?.node) {
    return 'node';
  } else {
    // デフォルトはブラウザ
    return 'browser';
  }
}

/**
 * 環境に応じて適切なリポジトリを動的にインポートして返す
 */
export async function createQueryRepository(): Promise<QueryRepository> {
  const environment = detectEnvironment();
  
  switch (environment) {
    case 'browser':
      const browserRepo = await import('../repositories/browserQueryRepository');
      return {
        findQueryFile: browserRepo.findQueryFile,
        readQueryFile: browserRepo.readQueryFile,
        getAvailableQueries: browserRepo.getAvailableQueries,
        getQuery: browserRepo.getQuery,
        executeQuery: browserRepo.executeQuery,
        getSuccess: browserRepo.getSuccess,
      };
      
    case 'node':
      const nodeRepo = await import('../repositories/nodeQueryRepository');
      return {
        findQueryFile: nodeRepo.findQueryFile,
        readQueryFile: nodeRepo.readQueryFile,
        getAvailableQueries: nodeRepo.getAvailableQueries,
        getQuery: nodeRepo.getQuery,
        executeQuery: nodeRepo.executeQuery,
        getSuccess: nodeRepo.getSuccess,
      };
      
    case 'deno':
      const denoRepo = await import('../repositories/denoQueryRepository');
      return {
        findQueryFile: denoRepo.findQueryFile,
        readQueryFile: denoRepo.readQueryFile,
        getAvailableQueries: denoRepo.getAvailableQueries,
        getQuery: denoRepo.getQuery,
        executeQuery: denoRepo.executeQuery,
        getSuccess: denoRepo.getSuccess,
      };
      
    default:
      throw new Error(`Unsupported environment: ${environment}`);
  }
}

/**
 * 特定の環境用のリポジトリを明示的に作成する
 */
export async function createBrowserRepository(): Promise<QueryRepository> {
  const browserRepo = await import('../repositories/browserQueryRepository');
  return {
    findQueryFile: browserRepo.findQueryFile,
    readQueryFile: browserRepo.readQueryFile,
    getAvailableQueries: browserRepo.getAvailableQueries,
    getQuery: browserRepo.getQuery,
    executeQuery: browserRepo.executeQuery,
    getSuccess: browserRepo.getSuccess,
  };
}

export async function createNodeRepository(): Promise<QueryRepository> {
  const nodeRepo = await import('../repositories/nodeQueryRepository');
  return {
    findQueryFile: nodeRepo.findQueryFile,
    readQueryFile: nodeRepo.readQueryFile,
    getAvailableQueries: nodeRepo.getAvailableQueries,
    getQuery: nodeRepo.getQuery,
    executeQuery: nodeRepo.executeQuery,
    getSuccess: nodeRepo.getSuccess,
  };
}

export async function createDenoRepository(): Promise<QueryRepository> {
  const denoRepo = await import('../repositories/denoQueryRepository');
  return {
    findQueryFile: denoRepo.findQueryFile,
    readQueryFile: denoRepo.readQueryFile,
    getAvailableQueries: denoRepo.getAvailableQueries,
    getQuery: denoRepo.getQuery,
    executeQuery: denoRepo.executeQuery,
    getSuccess: denoRepo.getSuccess,
  };
}
