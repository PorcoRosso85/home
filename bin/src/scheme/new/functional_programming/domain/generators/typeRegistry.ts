/**
 * typeRegistry.ts
 * 
 * 型レジストリの実装
 * 利用可能な型ジェネレーターを管理する
 */

import { SchemaGenerator, TypeRegistry, TypeRegistryEntry, SchemaTypeKind } from './schemaGenerator.ts';

/**
 * 型レジストリの実装クラス
 * スキーマ生成器の登録と検索を提供する
 */
export class TypeRegistryImpl implements TypeRegistry {
  private registry: Map<string, SchemaGenerator> = new Map();
  
  /**
   * 型ジェネレーターを登録する
   * 
   * @param entry 型レジストリエントリ
   */
  register<T, O>(entry: TypeRegistryEntry<T, O>): void {
    if (this.registry.has(entry.name)) {
      throw new Error(`型 '${entry.name}' は既に登録されています`);
    }
    
    this.registry.set(entry.name, entry.generator);
  }
  
  /**
   * 名前で型ジェネレーターを取得する
   * 
   * @param name 型名
   * @returns 型ジェネレーター、存在しない場合はnull
   */
  getGenerator(name: string): SchemaGenerator | null {
    return this.registry.get(name) || null;
  }
  
  /**
   * 種別で型ジェネレーターを取得する
   * 
   * @param kind 型種別
   * @returns 指定された種別の型ジェネレーターの配列
   */
  getGeneratorsByKind(kind: SchemaTypeKind): SchemaGenerator[] {
    return Array.from(this.registry.values())
      .filter(generator => generator.typeKind === kind);
  }
  
  /**
   * すべての登録済み型ジェネレーターを取得する
   * 
   * @returns 登録済みの型ジェネレーターの配列
   */
  getAllGenerators(): SchemaGenerator[] {
    return Array.from(this.registry.values());
  }
}

/**
 * 型レジストリのシングルトンインスタンスを作成するファクトリ関数
 * 
 * @returns 型レジストリのシングルトンインスタンス
 */
export function createTypeRegistry(): TypeRegistry {
  return new TypeRegistryImpl();
}

// シングルトンインスタンス
const typeRegistryInstance = createTypeRegistry();

/**
 * シングルトン型レジストリインスタンスを取得する
 * 
 * @returns 型レジストリのシングルトンインスタンス
 */
export function getTypeRegistry(): TypeRegistry {
  return typeRegistryInstance;
}
