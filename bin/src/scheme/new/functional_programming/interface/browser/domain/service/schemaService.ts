/**
 * schemaService.ts
 * 
 * スキーマ関連のアプリケーションサービス
 */

import { FunctionSchema } from '/home/nixos/scheme/new/functional_programming/domain/schema.ts';
import { Graph } from '/home/nixos/scheme/new/functional_programming/domain/entities/graph.ts';
import { SchemaRepository } from '../repository/schemaRepository.ts';
import { TreeNode } from '../models/treeNode.ts';
import { buildTreeFromFunctionData } from '../service/treeService.ts';

/**
 * スキーマサービスクラス
 */
export class SchemaService {
  /**
   * コンストラクタ
   * @param repository スキーマリポジトリ
   */
  constructor(private repository: SchemaRepository) {}

  /**
   * 利用可能なすべてのスキーマを取得
   */
  async getAllSchemas(): Promise<FunctionSchema[]> {
    return this.repository.getAllSchemas();
  }

  /**
   * スキーマリストを取得
   */
  async getSchemaList(): Promise<string[]> {
    return this.repository.getSchemaList();
  }

  /**
   * 指定パスのスキーマを取得
   */
  async loadSchema(path: string): Promise<FunctionSchema> {
    return this.repository.loadSchema(path);
  }

  /**
   * 依存関係グラフを取得
   */
  async getDependencyGraph(rootSchemaPath: string): Promise<Graph> {
    return this.repository.getDependencyGraph(rootSchemaPath);
  }

  /**
   * スキーマからツリー構造を構築
   */
  async buildSchemaTree(): Promise<TreeNode> {
    const schemas = await this.repository.getAllSchemas();
    return buildTreeFromFunctionData(schemas);
  }
}
