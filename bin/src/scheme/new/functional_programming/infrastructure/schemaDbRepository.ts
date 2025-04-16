/**
 * schemaDbRepository.ts
 * 
 * スキーマのデータベースリポジトリ実装
 * スキーマデータのデータベース永続化を担当
 */

import { 
  SchemaRepository, 
  TransactionalSchemaRepository 
} from '../domain/schemaRepository.ts';
import { FunctionSchema } from '../domain/schema.ts';
import { 
  DbClient, 
  Transaction, 
  QueryParams 
} from './dbClient.ts';

/**
 * スキーマDBリポジトリの実装
 */
export class SchemaDbRepository implements TransactionalSchemaRepository {
  private client: DbClient;
  private collectionName: string;
  
  /**
   * コンストラクタ
   * 
   * @param client DBクライアント
   * @param collectionName コレクション/テーブル名
   */
  constructor(client: DbClient, collectionName: string = 'schemas') {
    this.client = client;
    this.collectionName = collectionName;
  }
  
  /**
   * データベースに接続する
   */
  async connect(): Promise<void> {
    await this.client.connect();
    // 必要に応じてスキーマ/テーブル作成などの初期化処理を行う
    // await this.initializeSchema();
  }
  
  /**
   * スキーマをデータベースに保存する
   * 
   * @param schema 保存するスキーマ
   * @param key スキーマを識別するキー（通常はタイトルなど）
   * @returns 保存が成功したかどうか
   */
  async save(schema: FunctionSchema, key: string): Promise<boolean> {
    try {
      // キーをスキーマに埋め込む
      const schemaWithKey = { ...schema, id: key };
      
      // 既に存在するかチェック
      const exists = await this.exists(key);
      
      // 存在する場合は更新、そうでなければ挿入
      const query = exists
        ? `UPDATE ${this.collectionName} SET data = ? WHERE id = ?`
        : `INSERT INTO ${this.collectionName} (id, data) VALUES (?, ?)`;
      
      const params = exists
        ? { data: JSON.stringify(schema), id: key }
        : { id: key, data: JSON.stringify(schema) };
      
      await this.client.query(query, params);
      return true;
    } catch (error) {
      console.error('スキーマの保存中にエラーが発生しました:', error);
      return false;
    }
  }
  
  /**
   * キーでスキーマを検索する
   * 
   * @param key スキーマを識別するキー
   * @returns 見つかったスキーマまたはnull
   */
  async findByKey(key: string): Promise<FunctionSchema | null> {
    try {
      const query = `SELECT data FROM ${this.collectionName} WHERE id = ?`;
      const result = await this.client.queryOne<{data: string}>(query, { id: key });
      
      if (!result) return null;
      
      return JSON.parse(result.data) as FunctionSchema;
    } catch (error) {
      console.error(`キー ${key} でのスキーマ検索中にエラーが発生しました:`, error);
      return null;
    }
  }
  
  /**
   * 条件に一致するスキーマを検索する
   * 
   * @param predicate 条件関数
   * @returns 条件に一致するスキーマの配列
   */
  async find(predicate: (item: FunctionSchema) => boolean): Promise<FunctionSchema[]> {
    try {
      // すべてのスキーマを取得して、メモリ内でフィルタリング
      // より複雑なデータベースではクエリに変換することも可能
      const query = `SELECT data FROM ${this.collectionName}`;
      const results = await this.client.query<{data: string}>(query);
      
      const schemas = results.map(result => JSON.parse(result.data) as FunctionSchema);
      return schemas.filter(predicate);
    } catch (error) {
      console.error('スキーマ検索中にエラーが発生しました:', error);
      return [];
    }
  }
  
  /**
   * タイトルでスキーマを検索する
   * 
   * @param title 検索するスキーマのタイトル
   * @returns 見つかったスキーマまたはnull
   */
  async findByTitle(title: string): Promise<FunctionSchema | null> {
    try {
      // タイトルで検索するクエリ
      const query = `SELECT data FROM ${this.collectionName} WHERE data->'title' = ?`;
      const result = await this.client.queryOne<{data: string}>(query, { title });
      
      if (!result) return null;
      
      return JSON.parse(result.data) as FunctionSchema;
    } catch (error) {
      console.error(`タイトル ${title} でのスキーマ検索中にエラーが発生しました:`, error);
      return null;
    }
  }
  
  /**
   * スキーマタイプでスキーマを検索
   * 
   * @param type スキーマのタイプ
   * @returns 指定されたタイプのスキーマの配列
   */
  async findByType(type: string): Promise<FunctionSchema[]> {
    try {
      // タイプで検索するクエリ
      const query = `SELECT data FROM ${this.collectionName} WHERE data->'type' = ?`;
      const results = await this.client.query<{data: string}>(query, { type });
      
      return results.map(result => JSON.parse(result.data) as FunctionSchema);
    } catch (error) {
      console.error(`タイプ ${type} でのスキーマ検索中にエラーが発生しました:`, error);
      return [];
    }
  }
  
