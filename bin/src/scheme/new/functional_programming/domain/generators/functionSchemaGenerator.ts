/**
 * functionSchemaGenerator.ts
 * 
 * 関数型スキーマジェネレーターの実装
 * SchemaGenerator インターフェースに基づいた関数メタスキーマ生成
 */

import { 
  SchemaGenerator, 
  SchemaGeneratorOptions, 
  SchemaTypeKind 
} from './schemaGenerator.ts';
import { generateCompleteSchema } from '../../application/schemaBuilderServiceImpl.ts';
import { FunctionFeatures } from '../features/index.ts';

/**
 * 関数型スキーマのジェネレーター固有オプション
 */
export interface FunctionSchemaGeneratorOptions extends SchemaGeneratorOptions {
  /**
   * 関数の特性設定
   */
  features?: FunctionFeatures;
}

/**
 * 関数型スキーマのメタデータ型
 */
export interface FunctionSchemaMetadata {
  /**
   * シグネチャ定義
   */
  signatures?: Record<string, unknown>[];
  
  /**
   * 外部依存関係
   */
  externalDependencies?: Record<string, unknown>[];
  
  /**
   * 例外情報
   */
  thrownExceptions?: Record<string, unknown>[];
  
  /**
   * 使用例
   */
  usageExamples?: Record<string, unknown>[];
  
  /**
   * テスト仕様
   */
  tests?: Record<string, unknown>;
  
  /**
   * 非推奨情報
   */
  deprecated?: boolean;
  deprecationMessage?: string;
  
  /**
   * 関数合成情報
   */
  composition?: Record<string, unknown>;
  
  /**
   * 実装リソースURI
   */
  resourceUri?: string;
}

/**
 * 関数型スキーマジェネレーターの実装
 */
export class FunctionSchemaGenerator implements SchemaGenerator<FunctionSchemaMetadata, FunctionSchemaGeneratorOptions> {
  readonly typeKind: SchemaTypeKind = SchemaTypeKind.FUNCTION;
  readonly description: string = '関数型メタスキーマを生成するジェネレーター';
  
  /**
   * スキーマを生成する
   * 
   * @param options 生成オプション
   * @param metadata 追加メタデータ
   * @returns 生成されたスキーマ
   */
  generate(
    options: FunctionSchemaGeneratorOptions, 
    metadata?: FunctionSchemaMetadata
  ): Record<string, unknown> {
    // 既存のスキーマ生成サービスを活用
    const schema = generateCompleteSchema(
      options.title,
      options.description,
      options.features,
      metadata?.resourceUri || options.resourceUri
    );
    
    // メタデータの追加処理（必要に応じて）
    if (metadata) {
      const result = { ...schema } as Record<string, unknown>;
      
      // メタデータの各フィールドをスキーマに反映
      // ここでは任意のフィールドを上書きするだけの単純な実装
      // 実際の実装ではより複雑な統合ロジックが必要かもしれない
      if (metadata.signatures && metadata.signatures.length > 0) {
        result.signatures = metadata.signatures;
      }
      
      if (metadata.externalDependencies) {
        result.externalDependencies = metadata.externalDependencies;
      }
      
      if (metadata.thrownExceptions) {
        result.thrownExceptions = metadata.thrownExceptions;
      }
      
      if (metadata.usageExamples) {
        result.usageExamples = metadata.usageExamples;
      }
      
      if (metadata.tests) {
        result.tests = metadata.tests;
      }
      
      if (metadata.deprecated !== undefined) {
        result.deprecated = metadata.deprecated;
        if (metadata.deprecationMessage) {
          result.deprecationMessage = metadata.deprecationMessage;
        }
      }
      
      if (metadata.composition) {
        result.composition = metadata.composition;
      }
      
      return result;
    }
    
    // 変換: FunctionSchema → Record<string, unknown>
    return schema as unknown as Record<string, unknown>;
  }
  
  /**
   * スキーマに必要なプロパティをバリデーションする
   * 
   * @param metadata バリデーション対象のメタデータ
   * @returns バリデーション結果とエラーメッセージ
   */
  validate(metadata: FunctionSchemaMetadata): { valid: boolean; errors?: string[] } {
    const errors: string[] = [];
    
    // 必須フィールドのバリデーション
    // 実際のシステムではより詳細なバリデーションが必要
    if (metadata.signatures === undefined || metadata.signatures.length === 0) {
      errors.push('関数シグネチャが定義されていません');
    }
    
    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined
    };
  }
}

/**
 * 関数型スキーマジェネレーターのファクトリ関数
 * 
 * @returns 新しい関数型スキーマジェネレーターインスタンス
 */
export function createFunctionSchemaGenerator(): SchemaGenerator<FunctionSchemaMetadata, FunctionSchemaGeneratorOptions> {
  return new FunctionSchemaGenerator();
}
