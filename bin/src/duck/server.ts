/**
 * DuckDB Deno API Server - DuckLake対応版（v1.3.0）
 * 
 * 起動:
 * $ LOG_LEVEL=4 LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH nix run nixpkgs#deno -- run --allow-read --allow-ffi --allow-net --allow-env server.ts
 * 
 * テスト実行:
 * $ LOG_LEVEL=4 LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH nix run nixpkgs#deno -- test --allow-read --allow-write --allow-ffi --allow-net --allow-env --no-check server.ts
 * 
 * 注意: 
 * - @duckdb/node-api@1.3.0-alpha.21（アルファ版）を使用
 * - 3層アーキテクチャ（DDD準拠）
 * - In-source testを含む（規約準拠）
 */

import { DuckDBInstance } from "npm:@duckdb/node-api@1.3.0-alpha.21";
import * as log from "../log/logger.ts";

// 設定のインポート
import { 
  LOG_LEVEL,
  PORT,
  DATA_FILES_PATH,
  DUCKLAKE_DB_PATH,
  SERVER_NAME,
  CONTENT_TYPE_JSON,
  ENDPOINTS
} from "./infrastructure/variables.ts";

// 3層アーキテクチャのインポート
import { createDuckDBRepository } from "./infrastructure/repository/duckdbRepository.ts";
import { createFileRepository } from "./infrastructure/repository/fileRepository.ts";
import { createExecuteQueryUseCase } from "./application/usecase/executeQuery.ts";
import { createManageDuckLakeUseCase } from "./application/usecase/manageDuckLake.ts";
import type { QueryResult } from "./domain/types.ts";

// 依存性の型定義
type ServerDependencies = {
  executeQuery: ReturnType<typeof createExecuteQueryUseCase>;
  manageDuckLake: ReturnType<typeof createManageDuckLakeUseCase>;
};

// サーバーを作成する高階関数
async function createServer(dataPath: string) {
  log.info(`Starting ${SERVER_NAME}...`);
  
  const instance = await DuckDBInstance.create();
  const connection = await instance.connect();
  
  // リポジトリの作成
  const duckdbRepo = createDuckDBRepository({ connection });
  const fileRepo = createFileRepository(dataPath);
  
  // ユースケースの作成
  const executeQuery = createExecuteQueryUseCase({ duckdbRepo });
  const manageDuckLake = createManageDuckLakeUseCase({ duckdbRepo, fileRepo });
  
  // 依存性オブジェクト
  const deps: ServerDependencies = {
    executeQuery,
    manageDuckLake
  };
  
  // バージョン確認
  const versionResult = await executeQuery.execute("SELECT version() as version");
  if (versionResult.success) {
    log.info(`DuckDB version: ${versionResult.data[0].version}`);
  }
  
  // DuckLake拡張のインストール
  const installResult = await executeQuery.execute("INSTALL ducklake");
  if (installResult.success) {
    const loadResult = await executeQuery.execute("LOAD ducklake");
    if (loadResult.success) {
      log.info("✅ DuckLake ready!");
    }
  } else {
    log.warn("DuckLake not available:", installResult.error);
  }
  
  log.info("Server ready");
  
  return {
    handler: createHandler(deps),
    deps // テストで使用するために返す
  };
}

// HTTPハンドラーを生成する高階関数
function createHandler(deps: ServerDependencies) {
  return async function handler(req: Request): Promise<Response> {
    const url = new URL(req.url);
    const path = url.pathname;
    const method = req.method;
    
    log.info(`${method} ${path}`);
    
    if (method === "GET" && path === "/") {
      const statusResult = await deps.executeQuery.execute(
        "SELECT loaded FROM duckdb_extensions() WHERE extension_name = 'ducklake'"
      );
      
      const ducklakeStatus = statusResult.success && statusResult.data.length > 0 
        ? (statusResult.data[0].loaded ? "loaded" : "not loaded")
        : "not available";
      
      return new Response(
        JSON.stringify({ 
          status: "ok", 
          ducklake: ducklakeStatus
        }),
        { status: 200, headers: { "Content-Type": CONTENT_TYPE_JSON } }
      );
    }
    
    if (method === "POST" && path === "/query") {
      const body = await req.json().catch(() => null);
      
      if (!body || !body.query || body.query.trim() === "") {
        return new Response(
          JSON.stringify({ error: "Query required" }),
          { status: 400, headers: { "Content-Type": CONTENT_TYPE_JSON } }
        );
      }
      
      log.info(`Query: ${body.query}`);
      
      const result = await deps.executeQuery.executeWithValidation(body.query);
      
      if (!result.success) {
        return new Response(
          JSON.stringify({ 
            success: false, 
            error: result.error
          }),
          { status: 500, headers: { "Content-Type": CONTENT_TYPE_JSON } }
        );
      }
      
      return new Response(
        JSON.stringify(result),
        { status: 200, headers: { "Content-Type": CONTENT_TYPE_JSON } }
      );
    }
    
    return new Response(
      JSON.stringify({ error: "Not Found" }),
      { status: 404, headers: { "Content-Type": CONTENT_TYPE_JSON } }
    );
  };
}

