/**
 * schemaFileRepository.ts
 * 
 * スキーマファイルリポジトリ
 * 関数型アプローチで生成したスキーマをファイルに保存・管理するクラス
 */

import { fileSystem } from './fileSystem.ts';
import { FunctionSchema } from '../domain/schema.ts';
import { SchemaRepository } from '../domain/schemaRepository.ts';
import * as path from "node:path";

/**
 * スキーマファイルリポジトリの実装
 */
export class SchemaFileRepository implements SchemaRepository {
  private baseDir: string;
  
  /**
   * コンストラクタ
   * 
   * @param baseDir ファイル保存の基本ディレクトリ
   */
  constructor(baseDir: string = '.') {
    this.baseDir = baseDir;
  }
  
  /**
   * スキーマをJSONとして保存する
   * 
   * @param schema スキーマオブジェクト
   * @param key 保存するファイル名（パスを含む場合もある）
   * @param pretty 整形するかどうか（デフォルトはtrue）
   * @returns 保存が成功したかどうか
   */
  async save(
    schema: FunctionSchema,
    key: string,
    pretty: boolean = true
  ): Promise<boolean> {
    try {
      const outputPath = this.resolvePath(key);
      await fileSystem.writeJsonFile(outputPath, schema, pretty);
      return true;
    } catch (error) {
      console.error(`スキーマの保存中にエラーが発生しました: ${error}`);
      return false;
    }
  }
  
  /**
   * JSONからスキーマを読み込む
   * 
   * @param key ファイル名（パスを含む場合もある）
   * @returns 読み込まれたスキーマ、存在しない場合はnull
   */
  async findByKey(key: string): Promise<FunctionSchema | null> {
    try {
      const filePath = this.resolvePath(key);
      if (await this.exists(key)) {
        return await fileSystem.readJsonFile<FunctionSchema>(filePath);
      }
      return null;
    } catch (error) {
      console.error(`スキーマの読み込み中にエラーが発生しました: ${error}`);
      return null;
    }
  }
  
  /**
   * 条件に一致するスキーマを検索する
   * ファイルベースのため、すべてのファイルを読み込んでメモリ内でフィルタリング
   * 
   * @param predicate フィルタリング条件
   * @returns 条件に一致するスキーマの配列
   */
  async find(predicate: (item: FunctionSchema) => boolean): Promise<FunctionSchema[]> {
    try {
      // ディレクトリ内のすべてのJSONファイルを検索
      const files = await Deno.readDir(this.baseDir);
      const schemas: FunctionSchema[] = [];
      
      for await (const file of files) {
        if (file.isFile && file.name.endsWith('.json')) {
          try {
            const schema = await this.findByKey(file.name);
            if (schema && predicate(schema)) {
              schemas.push(schema);
            }
          } catch (error) {
            console.warn(`ファイル ${file.name} の処理中にエラーが発生しました: ${error}`);
            // エラーがあっても続行
          }
        }
      }
      
      return schemas;
    } catch (error) {
      console.error(`スキーマの検索中にエラーが発生しました: ${error}`);
      return [];
    }
  }
  
  /**
   * タイトルでスキーマを検索する
   * 
   * @param title 検索するスキーマのタイトル
   * @returns 見つかったスキーマ、存在しない場合はnull
   */
  async findByTitle(title: string): Promise<FunctionSchema | null> {
    const schemas = await this.find(schema => schema.title === title);
    return schemas.length > 0 ? schemas[0] : null;
  }
  
  /**
   * スキーマタイプでスキーマを検索する
   * 
   * @param type スキーマのタイプ
   * @returns 指定されたタイプのスキーマの配列
   */
  async findByType(type: string): Promise<FunctionSchema[]> {
    return await this.find(schema => schema.type === type);
  }
  
  /**
   * プロパティが存在するスキーマを検索する
   * 
   * @param propertyName 検索するプロパティ名
   * @returns 指定されたプロパティを持つスキーマの配列
   */
  async findByProperty(propertyName: string): Promise<FunctionSchema[]> {
    return await this.find(schema => 
      schema.properties && Object.prototype.hasOwnProperty.call(schema.properties, propertyName)
    );
  }
  
  /**
   * $refで参照されているスキーマを検索する
   * 
   * @param refUri 参照URI
   * @returns 指定されたURIを参照しているスキーマの配列
   */
  async findByRef(refUri: string): Promise<FunctionSchema[]> {
    return await this.find(schema => {
      // スキーマのJSONを文字列化して$refの存在を確認（単純な実装）
      const schemaStr = JSON.stringify(schema);
      return schemaStr.includes(`"$ref":"${refUri}"`);
    });
  }
  
  /**
   * キーに関連付けられたスキーマが存在するか確認する
   * 
   * @param key ファイル名（パスを含む場合もある）
   * @returns ファイルが存在する場合はtrue、それ以外はfalse
   */
  async exists(key: string): Promise<boolean> {
    try {
      const filePath = this.resolvePath(key);
      await Deno.stat(filePath);
      return true;
    } catch {
      return false;
    }
  }
  
  /**
   * キーに関連付けられたスキーマを削除する
   * 
   * @param key ファイル名（パスを含む場合もある）
   * @returns 削除が成功したかどうか
   */
  async delete(key: string): Promise<boolean> {
    try {
      const filePath = this.resolvePath(key);
      if (await this.exists(key)) {
        await Deno.remove(filePath);
        return true;
      }
      return false;
    } catch (error) {
      console.error(`スキーマの削除中にエラーが発生しました: ${error}`);
      return false;
    }
  }
  
  /**
   * キーをベースディレクトリからの相対パスに解決する
   * 
   * @param key ファイル名または相対パス
   * @returns 絶対パス
   */
  private resolvePath(key: string): string {
    // キーにパスが含まれている場合は、そのまま使用
    // そうでなければ、ベースディレクトリと結合
    if (path.isAbsolute(key) || key.includes('/') || key.includes('\\')) {
      return key;
    }
    return path.join(this.baseDir, key);
  }
}

/**
 * スキーマファイルリポジトリのファクトリ関数
 * 
 * @param baseDir ファイル保存の基本ディレクトリ
 * @returns スキーマファイルリポジトリのインスタンス
 */
export function createSchemaFileRepository(baseDir: string = '.'): SchemaRepository {
  return new SchemaFileRepository(baseDir);
}

/**
 * 従来のAPIとの互換性のためのオブジェクト
 * @deprecated 新しいインターフェースを使用してください
 */
export const schemaFileRepository = {
  /**
   * スキーマをJSONとして保存する
   * 
   * @param schema スキーマオブジェクト
   * @param outputPath 出力先ファイルパス
   * @param pretty 整形するかどうか（デフォルトはtrue）
   */
  saveSchema: async (
    schema: FunctionSchema,
    outputPath: string,
    pretty: boolean = true
  ): Promise<void> => {
    const repo = new SchemaFileRepository();
    await repo.save(schema, outputPath, pretty);
  },
  
  /**
   * JSONからスキーマを読み込む
   * 
   * @param filePath ファイルパス
   * @returns 読み込まれたスキーマ
   */
  loadSchema: async (filePath: string): Promise<FunctionSchema> => {
    const repo = new SchemaFileRepository();
    const schema = await repo.findByKey(filePath);
    if (!schema) {
      throw new Error(`ファイル ${filePath} が見つかりません。`);
    }
    return schema;
  }
};
