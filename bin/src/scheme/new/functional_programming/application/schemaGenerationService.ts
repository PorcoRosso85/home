/**
 * schemaGenerationService.ts
 * 
 * スキーマ生成サービス
 * 型に依存しない汎用的なスキーマ生成機能を提供
 */

import { SchemaRepository } from '../domain/schemaRepository.ts';
import { createSchemaRepository } from '../infrastructure/repositoryFactory.ts';
import {
  SchemaTypeKind,
  SchemaGeneratorOptions,
  getGeneratorByName,
  getGeneratorsByKind,
  getFunctionGenerator,
  FunctionSchemaMetadata,
  FunctionSchemaGeneratorOptions,
} from '../domain/generators/index.ts';

/**
 * スキーマ生成結果の型定義
 */
export interface SchemaGenerationResult {
  success: boolean;
  message: string;
  schema?: Record<string, unknown>;
  outputPath?: string | null;
}

/**
 * 型名からスキーマを生成する
 * 
 * @param typeName 型名
 * @param options 生成オプション
 * @param metadata 型固有のメタデータ（オプション）
 * @returns 生成されたスキーマオブジェクト
 * @throws 型名が見つからない場合はエラー
 */
export function generateSchemaByTypeName(
  typeName: string,
  options: SchemaGeneratorOptions,
  metadata?: unknown
): Record<string, unknown> {
  const generator = getGeneratorByName(typeName);
  
  if (!generator) {
    throw new Error(`型名 '${typeName}' に対応するジェネレーターが見つかりません`);
  }
  
  return generator.generate(options, metadata);
}

/**
 * 型種別からスキーマを生成する
 * 
 * @param typeKind 型種別
 * @param options 生成オプション
 * @param metadata 型固有のメタデータ（オプション）
 * @returns 生成されたスキーマオブジェクト
 * @throws 型種別が見つからない場合はエラー
 */
export function generateSchemaByTypeKind(
  typeKind: SchemaTypeKind,
  options: SchemaGeneratorOptions,
  metadata?: unknown
): Record<string, unknown> {
  const generators = getGeneratorsByKind(typeKind);
  
  if (generators.length === 0) {
    throw new Error(`型種別 '${typeKind}' に対応するジェネレーターが見つかりません`);
  }
  
  // デフォルトでは最初のジェネレーターを使用
  return generators[0].generate(options, metadata);
}

/**
 * 関数型スキーマを生成する
 * 
 * @param options 関数型スキーマのオプション
 * @param metadata 関数固有のメタデータ（オプション）
 * @returns 生成されたスキーマオブジェクト
 */
export function generateFunctionSchema(
  options: FunctionSchemaGeneratorOptions,
  metadata?: FunctionSchemaMetadata
): Record<string, unknown> {
  const generator = getFunctionGenerator();
  return generator.generate(options, metadata);
}

/**
 * スキーマを生成してリポジトリに保存する
 * 
 * @param schema 生成されたスキーマ
 * @param outputPath 出力パス
 * @param repository スキーマリポジトリ
 * @returns 生成結果
 */
export async function saveGeneratedSchema(
  schema: Record<string, unknown>,
  outputPath: string,
  repository?: SchemaRepository
): Promise<SchemaGenerationResult> {
  if (!outputPath) {
    console.warn('警告: 出力パスが指定されていません。スキーマはファイルに保存されません。');
    return { 
      success: true, 
      message: 'スキーマが正常に生成されましたが、保存されていません',
      schema,
      outputPath: null
    };
  }

  try {
    // リポジトリがない場合はデフォルトのリポジトリを使用
    const schemaRepo = repository || createSchemaRepository();
    
    const key = outputPath; // キーとしてファイルパスを使用
    console.log(`リポジトリ種別: ${schemaRepo.constructor.name}`);
    console.log(`スキーマの保存を開始します...`);
    
    // スキーマオブジェクトをリポジトリに保存
    // 型安全性のためにanyを使用
    await schemaRepo.save(schema as any, key);
    
    console.log(`スキーマをリポジトリに保存しました: ${key}`);
    
    return { 
      success: true, 
      message: `スキーマが正常に生成されました: ${outputPath}`,
      schema,
      outputPath
    };
  } catch (error) {
    console.error(`スキーマの保存中にエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`);
    return {
      success: false,
      message: `スキーマは生成されましたが、保存に失敗しました: ${error instanceof Error ? error.message : String(error)}`,
      schema,
      outputPath
    };
  }
}

