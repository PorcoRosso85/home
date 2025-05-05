/**
 * アプリケーション層のデータベースサービス
 * 
 * データベース接続と基本操作を管理するシンプルなサービス
 */

import { 
  initializeDatabase, 
  isError,
  cleanupDatabaseResources
} from '../infrastructure/database/databaseService';

/**
 * データベース操作の結果型
 */
export interface DatabaseOperationResult {
  success: boolean;
  data?: any;
  error?: string;
}

/**
 * データベースサービスクラス
 * 
 * データベース接続のみを管理する最小構成
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
            message: 'データベースに既に接続されています'
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
      
      // グローバル変数として保存（デバッグ用）
      window.kuzu = kuzu;
      window.db = db;
      window.conn = conn;
      
      return {
        success: true,
        data: {
          message: 'データベースに接続しました'
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
   * 直接Cypherクエリを実行する
   * 
   * @param query 実行するCypherクエリ
   * @returns クエリ実行結果
   */
  public async executeDirectQuery(query: string): Promise<DatabaseOperationResult> {
    try {
      // データベース接続確認
      if (!this.conn) {
        const connectResult = await this.connect();
        if (!connectResult.success) {
          return connectResult;
        }
      }
      
      // クエリ実行
      console.log(`クエリ実行: ${query}`);
      const queryResult = await this.conn.query(query);
      
      // 結果の変換
      let resultData;
      if (queryResult.getAllObjects) {
        resultData = await queryResult.getAllObjects();
      } else {
        resultData = queryResult;
      }
      
      return {
        success: true,
        data: resultData
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
   * データベースのノード数とエッジ数を取得する
   * 
   * @returns ノード数とエッジ数
   */
  public async getStats(): Promise<DatabaseOperationResult> {
    try {
      // ノード数を取得
      const nodeCountResult = await this.executeDirectQuery("MATCH (n) RETURN COUNT(n) AS nodeCount");
      if (!nodeCountResult.success) return nodeCountResult;
      
      // エッジ数を取得
      const edgeCountResult = await this.executeDirectQuery("MATCH ()-[r]->() RETURN COUNT(r) AS edgeCount");
      if (!edgeCountResult.success) return edgeCountResult;
      
      // 結果を整形
      const nodeCount = nodeCountResult.data[0]?.nodeCount || 0;
      const edgeCount = edgeCountResult.data[0]?.edgeCount || 0;
      
      return {
        success: true,
        data: { nodeCount, edgeCount }
      };
    } catch (error) {
      console.error('データベース統計取得エラー:', error);
      return {
        success: false,
        error: `データベース統計の取得に失敗しました: ${error.message}`
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
}

// シングルトンインスタンスを作成
export const databaseService = new DatabaseService();