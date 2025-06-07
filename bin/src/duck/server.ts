/**
 * DuckDB Deno API Server - DuckLake対応版（v1.3.0）
 * 
 * 起動:
 * $ LOG_LEVEL=4 LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH nix run nixpkgs#deno -- run --allow-read --allow-ffi --allow-net --allow-env server.ts
 * 
 * テスト実行:
 * $ LOG_LEVEL=4 LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH nix run nixpkgs#deno -- test --allow-read --allow-ffi --allow-net --allow-env server.ts
 * 
 * 注意: 
 * - @duckdb/node-api@1.3.0-alpha.21（アルファ版）を使用
 * - または npm:duckdb@1.3.0（旧API、安定版）に変更可能
 * - In-source testを含む（規約準拠）
 */

// アルファ版を試す（DuckLake対応の可能性が高い）
import { DuckDBInstance } from "npm:@duckdb/node-api@1.3.0-alpha.21";

// 旧APIを使う場合（安定版）
// import duckdb from "npm:duckdb@1.3.0";

import * as log from "../log/logger.ts";

log.info("Starting DuckDB Server with DuckLake (v1.3.0+)...");

let connection: any;

try {
  const instance = await DuckDBInstance.create();
  connection = await instance.connect();
  
  // バージョン確認
  const versionResult = await connection.runAndReadAll("SELECT version() as version");
  const version = versionResult.getRows()[0][0];
  log.info(`DuckDB version: ${version}`);
  
  // DuckLake設定
  try {
    await connection.run("INSTALL ducklake");
    await connection.run("LOAD ducklake");
    log.info("✅ DuckLake ready!");
  } catch (err) {
    log.warn("DuckLake not available:", err.message);
  }
  
  log.info("Server ready");
} catch (err) {
  log.error("Failed to initialize:", err);
  Deno.exit(1);
}

async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);
  const path = url.pathname;
  const method = req.method;
  
  log.info(`${method} ${path}`);
  
  if (method === "GET" && path === "/") {
    let ducklakeStatus = "unknown";
    try {
      const result = await connection.runAndReadAll(
        "SELECT loaded FROM duckdb_extensions() WHERE extension_name = 'ducklake'"
      );
      const rows = result.getRows();
      ducklakeStatus = rows.length > 0 && rows[0][0] ? "loaded" : "not loaded";
    } catch {
      ducklakeStatus = "not available";
    }
    
    return new Response(
      JSON.stringify({ 
        status: "ok", 
        ducklake: ducklakeStatus
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }
  
  if (method === "POST" && path === "/query") {
    try {
      const body = await req.json();
      const { query } = body;
      
      if (!query) {
        return new Response(
          JSON.stringify({ error: "Query required" }),
          { status: 400, headers: { "Content-Type": "application/json" } }
        );
      }
      
      log.info(`Query: ${query}`);
      
      const reader = await connection.runAndReadAll(query);
      const rows = reader.getRows();
      const columnCount = reader.columnCount;
      
      const columnNames: string[] = [];
      for (let i = 0; i < columnCount; i++) {
        columnNames.push(reader.columnName(i) || `col_${i}`);
      }
      
      const result = rows.map((row: any[]) => {
        const obj: Record<string, unknown> = {};
        columnNames.forEach((name, idx) => obj[name] = row[idx]);
        return obj;
      });
      
      return new Response(
        JSON.stringify({
          success: true,
          data: result,
          rowCount: rows.length,
          columns: columnNames
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
      
    } catch (error) {
      log.error("Query error:", error);
      return new Response(
        JSON.stringify({ 
          success: false, 
          error: error.message
        }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    }
  }
  
  return new Response(
    JSON.stringify({ error: "Not Found" }),
    { status: 404, headers: { "Content-Type": "application/json" } }
  );
}

const port = 8000;

// メインプロセスとして実行される場合のみサーバーを起動
if (import.meta.main) {
  log.info(`Server on http://localhost:${port}`);
  log.info("");
  log.info("Test commands:");
  log.info("1. Check version: SELECT version()");
  log.info("2. Install DuckLake: INSTALL ducklake; LOAD ducklake");
  log.info("3. Use DuckLake: ATTACH 'ducklake::memory:' AS lake (DATA_PATH ':memory:')");
  
  await Deno.serve({ port }, handler).finished;
}

// In-source tests (規約準拠: 実装ファイル内テスト)
if (!import.meta.main) {
  // テスト用の型定義（共用体型）
  type TestResult = 
    | { success: true; message: string }
    | { success: false; error: string };
  
  // テスト用のモックハンドラー関数
  async function testHandler(method: string, path: string, body?: any): Promise<TestResult> {
    const request = new Request(`http://localhost${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    
    const response = await handler(request);
    const data = await response.json();
    
    if (response.status >= 400) {
      return { success: false, error: data.error || "Request failed" };
    }
    
    return { success: true, message: JSON.stringify(data) };
  }
  
  Deno.test("GET / returns server status", async () => {
    const result = await testHandler("GET", "/");
    
    if (!result.success) {
      throw new Error(`Status check failed: ${result.error}`);
    }
    
    const data = JSON.parse(result.message);
    if (data.status !== "ok") {
      throw new Error("Expected status to be 'ok'");
    }
  });
  
  Deno.test("POST /query with empty query returns error", async () => {
    const result = await testHandler("POST", "/query", {});
    
    if (result.success) {
      throw new Error("Expected error for empty query");
    }
    
    if (result.error !== "Query required") {
      throw new Error(`Unexpected error: ${result.error}`);
    }
  });
  
  Deno.test("POST /query executes valid query", async () => {
    const result = await testHandler("POST", "/query", {
      query: "SELECT 1 as test_value"
    });
    
    if (!result.success) {
      throw new Error(`Query execution failed: ${result.error}`);
    }
    
    const data = JSON.parse(result.message);
    if (!data.success || data.rowCount !== 1) {
      throw new Error("Query did not return expected result");
    }
  });
  
  Deno.test("Undefined route returns 404", async () => {
    const result = await testHandler("GET", "/undefined");
    
    if (result.success) {
      throw new Error("Expected 404 error");
    }
    
    if (result.error !== "Not Found") {
      throw new Error(`Unexpected error: ${result.error}`);
    }
  });
}
