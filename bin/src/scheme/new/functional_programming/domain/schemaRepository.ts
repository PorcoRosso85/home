/**
 * schemaRepository.ts
 * 
 * スキーマ特化型のリポジトリインターフェース
 * 関数型スキーマの永続化と検索のための機能を定義
 */

import { Repository, BatchRepository, TransactionalRepository } from './repository.ts';
import { FunctionSchema } from './schema.ts';

/**
 * スキーマリポジトリの基本インターフェース
 */
export interface SchemaRepository extends Repository<FunctionSchema> {
  /**
   * タイトルでスキーマを検索する
   * 
   * @param title 検索するスキーマのタイトル
   * @returns 見つかったスキーマ、存在しない場合はnull
   */
  findByTitle(title: string): Promise<FunctionSchema | null>;
  
  /**
   * スキーマタイプでスキーマを検索する
   * 
   * @param type スキーマのタイプ
   * @returns 指定されたタイプのスキーマの配列
   */
  findByType(type: string): Promise<FunctionSchema[]>;
  
  /**
   * プロパティが存在するスキーマを検索する
   * 
   * @param propertyName 検索するプロパティ名
   * @returns 指定されたプロパティを持つスキーマの配列
   */
  findByProperty(propertyName: string): Promise<FunctionSchema[]>;
  
  /**
   * $refで参照されているスキーマを検索する
   * 
   * @param refUri 参照URI
   * @returns 指定されたURIを参照しているスキーマの配列
   */
  findByRef(refUri: string): Promise<FunctionSchema[]>;
}

/**
 * バッチ操作に対応したスキーマリポジトリ
 */
export interface BatchSchemaRepository extends SchemaRepository, BatchRepository<FunctionSchema> {
  /**
   * 複数のスキーマを相互参照データと共に更新する
   * 
   * @param schemas 更新するスキーマの配列
   * @returns 更新が成功したかどうか
   */
  updateSchemas(schemas: FunctionSchema[]): Promise<boolean>;
}

/**
 * トランザクション対応スキーマリポジトリ
 */
export interface TransactionalSchemaRepository extends SchemaRepository, TransactionalRepository<FunctionSchema> {
  /**
   * スキーマと関連データを整合性を保ちながら更新する
   * 
   * @param schema 更新するスキーマ
   * @param key スキーマを識別するキー
   * @param updateReferences 参照も更新するかどうか
   * @returns 更新が成功したかどうか
   */
  saveWithReferences(schema: FunctionSchema, key: string, updateReferences: boolean): Promise<boolean>;
}
