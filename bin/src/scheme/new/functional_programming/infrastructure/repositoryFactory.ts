/**
 * repositoryFactory.ts
 * 
 * リポジトリの実装を生成するファクトリ
 * 設定に基づいて適切なリポジトリを返す
 */

import { SchemaRepository, TransactionalSchemaRepository } from '../domain/schemaRepository.ts';
import { createSchemaFileRepository } from './schemaFileRepository.ts';
import { createSchemaDbRepository } from './schemaDbRepository.ts';
import { createDbClient, DbConfig } from './dbClient.ts';

/**
 * リポジトリの種類を表す列挙型
 */
export enum RepositoryType {
  FILE = 'file',
  DB = 'db',
  MEMORY = 'memory'
}

/**
 * リポジトリの設定インターフェース
 */
export interface RepositoryConfig {
  type: RepositoryType;
  basePath?: string; // ファイルリポジトリのベースディレクトリ
  dbConfig?: DbConfig; // DBリポジトリの設定
}

/**
 * デフォルトのリポジトリ設定
 */
export const defaultRepositoryConfig: RepositoryConfig = {
  type: RepositoryType.FILE,
  basePath: '.'
};

/**
 * スキーマリポジトリを生成するファクトリ関数
 * 設定に基づいて適切なリポジトリ実装を返す
 * 
 * @param config リポジトリの設定
 * @returns スキーマリポジトリのインスタンス
 */
export function createSchemaRepository(
  config: RepositoryConfig = defaultRepositoryConfig
): SchemaRepository {
  switch (config.type) {
    case RepositoryType.FILE:
      return createSchemaFileRepository(config.basePath || '.');
    
    case RepositoryType.DB:
      if (!config.dbConfig) {
        throw new Error('DB リポジトリの設定が指定されていません。');
      }
      const dbClient = createDbClient(config.dbConfig);
      return createSchemaDbRepository(dbClient);
    
    case RepositoryType.MEMORY:
      // インメモリDBを使用
      const memoryDbConfig: DbConfig = { type: 'inmemory' };
      const memoryClient = createDbClient(memoryDbConfig);
      return createSchemaDbRepository(memoryClient);
    
    default:
      throw new Error(`サポートされていないリポジトリタイプ: ${(config as any).type}`);
  }
}

/**
 * トランザクション対応スキーマリポジトリを生成するファクトリ関数
 * 
 * @param config リポジトリの設定
 * @returns トランザクション対応スキーマリポジトリのインスタンス
 */
export function createTransactionalSchemaRepository(
  config: RepositoryConfig = { type: RepositoryType.DB, dbConfig: { type: 'inmemory' } }
): TransactionalSchemaRepository {
  if (config.type === RepositoryType.FILE) {
    throw new Error('ファイルリポジトリはトランザクションをサポートしていません。');
  }
  
  const dbConfig = config.dbConfig || { type: 'inmemory' };
  const dbClient = createDbClient(dbConfig);
  
  // ここでは戻り値の型をキャストしています
  // 実際には createSchemaDbRepository が TransactionalSchemaRepository を返すことを確認する必要があります
  return createSchemaDbRepository(dbClient) as TransactionalSchemaRepository;
}
