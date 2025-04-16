# 新しいメタ型スキーマの追加方法

このドキュメントでは、既存の関数型メタスキーマ生成システムに新しい型（構造体、リスト等）のメタスキーマを追加する方法について詳細に説明します。

## 1. アーキテクチャの概要

現在のシステムは以下のアーキテクチャに基づいています：

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  インターフェース  │      │  アプリケーション  │      │     ドメイン     │
│    CLI / API     │─────▶│    サービス      │─────▶│    生成器       │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                         │                        │
        │                         │                        │
        ▼                         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   ユーザー入力    │      │  スキーマ生成     │      │ ファクトリー    │
│   コマンド解析    │      │  オプション処理   │      │ 型レジストリ    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## 2. 主要コンポーネントと役割

### ドメイン層
* **schemaGenerator.ts** - 生成器の共通インターフェース
  - `SchemaGenerator` インターフェース: すべての型生成器が実装すべき共通契約
  - `SchemaTypeKind` 列挙型: 対応する型種別の定義（FUNCTION, STRUCT, LIST等）

* **typeRegistry.ts** - 型生成器の登録と管理
  - `TypeRegistry` インターフェース: 型生成器の登録・取得のための機能
  - `TypeRegistryImpl` クラス: 実際の型レジストリの実装

* **generatorFactory.ts** - 型に応じた生成器を取得するファクトリー
  - `getGeneratorByName()`: 型名から適切な生成器を取得
  - `getGeneratorsByKind()`: 型種別から適切な生成器を取得
  - 型固有の取得関数（例: `getFunctionGenerator()`）

* **functionSchemaGenerator.ts** - 関数型特化の生成器
  - `FunctionSchemaGenerator` クラス: 関数型メタスキーマの生成機能
  - `generate()`: 実際のスキーマ生成処理
  - `validate()`: メタデータの検証処理

### アプリケーション層
* **schemaGenerationService.ts** - 統合生成サービス
  - `generateSchemaByTypeName()`: 型名に基づくスキーマ生成
  - `generateSchemaByTypeKind()`: 型種別に基づくスキーマ生成
  - `generateFunctionSchema()`: 関数型特化のスキーマ生成

### インターフェース層
* **generateNew.ts** - CLI用の拡張生成コマンド
  - コマンドライン引数の解析
  - 型選択に基づく生成処理の振り分け

## 3. 新しい型の追加手順

以下に、新しいメタ型（例: 構造体、リスト）を追加するための詳細な手順を示します。

### ステップ1: 型固有の生成器を実装する

1. `domain/generators/` ディレクトリに新しいファイル（例: `structSchemaGenerator.ts`）を作成します。

