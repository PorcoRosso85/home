/**
 * schemaBuilderServiceImpl.ts
 * 
 * スキーマビルダーサービスの実装
 * 関数型アプローチでの実装を提供します
 */

import { 
  FunctionSchema, 
  FunctionFeatures 
} from '../domain/schema.ts';
import { 
  createBaseSchema, 
  addPropertyToSchema, 
  addRequiredProperty 
} from '../domain/schemaCore.ts';
import { createSignaturesListSchema } from './schemas/signatureSchema.ts';
import { createFeaturesSchema } from './schemas/featureSchema.ts';
import { createExternalDependenciesSchema } from './schemas/externalDependenciesSchema.ts';
import { createThrownExceptionsSchema } from './schemas/thrownExceptionsSchema.ts';
import { createUsageExamplesSchema } from './schemas/usageExamplesSchema.ts';
import { createDeprecatedSchema, createDeprecationMessageSchema } from './schemas/deprecationSchema.ts';
import { createCompositionSchema } from './schemas/compositionSchema.ts';
import { createTestsSchema } from './schemas/testsSchema.ts';
import { createResourceUriSchema } from './schemas/resourceUriSchema.ts';
import { SCHEMA_DEFAULTS } from '../infrastructure/variables.ts';
import { collectReferences, collectExternalReferences } from './refCollector.ts';

/**
 * 関数型スキーマを完全に生成する
 * 
 * @param title スキーマのタイトル
 * @param description スキーマの説明
 * @param features 関数の特性
 * @param resourceUri 実装リソースURI（オプション）
 * @returns 生成されたスキーマ
 */
/**
 * FIXME: スキーマ生成に関する実装は以下の2つの課題について対応が必要
 * 1. src配下のクラスベース実装(GenerationServiceImpl)との互換性を考慮する
 *   - src/domain/generationService.ts の関数生成部分を関数型に置き換え
 *   - 参照変換機能を統合するか、別の純粋関数として実装するか検討
 * 2. スキーマ生成を純粋関数として整理
 *   - 現状、副作用のある操作とスキーマ生成処理が結合している箇所がある
 *   - ファイル操作などの副作用を分離し、スキーマ生成のみを行う純粋関数に再実装
 */


export function generateCompleteSchema(
  title: string = SCHEMA_DEFAULTS.TITLE,
  description: string = SCHEMA_DEFAULTS.DESCRIPTION,
  features: FunctionFeatures = {},
  resourceUri?: string
): FunctionSchema {
  // 基本スキーマを作成
  let schema = createBaseSchema(title, description);
  
  // シグネチャを追加
  schema = addPropertyToSchema(schema, 'signatures', createSignaturesListSchema());
  
  // 機能特性を追加（指定されている場合）
  if (Object.keys(features).length > 0) {
    schema = addPropertyToSchema(schema, 'features', createFeaturesSchema(features));
  }
  
  // リソースURIを常に追加する（TODOで指摘された修正）
  schema = addPropertyToSchema(schema, 'resourceUri', createResourceUriSchema());
  
  // 外部依存関係を追加
  schema = addPropertyToSchema(schema, 'externalDependencies', createExternalDependenciesSchema());
  
  // 例外情報を追加
  schema = addPropertyToSchema(schema, 'thrownExceptions', createThrownExceptionsSchema());
  
  // 使用例を追加
  schema = addPropertyToSchema(schema, 'usageExamples', createUsageExamplesSchema());
  
  // 非推奨情報を追加
  schema = addPropertyToSchema(schema, 'deprecated', createDeprecatedSchema());
  schema = addPropertyToSchema(schema, 'deprecationMessage', createDeprecationMessageSchema());
  
  // 関数合成情報を追加
  if (features.composition) {
    schema = addPropertyToSchema(schema, 'composition', createCompositionSchema());
  }

  // テスト情報を追加
  if (features.tests) {
    schema = addPropertyToSchema(schema, 'tests', createTestsSchema(features.tests));
  } else {
    // デフォルトのテスト情報を追加（必須フラグがfalseのみ）
    schema = addPropertyToSchema(schema, 'tests', createTestsSchema());
  }
  
  return schema;
}

/**
 * 生成されたスキーマから参照情報を収集する
 * 
 * @param schema FunctionSchema オブジェクト
 * @returns 収集された$ref参照のリスト
 */
export function getSchemaReferences(schema: FunctionSchema): string[] {
  return collectReferences(schema);
}

/**
 * 生成されたスキーマから外部参照のみを収集する
 * 
 * @param schema FunctionSchema オブジェクト
 * @returns 外部$ref参照のリスト
 */
export function getExternalReferences(schema: FunctionSchema): string[] {
  return collectExternalReferences(schema);
}

/**
 * スキーマビルダーサービスの関数をオブジェクトとしてエクスポート
 * （既存コードとの互換性のため）
 */
export const schemaBuilderService = {
  // domain層からの関数をそのまま再エクスポート
  createBaseSchema,
  addPropertyToSchema,
  addRequiredProperty,
  generateCompleteSchema,
  
  // 新しい参照収集関数
  getSchemaReferences,
  getExternalReferences
};
