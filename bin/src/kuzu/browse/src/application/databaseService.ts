/**
 * アプリケーション層のデータベースサービス - シンプル版
 * 
 * Parquet読み込み機能のみサポートするシンプルなサービス
 */

import { 
  initializeDatabase, 
  isError,
  executeCypherScript,
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
 * データベースに接続する
 * @returns 接続結果
 */
export const connect = async (): Promise<DatabaseOperationResult> => {
  try {
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
    
    // 接続が成功したかテスト
    try {
      console.log('接続テスト実行中...');
      const testQuery = 'RETURN 1 AS test';
      const testResult = await conn.query(testQuery);
      const testObj = await testResult.getAllObjects();
      
      if (!testResult || !testObj || testObj.length === 0) {
        console.error('接続テストに失敗: 有効な結果が返されませんでした');
        
        // 新しく作成したリソースのクリーンアップを試みる
        await cleanupDatabaseResources(conn, db).catch(e => 
          console.warn('リソースクリーンアップエラー:', e));
        
        return {
          success: false,
          error: '接続は確立されましたが、テストクエリの実行に失敗しました'
        };
      }
      
      console.log('接続テスト成功:', testObj);
    } catch (testErr) {
      console.error('接続テストエラー:', testErr);
      
      // 新しく作成したリソースのクリーンアップを試みる
      await cleanupDatabaseResources(conn, db).catch(e => 
        console.warn('リソースクリーンアップエラー:', e));
      
      return {
        success: false,
        error: `接続テストに失敗しました: ${testErr.message}`
      };
    }
    
    // グローバル変数として保存（デバッグ用）
    window.conn = conn;
    window.db = db;
    window.kuzu = kuzu;
    
    return {
      success: true,
      data: {
        db,
        conn,
        kuzu
      }
    };
  } catch (error) {
    console.error('データベース接続エラー:', error);
    
    return {
      success: false,
      error: `データベース接続に失敗しました: ${error.message}`
    };
  }
};

/**
 * Cypherスクリプトを実行する
 * @param conn データベース接続
 * @param scriptPath スクリプトパス
 * @returns 実行結果
 */
export const executeScript = async (
  conn: any, 
  scriptPath: string
): Promise<DatabaseOperationResult> => {
  try {
    const result = await executeCypherScript(conn, scriptPath);
    
    if (result === true) {
      return {
        success: true,
        data: { message: `スクリプト ${scriptPath} の実行に成功しました` }
      };
    } else {
      return {
        success: false,
        error: result.message
      };
    }
  } catch (error) {
    return {
      success: false,
      error: `スクリプト実行エラー: ${error.message}`
    };
  }
};

// グローバル定義（TypeScript用）
declare global {
  interface Window {
    db_path: string;
    conn: any;
    db: any;
    kuzu: any;
  }
}