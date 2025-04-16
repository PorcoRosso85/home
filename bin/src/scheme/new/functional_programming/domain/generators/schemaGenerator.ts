/**
 * schemaGenerator.ts
 * 
 * スキーマジェネレーターの共通インターフェース
 * 異なる型のスキーマ生成器のための基本契約を定義
 */

/**
 * 生成対象の型種別
 */
export enum SchemaTypeKind {
  FUNCTION = 'function',
  STRUCT = 'struct',
  LIST = 'list',
  ENUM = 'enum',
  UNION = 'union',
  PRIMITIVE = 'primitive',
}

/**
 * 基本的なスキーマ生成オプション
 */
export interface SchemaGeneratorOptions {
  title?: string;
  description?: string;
  version?: string;
  resourceUri?: string;
  additionalProperties?: Record<string, unknown>;
}

/**
 * スキーマジェネレーターの共通インターフェース
 * 異なる型のメタスキーマ生成器が実装する統一インターフェース
 */
export interface SchemaGenerator<T = unknown, O extends SchemaGeneratorOptions = SchemaGeneratorOptions> {
  /**
   * ジェネレーターの型種別を取得
   */
  readonly typeKind: SchemaTypeKind;
  
  /**
   * ジェネレーターの説明を取得
   */
  readonly description: string;
  
  /**
   * スキーマを生成する
   * 
   * @param options 生成オプション
   * @param metadata 追加メタデータ（型特有の設定）
   * @returns 生成されたスキーマ
   */
  generate(options: O, metadata?: T): Record<string, unknown>;
  
  /**
   * スキーマに必要なプロパティをバリデーションする
   * 
   * @param metadata バリデーション対象のメタデータ
   * @returns バリデーション結果（true: 有効, false: 無効）とエラーメッセージ
   */
  validate(metadata: T): { valid: boolean; errors?: string[] };
}

/**
 * 型レジストリエントリ
 * 型名とジェネレーターのマッピング
 */
export interface TypeRegistryEntry<T = unknown, O extends SchemaGeneratorOptions = SchemaGeneratorOptions> {
  name: string;
  generator: SchemaGenerator<T, O>;
}

/**
 * 型レジストリ
 * 利用可能なすべての型ジェネレーターを管理する
 */
export interface TypeRegistry {
  /**
   * 型ジェネレーターを登録する
   * 
   * @param entry 型レジストリエントリ
   */
  register<T, O extends SchemaGeneratorOptions>(entry: TypeRegistryEntry<T, O>): void;
  
  /**
   * 名前で型ジェネレーターを取得する
   * 
   * @param name 型名
   * @returns 型ジェネレーター、存在しない場合はnull
   */
  getGenerator(name: string): SchemaGenerator | null;
  
  /**
   * 種別で型ジェネレーターを取得する
   * 
   * @param kind 型種別
   * @returns 指定された種別の型ジェネレーターの配列
   */
  getGeneratorsByKind(kind: SchemaTypeKind): SchemaGenerator[];
  
  /**
   * すべての登録済み型ジェネレーターを取得する
   * 
   * @returns 登録済みの型ジェネレーターの配列
   */
  getAllGenerators(): SchemaGenerator[];
}
