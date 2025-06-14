/**
 * index.ts
 * 
 * スキーマジェネレーターモジュールのインデックスファイル
 * 外部からの利用に必要なすべてのエクスポートを提供
 */

// スキーマジェネレーターの基本インターフェース
export {
  SchemaTypeKind,
  type SchemaGenerator,
  type SchemaGeneratorOptions,
  type TypeRegistry,
  type TypeRegistryEntry
} from './schemaGenerator.ts';

// 型レジストリ
export {
  createTypeRegistry,
  getTypeRegistry
} from './typeRegistry.ts';

// ジェネレーターファクトリ
export {
  getGeneratorByName,
  getGeneratorsByKind,
  getAllGenerators,
  getFunctionGenerator,
  type FunctionSchemaMetadata,
  type FunctionSchemaGeneratorOptions
} from './generatorFactory.ts';

// 関数型スキーマジェネレーター
export {
  createFunctionSchemaGenerator
} from './functionSchemaGenerator.ts';
