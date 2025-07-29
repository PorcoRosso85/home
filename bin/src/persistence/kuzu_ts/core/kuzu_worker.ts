/**
 * KuzuDB Worker Process
 * 
 * npm:kuzuを別プロセスで実行し、パニックを隔離
 */

// ワーカー内ではnpm:kuzuを直接使用
import { Database, Connection } from "npm:kuzu";

interface WorkerMessage {
  id: string;
  type: "createDatabase" | "createConnection" | "query" | "close";
  payload: any;
}

interface WorkerResponse {
  id: string;
  success: boolean;
  data?: any;
  error?: string;
}

// データベースとコネクションの管理
const databases = new Map<string, Database>();
const connections = new Map<string, Connection>();

// メッセージハンドラー
self.onmessage = async (event: MessageEvent<WorkerMessage>) => {
  const { id, type, payload } = event.data;
  
  try {
    let response: WorkerResponse;
    
    switch (type) {
      case "createDatabase": {
        const { dbId, path, options } = payload;
        const db = new Database(path, options?.maxSize);
        databases.set(dbId, db);
        response = { id, success: true, data: { dbId } };
        break;
      }
      
      case "createConnection": {
        const { connId, dbId } = payload;
        const db = databases.get(dbId);
        if (!db) throw new Error(`Database ${dbId} not found`);
        
        const conn = new Connection(db);
        connections.set(connId, conn);
        response = { id, success: true, data: { connId } };
        break;
      }
      
      case "query": {
        const { connId, sql } = payload;
        const conn = connections.get(connId);
        if (!conn) throw new Error(`Connection ${connId} not found`);
        
        const result = await conn.query(sql);
        const rows = await result.getAll();
        response = { id, success: true, data: rows };
        break;
      }
      
      case "close": {
        const { connId, dbId } = payload;
        
        if (connId) {
          const conn = connections.get(connId);
          if (conn) {
            await conn.close();
            connections.delete(connId);
          }
        }
        
        if (dbId) {
          const db = databases.get(dbId);
          if (db) {
            await db.close();
            databases.delete(dbId);
          }
        }
        
        response = { id, success: true };
        break;
      }
      
      default:
        throw new Error(`Unknown message type: ${type}`);
    }
    
    self.postMessage(response);
  } catch (error) {
    const response: WorkerResponse = {
      id,
      success: false,
      error: error instanceof Error ? error.message : String(error)
    };
    self.postMessage(response);
  }
};

// ワーカー終了時のクリーンアップ
self.addEventListener("unload", async () => {
  // すべてのコネクションを閉じる
  for (const conn of connections.values()) {
    try {
      await conn.close();
    } catch {}
  }
  
  // すべてのデータベースを閉じる
  for (const db of databases.values()) {
    try {
      await db.close();
    } catch {}
  }
});