```typescript
// structSchemaGenerator.ts の例
import { 
  SchemaGenerator, 
  SchemaGeneratorOptions, 
  SchemaTypeKind 
} from './schemaGenerator.ts';

/**
 * 構造体スキーマのジェネレーター固有オプション
 */
export interface StructSchemaGeneratorOptions extends SchemaGeneratorOptions {
  /**
   * 構造体の特性設定
   */
  structFeatures?: {
    immutable?: boolean;
    extensible?: boolean;
    // 他の構造体固有の特性
  };
}

/**
 * 構造体スキーマのメタデータ型
 */
export interface StructSchemaMetadata {
  /**
   * フィールド定義
   */
  fields?: Record<string, unknown>[];
  
  /**
   * 型制約
   */
  constraints?: Record<string, unknown>[];
  
  // 他のメタデータフィールド
}

/**
 * 構造体スキーマジェネレーターの実装
 */
export class StructSchemaGenerator implements SchemaGenerator<StructSchemaMetadata, StructSchemaGeneratorOptions> {
  readonly typeKind: SchemaTypeKind = SchemaTypeKind.STRUCT;
  readonly description: string = '構造体メタスキーマを生成するジェネレーター';
  
  /**
   * スキーマを生成する
   * 
   * @param options 生成オプション
   * @param metadata 追加メタデータ
   * @returns 生成されたスキーマ
   */
  generate(
    options: StructSchemaGeneratorOptions, 
    metadata?: StructSchemaMetadata
  ): Record<string, unknown> {
    // 構造体スキーマの基本構造を生成
    const schema: Record<string, unknown> = {
      $schema: "https://json-schema.org/draft/2020-12/schema",
      title: options.title || "Struct Metadata Schema",
      description: options.description || "構造体メタデータのスキーマ定義",
      type: "object",
      required: ["title", "type", "fields"],
      properties: {
        title: {
          type: "string",
          description: "構造体の名前"
        },
        description: {
          type: "string",
          description: "構造体の説明"
        },
        type: {
          type: "string",
          enum: ["struct"],
          description: "型のカテゴリ (構造体のため 'struct'固定)"
        },
        fields: {
          type: "array",
          description: "構造体のフィールド定義リスト",
          minItems: 1,
          items: {
            type: "object",
            required: ["name", "type"],
            properties: {
              name: {
                type: "string",
                description: "フィールド名"
              },
              type: {
                type: "string",
                description: "フィールドの型"
              },
              description: {
                type: "string",
                description: "フィールドの説明"
              },
              required: {
                type: "boolean",
                description: "必須フィールドかどうか",
                default: true
              }
            }
          }
        }
      }
    };
    
    // 構造体特性の追加（オプション）
    if (options.structFeatures) {
      const structFeaturesSchema: Record<string, unknown> = {
        type: "object",
        description: "構造体の特性",
        properties: {}
      };
      
      if (options.structFeatures.immutable !== undefined) {
        structFeaturesSchema.properties = {
          ...structFeaturesSchema.properties as Record<string, unknown>,
          immutable: {
            type: "boolean",
            description: "イミュータブルな構造体かどうか",
            default: options.structFeatures.immutable
          }
        };
      }
      
      if (options.structFeatures.extensible !== undefined) {
        structFeaturesSchema.properties = {
          ...structFeaturesSchema.properties as Record<string, unknown>,
          extensible: {
            type: "boolean",
            description: "拡張可能な構造体かどうか",
            default: options.structFeatures.extensible
          }
        };
      }
      
      // スキーマに特性を追加
      schema.properties = {
        ...schema.properties as Record<string, unknown>,
        features: structFeaturesSchema
      };
    }
    
    // メタデータの統合（存在する場合）
    if (metadata) {
      if (metadata.fields && metadata.fields.length > 0) {
        schema.properties = {
          ...schema.properties as Record<string, unknown>,
          fields: {
            ...schema.properties.fields as Record<string, unknown>,
            items: metadata.fields
          }
        };
      }
      
      if (metadata.constraints) {
        schema.properties = {
          ...schema.properties as Record<string, unknown>,
          constraints: {
            type: "array",
            description: "構造体の制約条件",
            items: {
              type: "object",
              properties: {
                type: {
                  type: "string",
                  description: "制約の種類"
                },
                description: {
                  type: "string",
                  description: "制約の説明"
                },
                condition: {
                  type: "string",
                  description: "制約の条件式"
                }
              }
            }
          }
        };
      }
    }
    
    return schema;
  }
  
  /**
   * スキーマに必要なプロパティをバリデーションする
   * 
   * @param metadata バリデーション対象のメタデータ
   * @returns バリデーション結果とエラーメッセージ
   */
  validate(metadata: StructSchemaMetadata): { valid: boolean; errors?: string[] } {
    const errors: string[] = [];
    
    // 必須フィールドのバリデーション
    if (!metadata.fields || metadata.fields.length === 0) {
      errors.push('構造体フィールドが定義されていません');
    }
    
    return {
      valid: errors.length === 0,
      errors: errors.length > 0 ? errors : undefined
    };
  }
}

/**
 * 構造体スキーマジェネレーターのファクトリ関数
 * 
 * @returns 新しい構造体スキーマジェネレーターインスタンス
 */
export function createStructSchemaGenerator(): SchemaGenerator<StructSchemaMetadata, StructSchemaGeneratorOptions> {
  return new StructSchemaGenerator();
}
```

### ステップ2: ジェネレーターファクトリーに新しい型を追加する

`domain/generators/generatorFactory.ts` を編集して、新しい型のジェネレーターを登録します：

```typescript
// generatorFactory.ts の追加部分

import { 
  createStructSchemaGenerator, 
  StructSchemaGenerator, 
  StructSchemaMetadata,
  StructSchemaGeneratorOptions 
} from './structSchemaGenerator.ts';

// ... 既存のコード ...

// 初期化関数に新しい型の登録を追加
function initializeGenerators() {
  if (generatorsInitialized) {
    return;
  }
  
  const registry = getTypeRegistry();
  
  // 関数型ジェネレーターを登録
  registry.register({
    name: 'function',
    generator: createFunctionSchemaGenerator()
  });
  
  // 構造体ジェネレーターを登録
  registry.register({
    name: 'struct',
    generator: createStructSchemaGenerator()
  });
  
  // ... 他の型の登録 ...
  
  generatorsInitialized = true;
}

// ... 既存のコード ...

/**
 * 構造体ジェネレーターを取得する
 * 
 * @returns 構造体ジェネレーター
 */
export function getStructGenerator(): SchemaGenerator<StructSchemaMetadata, StructSchemaGeneratorOptions> {
  initializeGenerators();
  const generator = getTypeRegistry().getGenerator('struct');
  if (!generator) {
    throw new Error('構造体ジェネレーターが見つかりません');
  }
  return generator as StructSchemaGenerator;
}

// 型をエクスポート
export type { StructSchemaMetadata, StructSchemaGeneratorOptions };
```

### ステップ3: アプリケーションサービスに新しい型向けの関数を追加する

`application/schemaGenerationService.ts` に新しい型用の便利関数を追加します：

