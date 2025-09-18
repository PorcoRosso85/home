/**
 * schemaCore.ts
 * 
 * 関数型プログラミングのためのスキーマの中核機能を提供する関数群
 */

import * as fs from 'node:fs';
import * as path from 'node:path';
import { SchemaSourceType } from '../types/SchemaSourceType.ts';
import { JSON_SCHEMA, SCHEMA_DEFAULTS } from '../infrastructure/variables.ts';

/**
 * 基本的なスキーマ構造
 */
export interface FunctionSchema {
  $schema: string;
  title: string;
  description: string;
  type: string;
  required: string[];
  properties: Record<string, any>;
}

/**
 * 基本的なJSONスキーマ構造を生成する
 * 
 * @param title スキーマのタイトル
 * @param description スキーマの説明
 * @returns 基本的なスキーマ構造
 */
export function createBaseSchema(
  title: string = SCHEMA_DEFAULTS.TITLE, 
  description: string = SCHEMA_DEFAULTS.DESCRIPTION
): FunctionSchema {
  return {
    $schema: "https://json-schema.org/draft/2020-12/schema",
    title,
    description,
    type: 'object',
    required: ['title', 'type', 'signatures'],
    properties: {
      title: {
        type: 'string',
        description: '関数型の名前'
      },
      description: {
        type: 'string',
        description: '関数型の説明'
      },
      type: {
        type: 'string',
        enum: ['function'],
        description: "型のカテゴリ (関数のため 'function'固定)"
      }
    }
  };
}

/**
 * スキーマをJSON文字列に変換
 * 
 * @param schema スキーマオブジェクト
 * @param pretty 整形するかどうか
 * @returns JSON文字列
 */
export function schemaToJson(schema: FunctionSchema, pretty: boolean = true): string {
  return pretty 
    ? JSON.stringify(schema, null, 2) 
    : JSON.stringify(schema);
}

/**
 * スキーマをファイルに保存
 * 
 * @param schema スキーマオブジェクト
 * @param filePath 保存先ファイルパス
 */
export function saveSchemaToFile(schema: FunctionSchema, filePath: string): void {
  const dirPath = path.dirname(filePath);
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
  fs.writeFileSync(filePath, schemaToJson(schema), 'utf8');
}

/**
 * スキーマに新しいプロパティを追加
 * 
 * @param schema 元のスキーマ
 * @param propertyName プロパティ名
 * @param propertySchema プロパティのスキーマ
 * @returns 更新されたスキーマ
 */
export function addPropertyToSchema(
  schema: FunctionSchema, 
  propertyName: string, 
  propertySchema: any
): FunctionSchema {
  return {
    ...schema,
    properties: {
      ...schema.properties,
      [propertyName]: propertySchema
    }
  };
}

/**
 * スキーマに必須プロパティを追加
 * 
 * @param schema 元のスキーマ
 * @param requiredProperty 必須プロパティ名
 * @returns 更新されたスキーマ
 */
export function addRequiredProperty(
  schema: FunctionSchema, 
  requiredProperty: string
): FunctionSchema {
  if (schema.required.includes(requiredProperty)) {
    return schema;
  }
  
  return {
    ...schema,
    required: [...schema.required, requiredProperty]
  };
}

/**
 * スキーマ参照URIを生成
 * 
 * @param typeId スキーマの型ID
 * @param metaSource メタスキーマのソース種別
 * @param metaId メタスキーマのID
 * @returns スキーマ参照URI
 */
export function createReferenceUri(
  typeId: string, 
  metaSource: SchemaSourceType, 
  metaId: string
): string {
  return `scheme://${typeId}/${metaSource}:${metaId}`;
}
