/**
 * Generate Queries Command
 * 
 * クエリ生成に関するコマンド関数群
 * 注意: dmlGenerator削除により一時的に機能停止中
 */

import type { QueryResult } from '../../domain/entities/queryResult';

// dmlGenerator削除により型定義も削除
export type EntityDefinition = {
  entity_type: "node" | "edge";
  table_name: string;
  templates: string[];
  properties: Record<string, any>;
  from_table?: string;
  to_table?: string;
};

/**
 * 単一エンティティからクエリを生成する
 * 注意: dmlGenerator削除により機能停止中
 */
export async function generateQueriesForEntity(
  entityPath: string,
  outputDir?: string
): Promise<QueryResult<void>> {
  return {
    success: false,
    error: "dmlGenerator削除により機能停止中です。代替実装が必要です。"
  };
}

/**
 * 全エンティティからクエリを生成する
 * 注意: dmlGenerator削除により機能停止中
 */
export async function generateAllQueries(
  inputDir?: string,
  outputDir?: string
): Promise<QueryResult<number>> {
  return {
    success: false,
    error: "dmlGenerator削除により機能停止中です。代替実装が必要です。"
  };
}

/**
 * エンティティ定義から動的にクエリを生成する
 * 注意: dmlGenerator削除により機能停止中
 */
export async function generateQueryFromDefinition(
  entityDefinition: EntityDefinition,
  templateType: string
): Promise<QueryResult<string>> {
  return {
    success: false,
    error: "dmlGenerator削除により機能停止中です。代替実装が必要です。"
  };
}

/**
 * クエリテンプレートを生成する（カスタマイズ用）
 * 注意: dmlGenerator削除により機能停止中
 */
export async function generateQueryTemplate(
  entityType: 'node' | 'edge',
  templateType: 'create' | 'match' | 'update' | 'delete',
  tableName: string,
  properties: Record<string, { type: string; primary_key?: boolean }>,
  fromTable?: string,
  toTable?: string
): Promise<QueryResult<string>> {
  return {
    success: false,
    error: "dmlGenerator削除により機能停止中です。代替実装が必要です。"
  };
}

/**
 * 進捗報告付きでクエリを一括生成する
 * 注意: dmlGenerator削除により機能停止中
 */
export async function generateQueriesWithProgress(
  entities: EntityDefinition[],
  outputDir?: string,
  onProgress?: (completed: number, total: number, currentEntity: string) => void
): Promise<QueryResult<number>> {
  return {
    success: false,
    error: "dmlGenerator削除により機能停止中です。代替実装が必要です。"
  };
}

/**
 * バリデーション付きクエリ生成
 * 注意: dmlGenerator削除により機能停止中
 */
export async function generateValidatedQueries(
  entityPath: string,
  outputDir?: string,
  validateBeforeGeneration?: boolean
): Promise<QueryResult<{ generatedCount: number; validationResults: any[] }>> {
  return {
    success: false,
    error: "dmlGenerator削除により機能停止中です。代替実装が必要です。"
  };
}

/**
 * カスタムテンプレート使用でのクエリ生成
 * 注意: dmlGenerator削除により機能停止中
 */
export async function generateQueriesWithCustomTemplate(
  entityDefinition: EntityDefinition,
  customTemplate: string,
  outputPath?: string
): Promise<QueryResult<string>> {
  return {
    success: false,
    error: "dmlGenerator削除により機能停止中です。代替実装が必要です。"
  };
}

/**
 * 【重要】代替実装に関する注意
 * 
 * dmlGenerator.tsの削除により、以下の機能が一時停止しています：
 * 
 * 1. エンティティ定義からのDMLクエリ自動生成
 * 2. テンプレート適用によるクエリ生成
 * 3. JSON設定ファイルからの一括クエリ生成
 * 
 * 代替案：
 * - templateScanner.tsとqueryService.tsの組み合わせ使用
 * - 手動でのcypherファイル作成
 * - Python版dml_generator.pyの使用（存在する場合）
 * 
 * これらの機能が必要な場合は、規約準拠版の新しい実装を作成してください。
 */
