/**
 * 動的import版のKuzuDBデータベース実装
 * 
 * kuzu/queryの実装を参考に、動的importでパニックを回避
 */
import type { DatabaseResult, ConnectionResult } from "./result_types.ts";
import { createValidationError, createFileOperationError } from "./errors.ts";
import { log } from "log_ts/mod.ts";
import { DEFAULT_DB_MAX_SIZE } from "./variables.ts";
import { existsSync } from "jsr:@std/fs@^1.0.0";

// KuzuDBモジュールのキャッシュ
let kuzuModule: any = null;

/**
 * KuzuDBモジュールを動的にロード
 */
async function loadKuzu() {
  if (!kuzuModule) {
    try {
      kuzuModule = await import("npm:kuzu");
      log("DEBUG", {
        uri: "kuzu_ts.database_dynamic",
        message: "KuzuDB module loaded dynamically"
      });
    } catch (e) {
      log("ERROR", {
        uri: "kuzu_ts.database_dynamic",
        message: "Failed to load KuzuDB module",
        error: String(e)
      });
      throw e;
    }
  }
  return kuzuModule;
}

/**
 * データベース作成（動的import版）
 */
export async function createDatabaseDynamic(
  path: string,
  options: { bufferPoolSize?: number } = {}
): Promise<DatabaseResult> {
  // バリデーション
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
    const kuzu = await loadKuzu();
    
    if (path === ":memory:") {
      log("INFO", {
        uri: "kuzu_ts.database_dynamic",
        message: "Creating in-memory database (dynamic)",
        path: path
      });
      
      return new kuzu.Database(":memory:", options.bufferPoolSize);
    } else {
      // ディレクトリ作成
      const dir = path.substring(0, path.lastIndexOf("/"));
      if (dir && !existsSync(dir)) {
        try {
          Deno.mkdirSync(dir, { recursive: true });
          log("DEBUG", {
            uri: "kuzu_ts.database_dynamic",
            message: "Created directory for database",
            directory: dir
          });
        } catch (e) {
          log("ERROR", {
            uri: "kuzu_ts.database_dynamic",
            message: "Failed to create directory",
            error: String(e),
            directory: dir
          });
          return createFileOperationError(
            `Failed to create directory: ${e}`,
            "mkdir",
            dir,
            {
              permission_issue: e instanceof Deno.errors.PermissionDenied,
              exists: false
            }
          );
        }
      }
      
      log("INFO", {
        uri: "kuzu_ts.database_dynamic",
        message: "Creating persistent database (dynamic)",
        path: path,
        maxDBSize: DEFAULT_DB_MAX_SIZE
      });
      
      return new kuzu.Database(path, DEFAULT_DB_MAX_SIZE);
    }
  } catch (e) {
    log("ERROR", {
      uri: "kuzu_ts.database_dynamic",
      message: "Failed to create database",
      error: String(e),
      path: path
    });
    
    return createFileOperationError(
      `Failed to create database: ${e}`,
      "create",
      path,
      {
        permission_issue: false,
        exists: null
      }
    );
  }
}

/**
 * コネクション作成（動的import版）
 */
export async function createConnectionDynamic(database: any): Promise<ConnectionResult> {
  if (!database || typeof database !== "object") {
    log("ERROR", {
      uri: "kuzu_ts.database_dynamic",
      message: "Invalid database instance provided for connection",
      dbType: typeof database
    });
    
    return createValidationError(
      "Invalid database instance provided",
      "database",
      String(database),
      "Valid Database instance",
      "Create database using createDatabaseDynamic() first"
    );
  }

  try {
    const kuzu = await loadKuzu();
    
    log("INFO", {
      uri: "kuzu_ts.database_dynamic",
      message: "Creating database connection (dynamic)"
    });
    
    return new kuzu.Connection(database);
  } catch (e) {
    log("ERROR", {
      uri: "kuzu_ts.database_dynamic",
      message: "Failed to create connection",
      error: String(e)
    });
    
    return createValidationError(
      `Failed to create connection: ${e}`,
      "connection",
      "Connection creation failed",
      "Valid database connection",
      "Check database status and try again"
    );
  }
}

/**
 * データベースをクリーンに閉じる
 */
export async function closeDatabaseSafe(database: any): Promise<void> {
  if (database && typeof database.close === "function") {
    try {
      await database.close();
      log("DEBUG", {
        uri: "kuzu_ts.database_dynamic",
        message: "Database closed safely"
      });
    } catch (e) {
      log("WARN", {
        uri: "kuzu_ts.database_dynamic",
        message: "Error closing database",
        error: String(e)
      });
    }
  }
}

/**
 * コネクションをクリーンに閉じる
 */
export async function closeConnectionSafe(connection: any): Promise<void> {
  if (connection && typeof connection.close === "function") {
    try {
      await connection.close();
      log("DEBUG", {
        uri: "kuzu_ts.database_dynamic",
        message: "Connection closed safely"
      });
    } catch (e) {
      log("WARN", {
        uri: "kuzu_ts.database_dynamic",
        message: "Error closing connection",
        error: String(e)
      });
    }
  }
}