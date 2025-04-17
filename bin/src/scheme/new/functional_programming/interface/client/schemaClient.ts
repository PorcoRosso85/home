/**
 * schemaClient.ts
 * 
 * スキーマ操作の共通処理
 * CLI、ブラウザ両方で使用するスキーマ関連機能
 */

import { FunctionSchema } from '../../domain/schema.ts';
import { Graph } from '../../domain/entities/graph.ts';

/**
 * スキーマデータアクセスインターフェース
 * 異なる実装（ファイル、API）の抽象化
 */
export interface SchemaDataAccess {
  /** スキーマのロード */
  loadSchema(path: string): Promise<FunctionSchema>;
  
  /** スキーマの保存 */
  saveSchema(schema: FunctionSchema, path: string): Promise<void>;
  
  /** 依存関係グラフの取得 */
  getDependencyGraph(rootSchemaPath: string): Promise<Graph>;
  
  /** スキーマの検証 */
  validateSchema(schema: FunctionSchema): Promise<boolean>;
  
  /** スキーマリストの取得 */
  getSchemaList(): Promise<string[]>;
}

/**
 * JSON文字列からFunctionSchemaオブジェクトへの変換
 * 
 * @param json JSON文字列
 * @returns FunctionSchema オブジェクト
 */
export function parseSchemaJson(json: string): FunctionSchema {
  try {
    return JSON.parse(json) as FunctionSchema;
  } catch (error) {
    throw new Error(`スキーマJSONの解析に失敗しました: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * スキーマオブジェクトからJSON文字列への変換
 * 
 * @param schema FunctionSchema オブジェクト
 * @param pretty 整形フラグ。trueの場合、インデントされたJSONを返す
 * @returns JSON文字列
 */
export function stringifySchema(schema: FunctionSchema, pretty = true): string {
  try {
    return pretty ? JSON.stringify(schema, null, 2) : JSON.stringify(schema);
  } catch (error) {
    throw new Error(`スキーマの文字列化に失敗しました: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * スキーマの基本的な検証
 * 必須フィールドの存在確認のみ
 * 
 * @param schema 検証するスキーマ
 * @returns 有効な場合はtrue、そうでなければfalse
 */
export function validateBasicSchema(schema: FunctionSchema): boolean {
  // 必須フィールドの存在チェック
  if (!schema.$schema) return false;
  if (!schema.title) return false;
  if (!schema.type) return false;
  if (schema.type !== 'object' && schema.type !== 'function') return false;
  
  return true;
}

/**
 * スキーマオブジェクトから$refの参照を抽出
 * 
 * @param obj 探索対象のオブジェクト
 * @returns 見つかった$refの値の配列
 */
export function findSchemaReferences(obj: any): string[] {
  const refs: string[] = [];
  
  // オブジェクトの再帰的探索関数
  function explore(value: any) {
    if (!value || typeof value !== 'object') return;
    
    // 配列の場合は各要素を探索
    if (Array.isArray(value)) {
      for (const item of value) {
        explore(item);
      }
      return;
    }
    
    // $refプロパティがあれば追加
    if ('$ref' in value && typeof value.$ref === 'string') {
      refs.push(value.$ref);
    }
    
    // 他のプロパティを再帰的に探索
    for (const key in value) {
      explore(value[key]);
    }
  }
  
  explore(obj);
  return refs;
}
