import * as logger from '../../../common/infrastructure/logger';

declare global {
  type Window = {
    kuzu: any;
    db: any;
    conn: any;
  }
}

export async function createConnection(): Promise<any> {
  logger.info('データベース初期化開始');
  
  try {
    // Kuzu-Wasmのロード
    const kuzuWasm = await import("kuzu-wasm");
    const kuzu = kuzuWasm.default || kuzuWasm;
    
    // グローバルにkuzuオブジェクトを設定
    window.kuzu = kuzu;
    
    // データベースと接続を作成し、グローバルに保存
    logger.debug('データベース作成中...');
    const db = new kuzu.Database("");
    const conn = new kuzu.Connection(db);
    
    // グローバルに接続も保存
    window.db = db;
    window.conn = conn;
    
    return conn;
  } catch (error) {
    logger.error('データベース初期化エラー:', error);
    throw error;
  }
}
