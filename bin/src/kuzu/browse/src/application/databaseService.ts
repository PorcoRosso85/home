/**
 * アプリケーション層のデータベースサービス
 * 
 * インフラストラクチャ層のデータベースサービスとクエリサービスを組み合わせ、
 * データベース操作を一元管理するサービス
 */

import { 
  initializeDatabase, 
  isError, 
  setupUserTable, 
  cleanupDatabaseResources 
} from '../infrastructure/database/databaseService';

import { 
  executeQuery, 
  QueryType, 
  QueryParams,
  QueryServiceResult 
} from './queryService';

/**
 * データベース操作の結果型
 */
export interface DatabaseOperationResult {
  success: boolean;
  data?: any;
  error?: string;
  query?: string;
}

/**
 * データベースサービスクラス
 * 
 * データベース接続とクエリ実行を管理する
 */
export class DatabaseService {
  private conn: any = null;
  private db: any = null;
  private kuzu: any = null;
  
  /**
   * データベースに接続する
   * 
   * @returns 接続結果
   */
  public async connect(): Promise<DatabaseOperationResult> {
    try {
      // すでに接続されている場合は再利用
      if (this.conn) {
        return {
          success: true,
          data: { 
            message: 'データベースに既に接続されています',
            connection: this.conn
          }
        };
      }
      
      // データベース初期化
      console.log('データベース接続を開始します...');
      const dbResult = await initializeDatabase();
      
      if (isError(dbResult)) {
        return {
          success: false,
          error: dbResult.message
        };
      }
      
      const { kuzu, db, conn } = dbResult;
      this.kuzu = kuzu;
      this.db = db;
      this.conn = conn;
      
      // Userテーブルセットアップ（必要に応じて）
      const setupError = await setupUserTable(conn);
      if (setupError) {
        return {
          success: false,
          error: setupError.message
        };
      }
      
      // グローバル変数として保存（デバッグ用）
      window.kuzu = kuzu;
      window.db = db;
      window.conn = conn;
      
      return {
        success: true,
        data: {
          message: 'データベースに接続しました',
          connection: conn
        }
      };
    } catch (error) {
      console.error('データベース接続エラー:', error);
      return {
        success: false,
        error: `データベース接続に失敗しました: ${error.message}`
      };
    }
  }
  
  /**
   * クエリを実行する
   * 
   * @param queryType クエリタイプ
   * @param params クエリパラメータ
   * @returns クエリ実行結果
   */
  public async executeQuery(
    queryType: QueryType, 
    params: QueryParams = {}
  ): Promise<DatabaseOperationResult> {
    try {
      // データベース接続確認
      if (!this.conn) {
        const connectResult = await this.connect();
        if (!connectResult.success) {
          return connectResult;
        }
      }
      
      // クエリ実行
      const { result, query } = await executeQuery(this.conn, queryType, params);
      
      // エラー処理
      if ('code' in result) {
        return {
          success: false,
          error: result.message,
          query
        };
      }
      
      return {
        success: true,
        data: result,
        query
      };
    } catch (error) {
      console.error('クエリ実行エラー:', error);
      return {
        success: false,
        error: `クエリ実行に失敗しました: ${error.message}`
      };
    }
  }
  
  /**
   * データベース接続を閉じる
   * 
   * @returns 処理結果
   */
  public async disconnect(): Promise<DatabaseOperationResult> {
    try {
      if (!this.conn || !this.db) {
        return {
          success: true,
          data: { message: 'データベース接続は既に閉じられています' }
        };
      }
      
      const cleanupError = await cleanupDatabaseResources(this.conn, this.db);
      if (cleanupError) {
        return {
          success: false,
          error: cleanupError.message
        };
      }
      
      this.conn = null;
      this.db = null;
      this.kuzu = null;
      
      // グローバル変数からも削除
      window.conn = null;
      window.db = null;
      window.kuzu = null;
      
      return {
        success: true,
        data: { message: 'データベース接続を閉じました' }
      };
    } catch (error) {
      console.error('データベース切断エラー:', error);
      return {
        success: false,
        error: `データベース接続の切断に失敗しました: ${error.message}`
      };
    }
  }
  
  /**
   * データベース接続の状態を取得する
   * 
   * @returns 接続状態
   */
  public getConnectionStatus(): any {
    return {
      isConnected: !!this.conn,
      databaseInstance: this.db,
      connection: this.conn
    };
  }
}

// シングルトンインスタンスを作成
export const databaseService = new DatabaseService();
