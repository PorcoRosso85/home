/**
 * KuzuDB Worker Client
 * 
 * ワーカープロセスと通信するクライアント実装
 */
import type { DatabaseResult, ConnectionResult } from "./result_types.ts";
import { createValidationError, createFileOperationError } from "./errors.ts";
import { log } from "log_ts/mod.ts";

// ワーカーインスタンス
let worker: Worker | null = null;
let messageId = 0;
const pendingRequests = new Map<string, {
  resolve: (value: any) => void;
  reject: (error: any) => void;
}>();

/**
 * ワーカーを初期化
 */
function initWorker() {
  if (!worker) {
    worker = new Worker(
      new URL("./kuzu_worker.ts", import.meta.url).href,
      { 
        type: "module",
        deno: {
          permissions: {
            read: true,
            write: true,
            net: true,
            env: true,
            ffi: true
          }
        }
      }
    );
    
    // レスポンスハンドラー
    worker.onmessage = (event) => {
      const { id, success, data, error } = event.data;
      const pending = pendingRequests.get(id);
      
      if (pending) {
        if (success) {
          pending.resolve(data);
        } else {
          pending.reject(new Error(error));
        }
        pendingRequests.delete(id);
      }
    };
    
    // エラーハンドラー
    worker.onerror = (error) => {
      log("ERROR", {
        uri: "kuzu_ts.database_worker_client",
        message: "Worker error",
        error: String(error)
      });
    };
    
    log("INFO", {
      uri: "kuzu_ts.database_worker_client",
      message: "Worker initialized"
    });
  }
}

/**
 * ワーカーにメッセージを送信
 */
async function sendMessage(type: string, payload: any): Promise<any> {
  initWorker();
  
  const id = String(++messageId);
  
  return new Promise((resolve, reject) => {
    pendingRequests.set(id, { resolve, reject });
    worker!.postMessage({ id, type, payload });
    
    // タイムアウト設定（30秒）
    setTimeout(() => {
      if (pendingRequests.has(id)) {
        pendingRequests.delete(id);
        reject(new Error("Worker request timeout"));
      }
    }, 30000);
  });
}

// データベースプロキシクラス
export class WorkerDatabase {
  constructor(private dbId: string) {}
  
  async close(): Promise<void> {
    await sendMessage("close", { dbId: this.dbId });
  }
}

// コネクションプロキシクラス
export class WorkerConnection {
  constructor(
    private connId: string,
    private dbId: string
  ) {}
  
  async query(sql: string): Promise<any> {
    const rows = await sendMessage("query", { 
      connId: this.connId, 
      sql 
    });
    return {
      getAll: async () => rows
    };
  }
  
  async close(): Promise<void> {
    await sendMessage("close", { connId: this.connId });
  }
}

/**
 * ワーカープロセスでデータベースを作成
 */
export async function createDatabaseWorker(
  path: string,
  options: { bufferPoolSize?: number } = {}
): Promise<DatabaseResult> {
  if (!path || path.trim() === "") {
    return createValidationError(
      "Database path cannot be empty",
      "path",
      path,
      "non-empty string",
      "Provide a valid file path or ':memory:' for in-memory database"
    );
  }
  
  try {
    const dbId = `db_${Date.now()}_${Math.random()}`;
    
    log("INFO", {
      uri: "kuzu_ts.database_worker_client",
      message: "Creating database in worker",
      path,
      dbId
    });
    
    await sendMessage("createDatabase", {
      dbId,
      path,
      options: { maxSize: options.bufferPoolSize }
    });
    
    return new WorkerDatabase(dbId) as any;
  } catch (error) {
    log("ERROR", {
      uri: "kuzu_ts.database_worker_client",
      message: "Failed to create database in worker",
      error: String(error)
    });
    
    return createFileOperationError(
      `Failed to create database: ${error}`,
      "create",
      path,
      { permission_issue: false, exists: null }
    );
  }
}

/**
 * ワーカープロセスでコネクションを作成
 */
export async function createConnectionWorker(
  database: WorkerDatabase
): Promise<ConnectionResult> {
  if (!database || !(database instanceof WorkerDatabase)) {
    return createValidationError(
      "Invalid database instance",
      "database",
      String(database),
      "WorkerDatabase instance",
      "Create database using createDatabaseWorker() first"
    );
  }
  
  try {
    const connId = `conn_${Date.now()}_${Math.random()}`;
    const dbId = (database as any).dbId;
    
    log("INFO", {
      uri: "kuzu_ts.database_worker_client",
      message: "Creating connection in worker",
      connId,
      dbId
    });
    
    await sendMessage("createConnection", {
      connId,
      dbId
    });
    
    return new WorkerConnection(connId, dbId) as any;
  } catch (error) {
    log("ERROR", {
      uri: "kuzu_ts.database_worker_client",
      message: "Failed to create connection in worker",
      error: String(error)
    });
    
    return createValidationError(
      `Failed to create connection: ${error}`,
      "connection",
      "Connection creation failed",
      "Valid database connection",
      "Check database status and try again"
    );
  }
}

/**
 * ワーカーを終了
 */
export function terminateWorker(): void {
  if (worker) {
    worker.terminate();
    worker = null;
    pendingRequests.clear();
    
    log("INFO", {
      uri: "kuzu_ts.database_worker_client",
      message: "Worker terminated"
    });
  }
}