  /**
   * 特定のプロパティを持つスキーマを検索する
   * 
   * @param propertyName プロパティ名
   * @returns そのプロパティを持つスキーマの配列
   */
  async findByProperty(propertyName: string): Promise<FunctionSchema[]> {
    try {
      // プロパティ名で検索するクエリ
      // 実際のDBの実装によって検索ロジックは異なる
      const query = `SELECT data FROM ${this.collectionName} WHERE data->'properties' ? ?`;
      const results = await this.client.query<{data: string}>(query, { property: propertyName });
      
      return results.map(result => JSON.parse(result.data) as FunctionSchema);
    } catch (error) {
      console.error(`プロパティ ${propertyName} でのスキーマ検索中にエラーが発生しました:`, error);
      return [];
    }
  }
  
  /**
   * 特定の参照URIを持つスキーマを検索する
   * 
   * @param refUri 参照URI
   * @returns 指定されたURIを参照しているスキーマの配列
   */
  async findByRef(refUri: string): Promise<FunctionSchema[]> {
    try {
      // JSONデータ内の$refプロパティを検索するクエリ
      // 実際のDBの実装によって検索ロジックは異なる
      const query = `SELECT data FROM ${this.collectionName} WHERE data::text LIKE ?`;
      const results = await this.client.query<{data: string}>(
        query, 
        { refPattern: `%"$ref":"${refUri}"%` }
      );
      
      return results.map(result => JSON.parse(result.data) as FunctionSchema);
    } catch (error) {
      console.error(`参照 ${refUri} でのスキーマ検索中にエラーが発生しました:`, error);
      return [];
    }
  }
  
  /**
   * スキーマが存在するか確認する
   * 
   * @param key スキーマのキー
   * @returns 存在する場合はtrue
   */
  async exists(key: string): Promise<boolean> {
    try {
      const query = `SELECT 1 FROM ${this.collectionName} WHERE id = ?`;
      return await this.client.exists(query, { id: key });
    } catch (error) {
      console.error(`キー ${key} の存在確認中にエラーが発生しました:`, error);
      return false;
    }
  }
  
  /**
   * スキーマを削除する
   * 
   * @param key スキーマのキー
   * @returns 削除に成功したかどうか
   */
  async delete(key: string): Promise<boolean> {
    try {
      const query = `DELETE FROM ${this.collectionName} WHERE id = ?`;
      await this.client.query(query, { id: key });
      return true;
    } catch (error) {
      console.error(`キー ${key} のスキーマ削除中にエラーが発生しました:`, error);
      return false;
    }
  }
  
  /**
   * トランザクションを開始する
   * 
   * @returns トランザクションオブジェクト
   */
  async beginTransaction(): Promise<Transaction> {
    return await this.client.beginTransaction();
  }
  
  /**
   * スキーマと関連データを整合性を保ちながら更新する
   * 
   * @param schema 更新するスキーマ
   * @param key スキーマを識別するキー
   * @param updateReferences 参照も更新するかどうか
   * @returns 更新が成功したかどうか
   */
  async saveWithReferences(
    schema: FunctionSchema, 
    key: string, 
    updateReferences: boolean
  ): Promise<boolean> {
    // トランザクションを開始
    const transaction = await this.beginTransaction();
    
    try {
      // メインのスキーマを保存
      const success = await this.save(schema, key);
      if (!success) {
        await transaction.rollback();
        return false;
      }
      
      // 参照の更新が必要な場合
      if (updateReferences) {
        // $refプロパティを検索して関連データを更新
        // これは実際のユースケースに応じて実装する必要がある
        // 例: this.updateReferences(schema, key);
      }
      
      // すべての処理が成功したらコミット
      await transaction.commit();
      return true;
    } catch (error) {
      // エラーが発生した場合はロールバック
      await transaction.rollback();
      console.error('スキーマと参照の更新中にエラーが発生しました:', error);
      return false;
    }
  }
  
  /**
   * データベースのスキーマ/テーブルを初期化する
   * 実際の実装はデータベースエンジンに依存
   */
  private async initializeSchema(): Promise<void> {
    try {
      // スキーマテーブルが存在するか確認
      const checkQuery = `SELECT 1 FROM information_schema.tables WHERE table_name = ?`;
      const exists = await this.client.exists(checkQuery, { table_name: this.collectionName });
      
      if (!exists) {
        // テーブルが存在しない場合は作成
        const createQuery = `
          CREATE TABLE ${this.collectionName} (
            id TEXT PRIMARY KEY,
            data JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          )
        `;
        await this.client.query(createQuery);
        
        // インデックスの作成
        await this.client.query(`CREATE INDEX idx_${this.collectionName}_title ON ${this.collectionName} ((data->>'title'))`);
        await this.client.query(`CREATE INDEX idx_${this.collectionName}_type ON ${this.collectionName} ((data->>'type'))`);
      }
    } catch (error) {
      console.error('スキーマ初期化中にエラーが発生しました:', error);
      throw error;
    }
  }
}

/**
 * スキーマDBリポジトリのファクトリ関数
 * 
 * @param client DBクライアント
 * @param collectionName コレクション/テーブル名
 * @returns スキーマDBリポジトリのインスタンス
 */
export function createSchemaDbRepository(
  client: DbClient, 
  collectionName: string = 'schemas'
): SchemaRepository {
  return new SchemaDbRepository(client, collectionName);
}
