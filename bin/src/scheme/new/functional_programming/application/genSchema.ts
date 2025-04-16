/**
 * genSchema.ts
 * 
 * スキーマ生成アプリケーションサービス
 * このファイルは関数型アプローチに基づいたアプリケーション層の実装です
 */

import * as path from 'node:path';
import { SchemaGeneratorConfig } from '../interface/cliArgParser.ts';
import { generateCompleteSchema } from './schemaBuilderServiceImpl.ts';
import { SchemaRepository } from '../domain/schemaRepository.ts';
import { createSchemaRepository } from '../infrastructure/repositoryFactory.ts';
import { FunctionFeatures } from '../domain/features/index.ts';
import { FunctionSchema } from '../domain/schema.ts';

/**
 * スキーマ生成操作の結果
 */
export interface SchemaGenerationResult {
  success: boolean;
  message: string;
  schema?: FunctionSchema;
  outputPath?: string | null;
}

/**
 * 設定に基づいて機能特性オブジェクトを構築する
 * 
 * @param config スキーマ生成設定
 * @returns 機能特性オブジェクト
 */
export function buildFeaturesFromConfig(config: SchemaGeneratorConfig): FunctionFeatures {
  const features: FunctionFeatures = {};
  
  if (config.enableFeatures.purity) {
    features.purity = { isPure: true };
  }
  
  if (config.enableFeatures.evaluation) {
    features.evaluation = { isLazy: false };
  }
  
  if (config.enableFeatures.currying) {
    features.currying = { isCurried: false };
  }
  
  if (config.enableFeatures.recursion) {
    features.recursion = { isRecursive: false };
  }
  
  if (config.enableFeatures.memoization) {
    features.memoization = { supportsMemoization: false };
  }
  
  if (config.enableFeatures.async) {
    features.async = { isAsync: false };
  }
  
  if (config.enableFeatures.multipleReturns) {
    features.multipleReturns = { multipleReturnValues: false };
  }
  
  if (config.enableFeatures.composition) {
    features.composition = {
      composable: true,
      compositionPatterns: ["pipeline", "pointfree"],
      dataFlow: {
        inputTransformations: [],
        outputAdaptations: []
      },
      optimizationHints: {
        fusable: true,
        parallelizable: true,
        memoizable: true
      }
    };
  }
  
  // FIXME: 下記の型システム機能と依存型の詳細定義は本実装時に最新の機能定義に合わせて更新が必要
  // - Function.meta.jsonの最新定義に従った型システム構造体を生成する
  // - 特に依存型プロパティの完全サポートを追加する
  // - また、applicationとdomain層に実装が分散しているため統合が必要


  // 型システムの特性（常に追加）
  features.typeSystem = {
    kind: 'static',
    algebraicDataTypes: {
      sumTypes: {
        supported: true,
        representation: 'tagged-union'
      },
      productTypes: {
        supported: true,
        representation: 'record'
      },
      patternMatching: {
        supported: true,
        exhaustivenessChecking: true
      }
    },
    generics: {
      supported: true,
      typeParameters: {
        variance: 'invariant',
        constraints: {
          supported: true,
          constraintMechanisms: ['subtyping', 'interfaces']
        }
      },
      higherKindedTypes: {
        supported: false
      }
    },
    typeInference: {
      supported: true,
      algorithm: 'Hindley-Milner',
      completeness: 'partial'
    },
    // 依存型の設定
    dependentTypes: {
      supported: true,
      valueIndexing: {
        supported: true,
        allowedValueTypes: ['constant', 'parameter']
      },
      refinementTypes: {
        supported: true,
        staticVerification: true,
        dynamicVerification: true
      },
      typeLevelComputation: {
        supported: true,
        recursion: true,
        typeFunctions: {
          supported: true,
          higherOrder: true
        },
        conditionals: {
          supported: true,
          ifThenElse: true,
          patternMatching: true
        }
      },
      singletonTypes: {
        supported: true,
        literalTypes: ['number', 'string', 'boolean']
      }
    }
  };
  
  // テスト情報の追加（常に追加）
  features.tests = {
    requiresTests: true,
    testCaseGeneration: {
      essentialHappyPath: {
        description: "基本的な正常系テストケース",
        motivation: "基本的な機能が期待通りに動作することを確認するため"
      }
    },
    testability: {
      mockability: {
        score: 8,
        description: "依存関係が明示的で、純粋関数のためモック化が容易"
      }
    }
  };
  
  return features;
}