```typescript
// schemaGenerationService.ts の追加部分

import {
  getStructGenerator,
  StructSchemaMetadata,
  StructSchemaGeneratorOptions,
} from '../domain/generators/index.ts';

// ... 既存のコード ...

/**
 * 構造体スキーマを生成する
 * 
 * @param options 構造体スキーマのオプション
 * @param metadata 構造体固有のメタデータ（オプション）
 * @returns 生成されたスキーマオブジェクト
 */
export function generateStructSchema(
  options: StructSchemaGeneratorOptions,
  metadata?: StructSchemaMetadata
): Record<string, unknown> {
  const generator = getStructGenerator();
  return generator.generate(options, metadata);
}

// サービスオブジェクトに新しい関数を追加
export const schemaGenerationService = {
  generateSchemaByTypeName,
  generateSchemaByTypeKind,
  generateFunctionSchema,
  generateStructSchema,  // 新しい関数を追加
  saveGeneratedSchema,
  removeSchemaProperties,
  generateAndSaveSchema
};
```

### ステップ4: インデックスファイルを更新する

`domain/generators/index.ts` を更新して、新しい型をエクスポートします：

```typescript
// index.ts の追加部分

// ... 既存のエクスポート ...

// ジェネレーターファクトリー
export {
  getGeneratorByName,
  getGeneratorsByKind,
  getAllGenerators,
  getFunctionGenerator,
  getStructGenerator,  // 新しい関数をエクスポート
  type FunctionSchemaMetadata,
  type FunctionSchemaGeneratorOptions,
  type StructSchemaMetadata,  // 新しい型をエクスポート
  type StructSchemaGeneratorOptions  // 新しい型をエクスポート
} from './generatorFactory.ts';

// 関数型スキーマジェネレーター
export {
  createFunctionSchemaGenerator
} from './functionSchemaGenerator.ts';

// 構造体スキーマジェネレーター
export {
  createStructSchemaGenerator
} from './structSchemaGenerator.ts';
```

### ステップ5: CLIコマンドを更新する（オプション）

必要に応じて、`interface/cli/generateNew.ts` に型固有の処理を追加することもできます：

```typescript
// generateNew.ts の追加部分

// ... 既存のコード ...

// 型に応じた処理部分を拡張
if (options.typeKind === SchemaTypeKind.FUNCTION) {
  // 関数型の処理（既存）
  // ...
} else if (options.typeKind === SchemaTypeKind.STRUCT) {
  // 構造体型の処理
  const structOptions: StructSchemaGeneratorOptions = {
    ...genOptions,
    structFeatures: {
      immutable: true,  // デフォルト値またはオプションから取得
      extensible: false  // デフォルト値またはオプションから取得
    }
  };
  
  // 構造体スキーマを生成
  let schema = schemaGenerationService.generateStructSchema(structOptions);
  
  // 以下は共通処理（スキップ、保存など）
  // ...
} else {
  // その他の型の処理（既存）
  // ...
}

// ... 既存のコード ...
```

## 4. リファクタリングのポイント

新しい型を追加する際に考慮すべきリファクタリングのポイント：

### 共通ロジックの抽出
- 各型の生成器に共通する処理は、基底クラスや共通ユーティリティに抽出することを検討
- 例: スキーマのベース部分生成、バリデーション共通ロジックなど

### 拡張性の向上
- 将来的な型の追加を容易にするため、依存関係を最小限に抑える
- 型固有の特性はそれぞれの生成器内にカプセル化する

### テスト
- 新しい型の生成器に対するユニットテストを追加
- スキーマ検証用のテストケースを充実させる

## 5. 使用例

新しい型が追加された後の使用例：

### コードでの使用
```typescript
import { schemaGenerationService } from './application/schemaGenerationService.ts';

// 関数型スキーマの生成
const functionSchema = schemaGenerationService.generateFunctionSchema({
  title: "MyFunction",
  description: "My custom function schema"
});

// 構造体スキーマの生成
const structSchema = schemaGenerationService.generateStructSchema({
  title: "MyStruct",
  description: "My custom struct schema",
  structFeatures: {
    immutable: true
  }
});

// スキーマの保存
await schemaGenerationService.saveGeneratedSchema(structSchema, './MyStruct__Meta.json');
```

### CLI経由での使用
```bash
# 関数型メタスキーマの生成
./interface/cli.ts generate-new --type function --output ./Function__Meta.json

# 構造体メタスキーマの生成
./interface/cli.ts generate-new --type struct --output ./Struct__Meta.json
```

## 6. 注意点

- 既存の機能を壊さないように慎重に実装する
- 型間の整合性を保つために命名規則を統一する
- リソースURIなどの共通項目をすべての型で一貫して扱う
- 型レジストリの初期化タイミングに注意する（遅延初期化を活用）

このドキュメントに従うことで、新しいメタ型を既存システムに効率的に追加することができます。
