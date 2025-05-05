/**
 * 最小構成のKuzuデータベースサービス
 * データベースの初期化と接続管理を担当します
 */

import { DB_DIR } from '../variables';

/**
 * データベース初期化の戻り値型
 */
export interface DatabaseInit {
  kuzu: any;
  db: any;
  conn: any;
}

/**
 * データベースエラーの型
 */
export interface DatabaseError {
  code: string;
  message: string;
  stack?: string;
}

/**
 * 初期化結果型
 */
export type DatabaseResult = DatabaseInit | DatabaseError;

/**
 * エラー判定関数
 */
export const isError = (result: DatabaseResult): result is DatabaseError => {
  return 'code' in result && 'message' in result;
};

/**
 * エラー作成関数
 */
export const createError = (code: string, message: string, error?: Error): DatabaseError => {
  return {
    code,
    message,
    stack: error?.stack
  };
};

/**
 * Kuzuデータベースを初期化する
 * @returns DatabaseInit または DatabaseError
 */
export const initializeDatabase = async (): Promise<DatabaseResult> => {
  try {
    console.log('Kuzu-Wasmモジュールのロード開始...');
    
    // Kuzu-Wasmのロード
    const kuzuWasm = await import("../../../node_modules/kuzu-wasm");
    console.log('Kuzu-Wasmモジュールのロード完了');
    
    // Kuzuインスタンス化
    console.log('Kuzuインスタンス化開始...');
    const kuzu = kuzuWasm.default || kuzuWasm;
    console.log('Kuzuインスタンス化完了');
    
    // DBファイルを参照
    console.log(`データベース作成開始...パス: ${DB_DIR}`);
    const db = new kuzu.Database(DB_DIR);
    console.log('データベース作成完了');
    
    // グローバルにDBパスを保存（UI表示用）
    window.db_path = DB_DIR;
    
    // データベース接続の作成
    console.log('データベース接続開始...');
    const conn = new kuzu.Connection(db);
    console.log('データベース接続完了');

    return { kuzu, db, conn };
  } catch (error) {
    console.error('Kuzu初期化エラー:', error);
    return createError(
      'DB_INIT_ERROR',
      `Kuzuの初期化中にエラーが発生しました: ${error.message}`,
      error
    );
  }
};

/**
 * データベース接続とリソースをクリーンアップする
 * @param conn データベース接続
 * @param db データベースインスタンス
 * @returns エラーがあればDatabaseError、なければnull
 */
export const cleanupDatabaseResources = async (
  conn: any, 
  db: any
): Promise<DatabaseError | null> => {
  try {
    console.log('接続をクローズしています...');
    await conn.close();
    console.log('接続がクローズされました');
    
    await db.close();
    console.log('データベースがクローズされました');
    return null;
  } catch (error) {
    console.error('クリーンアップエラー:', error);
    return createError(
      'CLEANUP_ERROR',
      `データベースリソースのクリーンアップ中にエラーが発生しました: ${error.message}`,
      error
    );
  }
};