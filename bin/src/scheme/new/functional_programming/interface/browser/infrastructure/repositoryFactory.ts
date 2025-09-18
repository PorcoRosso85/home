/**
 * repositoryFactory.ts
 * 
 * リポジトリインスタンスを提供するファクトリー
 */

import { SchemaRepository } from '../domain/repository/schemaRepository.ts';
import { MockSchemaRepository } from './mockSchemaRepository.ts';

/**
 * モックスキーマリポジトリを作成する
 */
export function createSchemaRepository(): SchemaRepository {
  return new MockSchemaRepository();
}
