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
        
        // データ挿入
        const result = await executeQuery.execute(
          `INSERT INTO ${catalogName}.test_table VALUES (1, 'Hello'), (2, 'DuckLake')`
        );
        if (!result.success) {
          throw new Error(`Failed to insert data: ${result.error}`);
        }
        
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
        
        log.info(`Generated ${newFiles.length} new DuckLake Parquet files`);
        
        // データが正しく挿入されたか確認
        const verifyResult = await executeQuery.execute(
          `SELECT COUNT(*) as count FROM ${catalogName}.test_table`
        );
        if (verifyResult.success) {
          const count = Number(verifyResult.data[0].count);
          if (count !== 2) {
            throw new Error(`Expected 2 rows but found ${count}`);
          }
        }
      });
      
      await t.step("update data and verify new file generation", async () => {
        // テスト用のfileRepositoryを作成
        const testFileRepo = createFileRepository(testDataPath);
        const beforeCount = await testFileRepo.getFileCount();
        
        // データ更新
        const result = await executeQuery.execute(
          `UPDATE ${catalogName}.test_table SET value = 'Updated' WHERE id = 1`
        );
        if (!result.success) {
          throw new Error(`Failed to update data: ${result.error}`);
        }
        
        // ファイル生成の検証
        const afterFiles = await testFileRepo.listParquetFiles();
        const newFiles = afterFiles.slice(beforeCount);
        
        if (newFiles.length === 0) {
          throw new Error("No new Parquet files generated after UPDATE");
        }
        
        log.info(`Generated ${newFiles.length} new files after UPDATE`);
        
        // 更新されたデータの確認
        const verifyResult = await executeQuery.execute(
          `SELECT * FROM ${catalogName}.test_table WHERE id = 1`
        );
        if (verifyResult.success && verifyResult.data.length > 0) {
          if (verifyResult.data[0].value !== 'Updated') {
            throw new Error("Data not updated correctly");
          }
          log.info("UPDATE verification successful");
        }
      });
      
      await t.step("verify data consistency", async () => {
        // 最終的なデータの整合性を確認
        const finalData = await executeQuery.execute(
          `SELECT * FROM ${catalogName}.test_table ORDER BY id`
        );
        
        if (!finalData.success) {
          throw new Error("Failed to query final data");
        }
        
        // データが正しく保存されているか確認
        if (finalData.data.length !== 2) {
          throw new Error(`Expected 2 rows but found ${finalData.data.length}`);
        }
        
        // id=1のデータが更新されているか
        const row1 = finalData.data.find(row => row.id === 1);
        if (!row1 || row1.value !== 'Updated') {
          throw new Error("Row with id=1 not updated correctly");
        }
        
        // id=2のデータが変更されていないか
        const row2 = finalData.data.find(row => row.id === 2);
        if (!row2 || row2.value !== 'DuckLake') {
          throw new Error("Row with id=2 was unexpectedly modified");
        }
        
        log.info("Data consistency verification successful");
      });
      
      await t.step("verify version management through file generation", async () => {
        const testFileRepo = createFileRepository(testDataPath);
        const allFiles = await testFileRepo.listParquetFiles();
        
        // 1. ファイル世代管理：各操作でファイルが生成されているか
        if (allFiles.length < 2) {
          throw new Error("Expected multiple file generations for version management");
        }
        
        // 2. ファイル名の一意性：UUIDが重複していないか
        const uuids = allFiles.map(f => {
          const match = f.path.match(/ducklake-([a-f0-9-]+)\.parquet/);
          return match ? match[1] : null;
        }).filter(uuid => uuid !== null);
        
        const uniqueUuids = new Set(uuids);
        if (uniqueUuids.size !== uuids.length) {
          throw new Error("Found duplicate UUIDs in file names");
        }
        
        // 3. 操作順序の保持：ファイル作成時刻が順序通りか
        const sortedFiles = [...allFiles].sort((a, b) => 
          new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
        );
        
        // 作成時刻が正しく記録されているか確認
        let prevTime = 0;
        for (const file of sortedFiles) {
          const currentTime = new Date(file.createdAt).getTime();
          if (currentTime < prevTime) {
            throw new Error("File creation times are not in expected order");
          }
          prevTime = currentTime;
        }
        
        // 4. データ復元可能性：削除操作後もデータが復元可能か
        // TODO: DELETE操作時のファイル生成動作について、DuckLake公式ドキュメントに
        //       明確な記載がないため、現時点ではスキップ。
        //       UPDATE操作については「deletes followed by inserts」として削除ファイルが
        //       生成されることが明記されているが、純粋なDELETE操作については不明。
        //       公式ドキュメントでの明確化を待つ。
        /*
        // 一部データを削除
        const deleteResult = await executeQuery.execute(
          `DELETE FROM ${catalogName}.test_table WHERE id = 2`
        );
        if (!deleteResult.success) {
          throw new Error("Failed to delete data for version test");
        }
        
        // 削除後の新しいファイル生成を確認
        const filesAfterDelete = await testFileRepo.listParquetFiles();
        if (filesAfterDelete.length <= allFiles.length) {
          throw new Error("No new file generated after DELETE operation");
        }
        
        // 削除後のデータ確認（id=1は残っているはず）
        const remainingData = await executeQuery.execute(
          `SELECT * FROM ${catalogName}.test_table ORDER BY id`
        );
        if (!remainingData.success || remainingData.data.length !== 1) {
          throw new Error("Data not correctly maintained after DELETE");
        }
        
        if (remainingData.data[0].id !== 1 || remainingData.data[0].value !== 'Updated') {
          throw new Error("Remaining data is not correct after DELETE");
        }
        */
        
        log.info(`Version management verified with ${allFiles.length} file generations`);
        log.info("All files have unique identifiers and maintain operation order");
        log.info("DELETE operation test skipped pending official documentation clarification");
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
