/**
 * repository.ts
 * 
 * リポジトリパターンのインターフェース定義
 * オブジェクトの永続化方法を抽象化し、ドメインとインフラの間の依存関係を管理
 */

/**
 * 汎用的なリポジトリインターフェース
 * Tは保存/読み込みの対象となるエンティティの型
 */
export interface Repository<T> {
  /**
   * エンティティを保存する
   * 
   * @param entity 保存するエンティティ
   * @param key エンティティを識別するキー
   * @returns 保存が成功したかどうか
   */
  save(entity: T, key: string): Promise<boolean>;
  
  /**
   * エンティティを取得する
   * 
   * @param key エンティティを識別するキー
   * @returns 取得したエンティティ、存在しない場合はnull
   */
  findByKey(key: string): Promise<T | null>;
  
  /**
   * 条件に一致するエンティティを検索する
   * 
   * @param predicate フィルタリング条件
   * @returns 条件に一致するエンティティの配列
   */
  find(predicate: (item: T) => boolean): Promise<T[]>;
  
  /**
   * キーに関連付けられたエンティティが存在するか確認する
   * 
   * @param key エンティティを識別するキー
   * @returns エンティティが存在する場合はtrue、それ以外はfalse
   */
  exists(key: string): Promise<boolean>;
  
  /**
   * キーに関連付けられたエンティティを削除する
   * 
   * @param key エンティティを識別するキー
   * @returns 削除が成功したかどうか
   */
  delete(key: string): Promise<boolean>;
}

/**
 * トランザクション対応リポジトリインターフェース
 * データベースなどトランザクションをサポートするストレージに対応
 */
export interface TransactionalRepository<T> extends Repository<T> {
  /**
   * トランザクションを開始する
   * 
   * @returns トランザクションオブジェクト
   */
  beginTransaction(): Promise<Transaction>;
}

/**
 * トランザクションインターフェース
 */
export interface Transaction {
  /**
   * トランザクションをコミットする
   */
  commit(): Promise<void>;
  
  /**
   * トランザクションをロールバックする
   */
  rollback(): Promise<void>;
}

/**
 * バッチ操作に対応したリポジトリインターフェース
 */
export interface BatchRepository<T> extends Repository<T> {
  /**
   * 複数のエンティティを一括で保存する
   * 
   * @param entities 保存するエンティティの配列
   * @param keyExtractor 各エンティティからキーを抽出する関数
   * @returns 保存が成功したかどうか
   */
  saveAll(entities: T[], keyExtractor: (entity: T) => string): Promise<boolean>;
  
  /**
   * 複数のキーに関連付けられたエンティティを一括で取得する
   * 
   * @param keys 取得するエンティティのキー配列
   * @returns 取得したエンティティの配列
   */
  findByKeys(keys: string[]): Promise<T[]>;
}
