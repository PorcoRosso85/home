/**
 * generatorFactory.ts
 * 
 * スキーマジェネレーターのファクトリ
 * 型に応じた適切なジェネレーターを取得する
 */

import { SchemaGenerator, SchemaTypeKind } from './schemaGenerator.ts';
import { getTypeRegistry } from './typeRegistry.ts';
import { 
  createFunctionSchemaGenerator, 
  FunctionSchemaGenerator, 
  FunctionSchemaMetadata,
  FunctionSchemaGeneratorOptions 
} from './functionSchemaGenerator.ts';

/**
 * 型ジェネレーター初期化フラグ
 */
let generatorsInitialized = false;

/**
 * ジェネレーターを初期化し、レジストリに登録する
 */
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
  
  // FIXME: 将来的に他の型（構造体、リスト、列挙型など）のジェネレーターを追加

  generatorsInitialized = true;
}

/**
 * 型名で適切なジェネレーターを取得する
 * 
 * @param typeName 型名
 * @returns 型に対応するジェネレーター、存在しない場合はnull
 */
export function getGeneratorByName(typeName: string): SchemaGenerator | null {
  initializeGenerators();
  return getTypeRegistry().getGenerator(typeName);
}

/**
 * 型種別で適切なジェネレーターを取得する
 * 
 * @param typeKind 型種別
 * @returns 型種別に対応するジェネレーターの配列
 */
export function getGeneratorsByKind(typeKind: SchemaTypeKind): SchemaGenerator[] {
  initializeGenerators();
  return getTypeRegistry().getGeneratorsByKind(typeKind);
}

/**
 * 登録済みのすべてのジェネレーターを取得する
 * 
 * @returns すべてのジェネレーターの配列
 */
export function getAllGenerators(): SchemaGenerator[] {
  initializeGenerators();
  return getTypeRegistry().getAllGenerators();
}

/**
 * 型固有のジェネレーターを取得するショートカット関数
 */

/**
 * 関数型ジェネレーターを取得する
 * 
 * @returns 関数型ジェネレーター
 */
export function getFunctionGenerator(): SchemaGenerator<FunctionSchemaMetadata, FunctionSchemaGeneratorOptions> {
  initializeGenerators();
  const generator = getTypeRegistry().getGenerator('function');
  if (!generator) {
    throw new Error('関数型ジェネレーターが見つかりません');
  }
  return generator as FunctionSchemaGenerator;
}

// 型をエクスポート
export type { FunctionSchemaMetadata, FunctionSchemaGeneratorOptions };
