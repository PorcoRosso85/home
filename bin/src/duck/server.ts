/**
 * DuckDB Deno API Server - 最小構成（デモデータなし）
 * Deno標準APIのみ使用
 * 
 * 起動方法:
 * --------
 * 
 * 通常の起動:
 * $ deno run --allow-read --allow-ffi --allow-net --allow-env server.ts
 * 
 * デバッグモード:
 * $ LOG_LEVEL=4 deno run --allow-read --allow-ffi --allow-net --allow-env server.ts
 * 
 * Nixでの起動:
 * $ LOG_LEVEL=4 LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH nix run nixpkgs#deno -- run --allow-read --allow-ffi --allow-net --allow-env server.ts
 * 
 * テスト:
 * ------
 * 
 * ヘルスチェック:
 * $ curl http://localhost:8000/
 * 
 * クエリ実行:
 * $ curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query": "SELECT 1"}'
 * $ curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query": "SELECT 42 as answer, '"'"'hello'"'"' as greeting"}'
 */

import { DuckDBInstance } from "npm:@duckdb/node-api";
import * as log from "../log/logger.ts";

log.info("Starting DuckDB Deno API Server (Minimal)...");

// DuckDB接続設定
let connection: any;

try {
  log.info("Initializing DuckDB...");
  const instance = await DuckDBInstance.create();
  connection = await instance.connect();
  
  // 接続テスト
  log.info("Testing connection with SELECT 1...");
  const testResult = await connection.runAndReadAll("SELECT 1 as test");
  const testRows = testResult.getRows();
  log.info(`Connection test result: ${JSON.stringify(testRows)}`);
  
  log.info("DuckDB initialized successfully");
} catch (err) {
  log.error("Failed to initialize DuckDB", err);
  log.error("Error details:", {
    message: err.message,
    stack: err.stack,
    name: err.name
  });
  Deno.exit(1);
}

// リクエストハンドラー
async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);
  const path = url.pathname;
  const method = req.method;
  
  log.info(`${method} ${path}`);
  
  // ヘルスチェック
  if (method === "GET" && path === "/") {
    return new Response(
      JSON.stringify({ 
        status: "ok", 
        message: "DuckDB API Server is running" 
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }
    );
  }
  
  // クエリ実行
  if (method === "POST" && path === "/query") {
    try {
      // リクエストボディ取得
      let body: any;
      try {
        body = await req.json();
        log.debug("Request body:", body);
      } catch (parseErr) {
        log.error("JSON parse error:", parseErr);
        return new Response(
          JSON.stringify({ error: "Invalid JSON" }),
          {
            status: 400,
            headers: { "Content-Type": "application/json" }
          }
        );
      }
      
      const { query } = body;
      
      if (!query || typeof query !== 'string') {
        log.warn("Missing or invalid query");
        return new Response(
          JSON.stringify({ error: "Query string is required" }),
          {
            status: 400,
            headers: { "Content-Type": "application/json" }
          }
        );
      }
      
      log.info(`Executing query: ${query}`);
      
      try {
        // クエリ実行
        const reader = await connection.runAndReadAll(query);
        log.debug("Query executed successfully");
        
        const rows = reader.getRows();
        log.debug(`Retrieved ${rows.length} rows`);
        
        // カラム名取得
        const columnCount = reader.columnCount;
        log.debug(`Column count: ${columnCount}`);
        
        const columnNames: string[] = [];
        for (let i = 0; i < columnCount; i++) {
          try {
            const colName = reader.columnName(i);
            columnNames.push(colName || `column_${i}`);
          } catch (colErr) {
            log.error(`Error getting column ${i} name:`, colErr);
            columnNames.push(`column_${i}`);
          }
        }
        
        log.debug(`Column names: ${JSON.stringify(columnNames)}`);
        
        // 結果を整形
        const result = rows.map((row: any[]) => {
          const obj: Record<string, unknown> = {};
          columnNames.forEach((name: string, index: number) => {
            obj[name] = row[index];
          });
          return obj;
        });
        
        const response = {
          success: true,
          data: result,
          rowCount: rows.length,
          columns: columnNames
        };
        
        return new Response(
          JSON.stringify(response),
          {
            status: 200,
            headers: { "Content-Type": "application/json" }
          }
        );
        
      } catch (queryError) {
        log.error("Query execution error:", queryError);
        log.error("Error details:", {
          message: queryError.message,
          stack: queryError.stack,
          name: queryError.name
        });
        throw queryError;
      }
      
    } catch (error) {
      log.error("Request handler error:", error);
      return new Response(
        JSON.stringify({ 
          success: false,
          error: error.message || "Internal server error"
        }),
        {
          status: 500,
          headers: { "Content-Type": "application/json" }
        }
      );
    }
  }
  
  // 404
  return new Response(
    JSON.stringify({ error: "Not Found" }),
    {
      status: 404,
      headers: { "Content-Type": "application/json" }
    }
  );
}

// サーバー起動
const port = 8000;
log.info(`Server listening on http://localhost:${port}`);
log.info("Endpoints:");
log.info("  GET  / - Health check");
log.info("  POST /query - Execute SQL queries");

// Deno標準HTTPサーバー
await Deno.serve({ port }, handler).finished;