/**
 * スキーマのプロパティを削除する
 * 
 * @param schema スキーマオブジェクト
 * @param skipProperties スキップするプロパティの配列
 * @returns 処理済みのスキーマオブジェクト
 */
export function removeSchemaProperties(
  schema: Record<string, unknown>,
  skipProperties: string[]
): Record<string, unknown> {
  if (!skipProperties || skipProperties.length === 0) {
    return schema;
  }
  
  // スキーマのコピーを作成
  const modifiedSchema = JSON.parse(JSON.stringify(schema));
  
  // プロパティの削除処理
  skipProperties.forEach(propName => {
    // トップレベルプロパティのチェック
    if (propName in modifiedSchema) {
      delete modifiedSchema[propName];
      console.log(`トップレベルプロパティ '${propName}' をスキップしました。`);
      
      // プロパティがrequiredリストにある場合、そこからも削除
      if (modifiedSchema.required && Array.isArray(modifiedSchema.required)) {
        const requiredIndex = modifiedSchema.required.indexOf(propName);
        if (requiredIndex !== -1) {
          modifiedSchema.required.splice(requiredIndex, 1);
        }
      }
    } 
    // 特定の子プロパティのチェック
    else if (modifiedSchema.properties && typeof modifiedSchema.properties === 'object') {
      // featuresプロパティ内のチェック
      if (modifiedSchema.properties.features && 
          modifiedSchema.properties.features.properties && 
          propName in modifiedSchema.properties.features.properties) {
          
        delete modifiedSchema.properties.features.properties[propName];
        console.log(`features内プロパティ '${propName}' をスキップしました。`);
        
        // フィーチャーのrequiredリストからも削除
        if (modifiedSchema.properties.features.required && 
            Array.isArray(modifiedSchema.properties.features.required)) {
          const requiredIndex = modifiedSchema.properties.features.required.indexOf(propName);
          if (requiredIndex !== -1) {
            modifiedSchema.properties.features.required.splice(requiredIndex, 1);
          }
        }
      } else {
        console.log(`警告: プロパティ '${propName}' は見つかりませんでした。`);
      }
    }
  });
  
  return modifiedSchema;
}

/**
 * 完全なスキーマ生成プロセスを実行する
 * 生成、プロパティ削除、保存を一連の流れで行う
 * 
 * @param typeName 型名
 * @param options 生成オプション
 * @param metadata 型固有のメタデータ（オプション）
 * @param skipProperties スキップするプロパティの配列（オプション）
 * @param outputPath 出力パス
 * @param repository スキーマリポジトリ（オプション）
 * @returns 生成結果
 */
export async function generateAndSaveSchema(
  typeName: string,
  options: SchemaGeneratorOptions,
  metadata?: unknown,
  skipProperties?: string[],
  outputPath?: string,
  repository?: SchemaRepository
): Promise<SchemaGenerationResult> {
  try {
    // スキーマの生成
    let schema = generateSchemaByTypeName(typeName, options, metadata);
    
    // スキップするプロパティがある場合は削除
    if (skipProperties && skipProperties.length > 0) {
      schema = removeSchemaProperties(schema, skipProperties);
    }
    
    // 出力パスが指定されている場合は保存
    if (outputPath) {
      return await saveGeneratedSchema(schema, outputPath, repository);
    } else {
      return {
        success: true, 
        message: 'スキーマが正常に生成されましたが、出力パスが指定されていないため保存されていません',
        schema
      };
    }
  } catch (error) {
    return { 
      success: false, 
      message: `エラーが発生しました: ${error instanceof Error ? error.message : '不明なエラー'}` 
    };
  }
}

/**
 * 一般的なサービスインターフェース
 * 外部からの利用のためにエクスポート
 */
export const schemaGenerationService = {
  generateSchemaByTypeName,
  generateSchemaByTypeKind,
  generateFunctionSchema,
  saveGeneratedSchema,
  removeSchemaProperties,
  generateAndSaveSchema
};
