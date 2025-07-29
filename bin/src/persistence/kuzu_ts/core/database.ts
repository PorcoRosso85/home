import { Database, Connection } from "kuzu";
import type { DatabaseResult, ConnectionResult } from "./result_types.ts";
import type { FileOperationError, ValidationError } from "./errors.ts";
import { dirname, join } from "jsr:@std/path@^1.0.0";
import { log } from "log_ts/mod.ts";

export interface DatabaseOptions {
  testUnique?: boolean;
}

export function createDatabase(
  path: string,
  options: DatabaseOptions = {}
): DatabaseResult {
  const { testUnique = false } = options;
  
  try {
    // Validate path
    if (!path || typeof path !== "string") {
      const error: ValidationError = {
        type: "ValidationError",
        message: "Database path must be a non-empty string",
        field: "path",
        value: String(path),
        constraint: "non-empty string",
        suggestion: "Provide a valid file path or ':memory:' for in-memory database"
      };
      return error;
    }

    // In-memory with testUnique should always create new instance
    if (path === ":memory:" && testUnique) {
      log("INFO", {
        uri: "kuzu_ts.database",
        message: "Creating in-memory database with testUnique"
      });
      return new Database(":memory:");
    }
    
    // For persistent databases, handle directory creation
    let finalPath = path;
    if (path !== ":memory:") {
      try {
        // Check if path points to an existing directory
        try {
          const stat = Deno.statSync(path);
          if (stat.isDirectory) {
            // If existing directory is passed, create db.kuzu file inside it
            finalPath = join(path, "db.kuzu");
            log("DEBUG", {
              uri: "kuzu_ts.database",
              message: "Directory path provided, using db.kuzu inside",
              originalPath: path,
              finalPath
            });
          }
        } catch {
          // Path doesn't exist yet, create parent directory
          const parentDir = dirname(path);
          try {
            Deno.mkdirSync(parentDir, { recursive: true });
            log("DEBUG", {
              uri: "kuzu_ts.database",
              message: "Created parent directory",
              parentDir
            });
          } catch (mkdirError) {
            // Ignore error if directory already exists
            if (!(mkdirError instanceof Error && mkdirError.message.includes("exists"))) {
              throw mkdirError;
            }
          }
          // Use the path as is (it will be treated as a file)
          finalPath = path;
        }
      } catch (e) {
        const errorMessage = e instanceof Error ? e.message : "Failed to create parent directory";
        log("ERROR", {
          uri: "kuzu_ts.database",
          message: "Failed to create parent directory",
          error: errorMessage,
          path
        });
        const error: FileOperationError = {
          type: "FileOperationError",
          message: errorMessage,
          operation: "create",
          file_path: path,
          permission_issue: e instanceof Error && e.message.includes("permission"),
          exists: false
        };
        return error;
      }
    }
    
    // Create new database
    log("INFO", {
      uri: "kuzu_ts.database",
      message: path === ":memory:" ? "Creating in-memory database" : "Creating persistent database",
      path: finalPath
    });
    const db = new Database(finalPath);
    
    return db;
  } catch (e) {
    // Handle file operation errors
    const errorMessage = e instanceof Error ? e.message : "Failed to create database";
    log("ERROR", {
      uri: "kuzu_ts.database",
      message: "Database creation failed",
      error: errorMessage,
      path
    });
    const error: FileOperationError = {
      type: "FileOperationError",
      message: errorMessage,
      operation: "create",
      file_path: path,
      permission_issue: e instanceof Error && e.message.includes("permission"),
      exists: false
    };
    return error;
  }
}

export function createConnection(db: Database): ConnectionResult {
  try {
    // Validate database instance
    if (!db || typeof db !== "object") {
      log("ERROR", {
        uri: "kuzu_ts.database",
        message: "Invalid database instance provided for connection",
        dbType: typeof db
      });
      const error: ValidationError = {
        type: "ValidationError",
        message: "Invalid database instance",
        field: "db",
        value: String(db),
        constraint: "valid Database instance",
        suggestion: "Pass a valid Database instance created by createDatabase"
      };
      return error;
    }

    log("INFO", {
      uri: "kuzu_ts.database",
      message: "Creating database connection"
    });
    return new Connection(db);
  } catch (e) {
    // Handle connection errors
    const errorMessage = e instanceof Error ? e.message : "Failed to create connection";
    log("ERROR", {
      uri: "kuzu_ts.database",
      message: "Connection creation failed",
      error: errorMessage
    });
    const error: FileOperationError = {
      type: "FileOperationError",
      message: errorMessage,
      operation: "connect",
      file_path: "database connection",
      permission_issue: false,
      exists: true
    };
    return error;
  }
}