/**
 * スキーマを生成して、必要に応じてリポジトリに保存する
 * 
 * @param schema 生成されたスキーマ
 * @param outputPath 出力パス
 * @param repository スキーマリポジトリ
 * @returns 生成結果
 */
export async function handleSchemaOutput(
  schema: FunctionSchema, 
  outputPath: string,
  repository: SchemaRepository
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
    const key = outputPath; // キーとしてファイルパスを使用
    console.log(`リポジトリ種別: ${repository.constructor.name}`);
    console.log(`スキーマの保存を開始します...`);
    await repository.save(schema, key);
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
 * スキーマから指定されたプロパティを削除する
 * 
 * @param schema スキーマオブジェクト
 * @param skipProperties スキップするプロパティの配列
 * @returns 処理済みのスキーマオブジェクト
 */
export function removeSkippedProperties(
  schema: FunctionSchema,
  skipProperties: string[]
): FunctionSchema {
  if (!skipProperties || skipProperties.length === 0) {
    return schema;
  }
  
  // スキーマのコピーを作成
  const modifiedSchema = JSON.parse(JSON.stringify(schema)) as FunctionSchema;
  
  // プロパティの削除処理
  if (modifiedSchema.properties) {
    const props = modifiedSchema.properties;
    
    skipProperties.forEach(propName => {
      // トップレベルプロパティのチェック (例: tests)
      if (props[propName]) {
        delete props[propName];
        console.log(`トップレベルプロパティ '${propName}' をスキップしました。`);
        
        // プロパティがrequiredリストにある場合、そこからも削除
        if (modifiedSchema.required) {
          const requiredIndex = modifiedSchema.required.indexOf(propName);
          if (requiredIndex !== -1) {
            modifiedSchema.required.splice(requiredIndex, 1);
          }
        }
      } 
      // featuresプロパティ内のチェック (例: typeSystem)
      else if (props.features && props.features.properties && 
               props.features.properties[propName]) {
        delete props.features.properties[propName];
        console.log(`features内プロパティ '${propName}' をスキップしました。`);
        
        // プロパティがrequiredリストにある場合、そこからも削除
        if (props.features.required) {
          const requiredIndex = props.features.required.indexOf(propName);
          if (requiredIndex !== -1) {
            props.features.required.splice(requiredIndex, 1);
          }
        }
      } else {
        console.log(`警告: プロパティ '${propName}' は見つかりませんでした。`);
      }
    });
  }
  
  return modifiedSchema;
}

/**
 * 設定からスキーマを生成する
 * 
 * @param config スキーマ生成設定
 * @param outputPath 出力先ファイルパス（省略時はconfig.outputPathを使用）
 * @param repository スキーマリポジトリ（省略時はデフォルトのリポジトリを使用）
 * @returns 生成結果
 */
export async function generateSchema(
  config: SchemaGeneratorConfig,
  outputPath?: string,
  repository?: SchemaRepository
): Promise<SchemaGenerationResult> {
  try {
    // 機能設定を構築
    const features = buildFeaturesFromConfig(config);
    
    // スキーマを生成（resourceUriパラメータを追加）
    let schema = generateCompleteSchema(
      config.title,
      config.description,
      features,
      config.resourceUri // 新しいconfigフィールド
    );
    
    // スキップするプロパティがある場合は削除
    if (config.skipProperties && config.skipProperties.length > 0) {
      schema = removeSkippedProperties(schema, config.skipProperties);
    }
    
    // リポジトリがない場合はデフォルトのリポジトリを使用
    const schemaRepo = repository || createSchemaRepository();
    
    // 出力処理（outputPathが指定されていない場合はconfig.outputPathを使用）
    const finalOutputPath = outputPath || config.outputPath;
    return await handleSchemaOutput(schema, finalOutputPath, schemaRepo);
  } catch (error) {
    return { 
      success: false, 
      message: `エラーが発生しました: ${error instanceof Error ? error.message : '不明なエラー'}` 
    };
  }
}

/**
 * 既存コードとの互換性のためのオブジェクトエクスポート
 */
export const schemaGenerationService = {
  generateSchema
};