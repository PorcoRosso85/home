/**
 * Infrastructure: Environment-specific KuzuDB loading
 */

export type KuzuModule = {
  Database: any;
  Connection: any;
  close?: () => Promise<void>;  // Optional since not all modules have it
};

/**
 * 環境検出
 */
export function detectEnvironment(): 'browser' | 'node' {
  if (typeof window !== 'undefined') return 'browser';
  if (typeof process !== 'undefined') return 'node';
  return 'node'; // デフォルト
}

/**
 * KuzuDBモジュールのロード
 */
export async function loadKuzu(): Promise<KuzuModule> {
  const env = detectEnvironment();
  
  if (env === 'browser') {
    console.log('🌐 Initializing KuzuDB for browser...');
    return await import('kuzu-wasm');
  } else {
    console.log('🖥️ Initializing KuzuDB for Node.js...');
    // For Node.js, use createRequire to load CommonJS module
    const { createRequire } = await import('module');
    const require = createRequire(import.meta.url || process.cwd());
    return require('kuzu-wasm/nodejs');
  }
}

/**
 * データベースインスタンスの作成
 */
export type DatabaseConfig = {
  path?: string;  // デフォルト: ':memory:'
  memorySize?: number;  // デフォルト: 256MB
  numThreads?: number;  // デフォルト: 4
};

export function createKuzuDatabase(
  kuzu: KuzuModule,
  config: DatabaseConfig = {}
): any {
  const {
    path = ':memory:',
    memorySize = 1 << 28,  // 256MB
    numThreads = 4
  } = config;
  
  const db = new kuzu.Database(path, memorySize);
  const conn = new kuzu.Connection(db, numThreads);
  
  return { db, conn };
}

/**
 * リソースのクリーンアップ
 */
export async function cleanupKuzu(resources: {
  conn?: any;
  db?: any;
  kuzu?: KuzuModule;
}): Promise<void> {
  console.log('🧹 Cleaning up KuzuDB resources...');
  
  if (resources.conn) {
    await resources.conn.close();
  }
  
  if (resources.db) {
    await resources.db.close();
  }
  
  if (resources.kuzu && resources.kuzu.close) {
    await resources.kuzu.close();
  }
}