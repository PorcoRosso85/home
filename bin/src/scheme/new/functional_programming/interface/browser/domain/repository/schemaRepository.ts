/**
 * schemaRepository.ts
 * 
 * スキーマデータのリポジトリインターフェース
 */

import { FunctionSchema } from '/home/nixos/scheme/new/functional_programming/domain/schema.ts';
import { Graph } from '/home/nixos/scheme/new/functional_programming/domain/entities/graph.ts';

/**
 * スキーマリポジトリインターフェース
 * 
 * スキーマデータにアクセスするための抽象インターフェース
 */
export interface SchemaRepository {
  /**
   * 利用可能なスキーマのパスリストを取得
   */
  getSchemaList(): Promise<string[]>;
  
  /**
   * 指定したパスのスキーマを取得
   */
  loadSchema(path: string): Promise<FunctionSchema>;

  /**
   * すべてのスキーマを取得
   */
  getAllSchemas(): Promise<FunctionSchema[]>;
  
  /**
   * 依存関係グラフを取得
   */
  getDependencyGraph(rootSchemaPath: string): Promise<Graph>;
}