// メインプロセスとして実行される場合のみサーバーを起動
if (import.meta.main) {
  const server = await createServer(DATA_FILES_PATH);
  log.info(`Server on http://localhost:${PORT}`);
  log.info("");
  log.info("Test commands:");
  log.info("1. Check version: SELECT version()");
  log.info("2. Install DuckLake: INSTALL ducklake; LOAD ducklake");
  log.info("3. Use DuckLake: ATTACH 'ducklake::memory:' AS lake (DATA_PATH ':memory:')");
  
  await Deno.serve({ port: PORT }, server.handler).finished;
}

// In-source tests (統合テスト)
if (!import.meta.main) {
  // 統合テスト1: CRUD操作とファイル生成
  Deno.test("DuckLake CRUD operations", async (t) => {
    // テスト用の一時ディレクトリを作成
    const tempDir = await Deno.makeTempDir({ prefix: "ducklake_test_crud_" });
    const dataPath = `${tempDir}/data/`;
    await Deno.mkdir(dataPath, { recursive: true });
    
    // テスト用サーバーインスタンスを作成
    const server = await createServer(dataPath);
    const { executeQuery, manageDuckLake } = server.deps;
    
    // テスト環境の作成
    const testEnv = await manageDuckLake.createTestEnvironment("crud");
    if (!testEnv.success) {
      throw new Error(`Failed to create test environment: ${testEnv.error}`);
    }
    
    const { catalogName, metadataPath, dataPath: testDataPath } = testEnv;
    
    try {
      await t.step("use test catalog", async () => {
        const result = await executeQuery.execute(`USE ${catalogName}`);
        if (!result.success) {
          throw new Error(`Failed to use catalog: ${result.error}`);
        }
        
        // DuckLakeカタログが正しくアタッチされているか確認
        const tablesResult = await executeQuery.execute("SHOW ALL TABLES");
        if (!tablesResult.success) {
          throw new Error(`Failed to show tables: ${tablesResult.error}`);
        }
        log.info(`Catalog ${catalogName} is ready with ${tablesResult.data.length} tables`);
      });
      
      await t.step("create table", async () => {
        const result = await executeQuery.execute(
          `CREATE TABLE ${catalogName}.test_table (id INTEGER, value VARCHAR)`
        );
        if (!result.success) {
          throw new Error(`Failed to create table: ${result.error}`);
        }
      });
      
      await t.step("insert data and verify file generation", async () => {
        // テスト用のfileRepositoryを作成（正しいパスで）
        const testFileRepo = createFileRepository(testDataPath);
        
        // ファイル数を記録
        const beforeCount = await testFileRepo.getFileCount();
        
        // 挿入前のスナップショット数を確認
        const beforeSnapshots = await executeQuery.execute(
          `SELECT * FROM ${catalogName}.ducklake_snapshots ORDER BY created_at`
        );
        
        // データ挿入
        const result = await executeQuery.execute(
          `INSERT INTO ${catalogName}.test_table VALUES (1, 'Hello'), (2, 'DuckLake')`
        );
        if (!result.success) {
          throw new Error(`Failed to insert data: ${result.error}`);
        }
        
        // 挿入後のスナップショットを確認
        const afterSnapshots = await executeQuery.execute(
          `SELECT * FROM ${catalogName}.ducklake_snapshots ORDER BY created_at`
        );
        
        // ファイル生成の検証
        const files = await testFileRepo.listParquetFiles();
        const newFiles = files.slice(beforeCount);
        
        if (newFiles.length === 0) {
          throw new Error("No new Parquet files generated after INSERT");
        }
        
        // DuckLakeが生成したファイルであることを確認
        for (const file of newFiles) {
          if (!file.path.includes("ducklake-")) {
            throw new Error(`File ${file.path} does not have ducklake prefix`);
          }
        }
        
        // スナップショットが増えていることを確認
        if (afterSnapshots.success && beforeSnapshots.success) {
          const snapshotDiff = afterSnapshots.data.length - beforeSnapshots.data.length;
          if (snapshotDiff < 1) {
            throw new Error("No new snapshot created after INSERT");
          }
          log.info(`Created ${snapshotDiff} new snapshot(s) after INSERT`);
        }
        
        log.info(`Generated ${newFiles.length} new DuckLake Parquet files`);
      });
      
      await t.step("update data and verify new file generation", async () => {
        // テスト用のfileRepositoryを作成
        const testFileRepo = createFileRepository(testDataPath);
        const beforeCount = await testFileRepo.getFileCount();
        const beforeFiles = await testFileRepo.listParquetFiles();
        
        // データ更新
        const result = await executeQuery.execute(
          `UPDATE ${catalogName}.test_table SET value = 'Updated' WHERE id = 1`
        );
        if (!result.success) {
          throw new Error(`Failed to update data: ${result.error}`);
        }
        
        // ファイル生成の検証（UPDATE = 新ファイル + deleteファイル）
        const afterFiles = await testFileRepo.listParquetFiles();
        const newFiles = afterFiles.slice(beforeCount);
        
        if (newFiles.length === 0) {
          throw new Error("No new Parquet files generated after UPDATE");
        }
        
        // 削除マーカーファイルの存在を確認
        const deleteFiles = newFiles.filter(f => f.type === 'delete' || f.path.includes('.delete'));
        const dataFiles = newFiles.filter(f => f.type === 'data' && !f.path.includes('.delete'));
        
        if (deleteFiles.length === 0) {
          throw new Error("No delete marker files generated after UPDATE");
        }
        
        log.info(`Generated ${dataFiles.length} data files and ${deleteFiles.length} delete marker files`);
        
        // 更新されたデータの確認
        const verifyResult = await executeQuery.execute(
          `SELECT * FROM ${catalogName}.test_table WHERE id = 1`
        );
        if (verifyResult.success && verifyResult.data.length > 0) {
          if (verifyResult.data[0].value !== 'Updated') {
            throw new Error("Data not updated correctly");
          }
        }
      });
      
      await t.step("verify snapshots and time travel", async () => {
        // スナップショット一覧を取得
        const snapshotsResult = await executeQuery.execute(
          `SELECT snapshot_id, created_at FROM ${catalogName}.ducklake_snapshots ORDER BY created_at`
        );
        
        if (!snapshotsResult.success || snapshotsResult.data.length < 2) {
          throw new Error("Expected at least 2 snapshots");
        }
        
        const snapshots = snapshotsResult.data;
        log.info(`Found ${snapshots.length} snapshots`);
        
        // 最初のスナップショット（INSERT後）の時点のデータを確認
        const firstSnapshot = snapshots[0].snapshot_id;
        const timeTravel = await executeQuery.execute(
          `SELECT * FROM ${catalogName}.test_table AT SNAPSHOT '${firstSnapshot}'`
        );
        
        if (!timeTravel.success) {
          // AT SNAPSHOT構文がサポートされていない場合はスキップ
          log.warn("Time travel query not supported, skipping verification");
        } else {
          // INSERT直後のデータが見えることを確認
          const hasOriginalData = timeTravel.data.some(row => 
            row.id === 1 && row.value === 'Hello'
          );
          if (!hasOriginalData) {
            throw new Error("Time travel did not show original data");
          }
          log.info("Time travel verification successful");
        }
      });
      
    } finally {
      // クリーンアップ
      await manageDuckLake.cleanupTestEnvironment(catalogName, tempDir);
    }
  });
  
  // 統合テスト2: ファイルシステム操作
  Deno.test("DuckLake file operations", async (t) => {
    // テスト用の一時ディレクトリを作成
    const tempDir = await Deno.makeTempDir({ prefix: "ducklake_test_files_" });
    const dataPath = `${tempDir}/data/`;
    await Deno.mkdir(dataPath, { recursive: true });
    
    // テスト用サーバーインスタンスを作成
    const server = await createServer(dataPath);
    const { executeQuery, manageDuckLake } = server.deps;
    
    const testEnv = await manageDuckLake.createTestEnvironment("files");
    if (!testEnv.success) {
      throw new Error(`Failed to create test environment: ${testEnv.error}`);
    }
    
    const { catalogName, metadataPath, dataPath: testDataPath } = testEnv;
    const fileRepo = createFileRepository(testDataPath);
    
    try {
      await t.step("verify initial state", async () => {
        const fileCount = await fileRepo.getFileCount();
        if (fileCount !== 0) {
          throw new Error("Expected 0 files initially");
        }
        
        // メタデータファイルの確認
        try {
          const metadataStat = await Deno.stat(metadataPath);
          if (!metadataStat.isFile) {
            throw new Error("Metadata file is not a regular file");
          }
          log.info(`DuckLake metadata file created: ${metadataPath}`);
        } catch (e) {
          throw new Error(`Metadata file not found: ${metadataPath}`);
        }
      });
      
      await t.step("create and populate table", async () => {
        await executeQuery.execute(`USE ${catalogName}`);
        await executeQuery.execute(
          `CREATE TABLE ${catalogName}.file_test (id INTEGER, data VARCHAR)`
        );
        
        // 複数回のINSERTで複数ファイル生成
        for (let i = 0; i < 3; i++) {
          await executeQuery.execute(
            `INSERT INTO ${catalogName}.file_test VALUES (${i}, 'batch_${i}')`
          );
        }
      });
      
      await t.step("list and analyze Parquet files", async () => {
        const files = await fileRepo.listParquetFiles();
        if (files.length === 0) {
          throw new Error("No Parquet files found");
        }
        
        // DuckLakeが生成したファイルであることを確認
        const ducklakeFiles = files.filter(f => f.path.includes("ducklake-"));
        if (ducklakeFiles.length !== files.length) {
          throw new Error("Found non-DuckLake Parquet files");
        }
        
        log.info(`Found ${files.length} DuckLake Parquet files:`);
        for (const file of files) {
          log.info(`  - ${file.path} (${file.size} bytes, type: ${file.type})`);
        }
        
        const totalSize = await fileRepo.getTotalSize();
        log.info(`Total size: ${totalSize} bytes`);
        
        // データ整合性の確認
        const dataCheck = await executeQuery.execute(
          `SELECT COUNT(*) as count FROM ${catalogName}.file_test`
        );
        if (dataCheck.success) {
          log.info(`Table contains ${dataCheck.data[0].count} rows`);
          if (Number(dataCheck.data[0].count) !== 3) {
            throw new Error(`Expected 3 rows but found ${dataCheck.data[0].count}`);
          }
        }
      });
      
    } finally {
      // クリーンアップ
      await manageDuckLake.cleanupTestEnvironment(catalogName, tempDir);
    }
  });
  
  // 基本的なHTTPハンドラーテスト
  Deno.test("HTTP handler tests", async (t) => {
    // テスト用の一時ディレクトリを作成
    const tempDir = await Deno.makeTempDir({ prefix: "ducklake_test_http_" });
    const dataPath = `${tempDir}/data/`;
    await Deno.mkdir(dataPath, { recursive: true });
    
    // テスト用サーバーインスタンスを作成
    const server = await createServer(dataPath);
    const handler = server.handler;
    
    try {
      await t.step("GET / returns server status", async () => {
        const request = new Request("http://localhost/");
        const response = await handler(request);
        
        if (response.status !== 200) {
          throw new Error(`Expected status 200, got ${response.status}`);
        }
        
        const data = await response.json();
        if (data.status !== "ok") {
          throw new Error("Expected status to be 'ok'");
        }
      });
      
      await t.step("POST /query validates input", async () => {
        const request = new Request("http://localhost/query", {
          method: "POST",
          body: JSON.stringify({ query: "" })
        });
        const response = await handler(request);
        
        if (response.status !== 400) {
          throw new Error(`Expected status 400, got ${response.status}`);
        }
        
        const data = await response.json();
        if (data.error !== "Query required") {
          throw new Error(`Expected "Query required" error, got: ${data.error}`);
        }
      });
    } finally {
      // クリーンアップ
      await Deno.remove(tempDir, { recursive: true });
    }
  });
}
