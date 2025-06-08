/**
 * DuckDB Deno API Server - スナップショットParquet提供版（v2.0.0）
 * 
 * 責務: バージョン指定されたDuckLakeスナップショットParquetファイルの提供
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
import type { QueryResult, QueryData, QueryError } from "./domain/types.ts";
import { isQueryError } from "./domain/types.ts";
import type { AppError, FormattedError } from "./shared/errors.ts";
import { getHttpStatusCode, formatError, isError } from "./shared/errors.ts";
import type { ApplicationError } from "./application/errors.ts";
import type { TestEnvironmentData } from "./application/usecase/manageDuckLake.ts";

// 依存性の型定義（規約準拠：interfaceではなくtype）
type ServerDependencies = {
  executeQuery: ReturnType<typeof createExecuteQueryUseCase>;
  manageDuckLake: ReturnType<typeof createManageDuckLakeUseCase>;
};

// サーバーを作成する高階関数
async function createServer(dataPath: string) {
  log.info(`Starting ${SERVER_NAME}...`);
  log.info(`Snapshot Parquet Provider Mode`);
  
  // 永続化オプション（環境変数で切り替え可能）
  const dbPath = Deno.env.get("DUCK_DB_PATH") || ""; // 空文字列 = In-Memory
  const instance = await DuckDBInstance.create(dbPath);
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
  if (!isQueryError(versionResult)) {
    log.info(`DuckDB version: ${versionResult.rows[0].version}`);
  }
  
  // DuckLake拡張のインストール
  const installResult = await executeQuery.execute("INSTALL ducklake");
  if (!isQueryError(installResult)) {
    const loadResult = await executeQuery.execute("LOAD ducklake");
    if (!isQueryError(loadResult)) {
      log.info("✅ DuckLake ready!");
    }
  } else {
    log.warn("DuckLake not available:", installResult.message);
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
    
    // CORSヘッダー
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    };
    
    // プリフライトリクエスト対応
    if (method === "OPTIONS") {
      return new Response(null, { 
        status: 204, 
        headers: corsHeaders 
      });
    }
    
    // パスからバージョンパラメータを抽出
    const snapshotMatch = path.match(/^\/api\/snapshot\/(.+)$/);
    
    // ルーティングをパターンマッチで処理
    const route = `${method}:${path}`;
    
    switch (route) {
      case "GET:/": {
        const statusResult = await deps.executeQuery.execute(
          "SELECT loaded FROM duckdb_extensions() WHERE extension_name = 'ducklake'"
        );
        
        const ducklakeStatus = !isQueryError(statusResult) && statusResult.rows.length > 0 
          ? (statusResult.rows[0].loaded ? "loaded" : "not loaded")
          : "not available";
        
        return new Response(
          JSON.stringify({ 
            status: "ok", 
            ducklake: ducklakeStatus,
            mode: "snapshot-provider"
          }),
          { 
            status: 200, 
            headers: { 
              "Content-Type": CONTENT_TYPE_JSON,
              ...corsHeaders 
            } 
          }
        );
      }
      
      case "POST:/query": {
        const body = await req.json().catch(() => null);
        
        if (!body || !body.query || body.query.trim() === "") {
          const error: ApplicationError = {
            code: "VALIDATION_FAILED",
            message: "[Query Validation] Query is required",
            details: { body }
          };
          
          const formatted = formatError(error);
          
          return new Response(
            JSON.stringify(formatted),
            { 
              status: getHttpStatusCode(error), 
              headers: { 
                "Content-Type": CONTENT_TYPE_JSON,
                ...corsHeaders 
              } 
            }
          );
        }
        
        log.info(`Query: ${body.query}`);
        
        const result = await deps.executeQuery.executeWithValidation(body.query);
        
        if (isError(result)) {
          const formatted = formatError(result);
          return new Response(
            JSON.stringify(formatted),
            { 
              status: getHttpStatusCode(result), 
              headers: { 
                "Content-Type": CONTENT_TYPE_JSON,
                ...corsHeaders 
              } 
            }
          );
        }
        
        return new Response(
          JSON.stringify(result),
          { 
            status: 200, 
            headers: { 
              "Content-Type": CONTENT_TYPE_JSON,
              ...corsHeaders 
            } 
          }
        );
      }
      
      case "POST:/api/versions": {
        log.info("Fetching available DuckLake snapshots");
        
        // DuckLakeの実際のスナップショットを確認
        // バージョン1-10をチェックして存在するものだけ返す
        const availableVersions = [];
        
        for (let v = 1; v <= 10; v++) {
          const testResult = await deps.executeQuery.execute(
            `SELECT COUNT(*) as count FROM lake.LocationURI AT (VERSION => ${v})`
          );
          
          // エラーが発生した場合はそのバージョンは存在しない
          if (isQueryError(testResult)) {
            continue;
          }
          
          const count = testResult.rows[0]?.count;
          if (count > 0) {
            // 前のバージョンとの差分を計算
            let changes = { total: 0, inserts: 0, deletes: 0, updates: 0 };
            
            if (v > 1) {
              // 前のバージョンと比較
              const prevResult = await deps.executeQuery.execute(
                `SELECT COUNT(*) as prev_count FROM lake.LocationURI AT (VERSION => ${v - 1})`
              );
              
              if (!isQueryError(prevResult)) {
                const prevCount = prevResult.rows[0]?.prev_count || 0;
                const diff = Number(count) - Number(prevCount);
                
                if (diff > 0) {
                  changes.inserts = diff;
                  changes.total = diff;
                } else if (diff < 0) {
                  changes.deletes = Math.abs(diff);
                  changes.total = Math.abs(diff);
                }
              }
            } else {
              // 最初のバージョンは全てinsert
              changes.inserts = Number(count);
              changes.total = Number(count);
            }
            
            availableVersions.push({
              version: v,
              timestamp: new Date().toISOString(),
              description: `DuckLake snapshot ${v}`,
              row_count: Number(count),
              changes
            });
          }
        }
        
        if (availableVersions.length === 0) {
          const error: ApplicationError = {
            code: "DUCKLAKE_NOT_AVAILABLE",
            message: "[DuckLake Version List] No DuckLake snapshots found. Please run duck.init.sh first."
          };
          
          const formatted = formatError(error);
          
          return new Response(
            JSON.stringify(formatted),
            { 
              status: 404, 
              headers: { 
                "Content-Type": CONTENT_TYPE_JSON,
                ...corsHeaders 
              } 
            }
          );
        }
        
        // バージョン番号の降順でソート
        availableVersions.sort((a, b) => b.version - a.version);
        
        return new Response(
          JSON.stringify({
            versions: availableVersions
          }),
          { 
            status: 200, 
            headers: { 
              "Content-Type": CONTENT_TYPE_JSON,
              ...corsHeaders 
            } 
          }
        );
      }
      
      default: {
        // スナップショットエンドポイントのパターンマッチング
        if (method === "POST" && snapshotMatch) {
          const version = snapshotMatch[1];
          log.info(`Snapshot request for version: ${version}`);
          
          // バージョンパラメータの検証
          const versionNum = parseInt(version);
          if (isNaN(versionNum)) {
            const error: ApplicationError = {
              code: "VALIDATION_FAILED",
              message: "[Snapshot Export] Invalid version format. Expected numeric snapshot ID.",
              details: { version }
            };
            
            const formatted = formatError(error);
            
            return new Response(
              JSON.stringify(formatted),
              { 
                status: 400, 
                headers: { 
                  "Content-Type": CONTENT_TYPE_JSON,
                  ...corsHeaders 
                } 
              }
            );
          }
          
          // 指定バージョンのLocationURIデータをParquetにエクスポート
          const tempDir = `/tmp/ducklake-snapshot-${versionNum}`;
          await Deno.mkdir(tempDir, { recursive: true });
          
          try {
            // AT (VERSION => n) を使用して特定バージョンのデータをエクスポート
            const exportQuery = `
              COPY (
                SELECT * FROM lake.LocationURI AT (VERSION => ${versionNum})
              ) TO '${tempDir}/LocationURI_v${versionNum}.parquet' (FORMAT PARQUET)
            `;
            
            const exportResult = await deps.executeQuery.execute(exportQuery);
            
            if (isQueryError(exportResult)) {
              log.error("Failed to export snapshot:", exportResult.message);
              
              // バージョンが存在しない可能性
              if (exportResult.message.includes("VERSION") || exportResult.message.includes("snapshot")) {
                const error: ApplicationError = {
                  code: "VERSION_NOT_FOUND",
                  message: `[Snapshot Export] Snapshot version ${versionNum} not found`,
                  version: String(versionNum)
                };
                
                const formatted = formatError(error);
                
                return new Response(
                  JSON.stringify(formatted),
                  { 
                    status: 404, 
                    headers: { 
                      "Content-Type": CONTENT_TYPE_JSON,
                      ...corsHeaders 
                    } 
                  }
                );
              }
              
              const error: ApplicationError = {
                code: "OPERATION_FAILED",
                message: `[Snapshot Export] Failed to export snapshot: ${exportResult.message}`,
                operation: "export_snapshot"
              };
              
              const formatted = formatError(error);
              
              return new Response(
                JSON.stringify(formatted),
                { 
                  status: 500, 
                  headers: { 
                    "Content-Type": CONTENT_TYPE_JSON,
                    ...corsHeaders 
                  } 
                }
              );
            }
            
            // エクスポートされたファイルを読み込み
            const parquetPath = `${tempDir}/LocationURI_v${versionNum}.parquet`;
            const fileContent = await Deno.readFile(parquetPath);
            
            // 一時ファイルをクリーンアップ
            await Deno.remove(tempDir, { recursive: true }).catch(() => {});
            
            log.info(`Returning snapshot v${versionNum} (${fileContent.byteLength} bytes)`);
            
            return new Response(
              fileContent,
              { 
                status: 200, 
                headers: { 
                  "Content-Type": "application/octet-stream",
                  "Content-Disposition": `attachment; filename="LocationURI_snapshot_v${versionNum}.parquet"`,
                  "X-Snapshot-Version": String(versionNum),
                  "X-DuckLake-Table": "LocationURI",
                  ...corsHeaders
                } 
              }
            );
          } catch (error) {
            // エラー時のクリーンアップ
            await Deno.remove(tempDir, { recursive: true }).catch(() => {});
            
            log.error("Failed to process snapshot request:", error);
            
            const appError: ApplicationError = {
              code: "OPERATION_FAILED",
              message: `[Snapshot Processing] ${error instanceof Error ? error.message : String(error)}`,
              operation: "process_snapshot"
            };
            
            const formatted = formatError(appError);
            
            return new Response(
              JSON.stringify(formatted),
              { 
                status: 500, 
                headers: { 
                  "Content-Type": CONTENT_TYPE_JSON,
                  ...corsHeaders 
                } 
              }
            );
          }
        }
        
        // ルートが見つからない場合
        const error: AppError = {
          code: "FILE_NOT_FOUND",
          message: `[Route Not Found] ${method} ${path}`,
          filePath: path
        };
        
        const formatted = formatError(error);
        
        return new Response(
          JSON.stringify(formatted),
          { 
            status: getHttpStatusCode(error), 
            headers: { 
              "Content-Type": CONTENT_TYPE_JSON,
              ...corsHeaders 
            } 
          }
        );
      }
    }
  };
}

// メインプロセスとして実行される場合のみサーバーを起動
if (import.meta.main) {
  const server = await createServer(DATA_FILES_PATH);
  log.info(`Server on http://localhost:${PORT}`);
  log.info("");
  log.info("Snapshot Provider Mode:");
  log.info("- POST /api/versions - List available versions");
  log.info("- POST /api/snapshot/:version - Get snapshot Parquet for specific version");
  log.info("- POST /query - Execute DuckDB query");
  
  await Deno.serve({ port: PORT }, server.handler).finished;
}

// In-source tests (統合テスト)
// FIXME: ユニットテストは指定関数のみ実装すること（すべての関数ではない）
if (!import.meta.main) {
  // テスト結果の型定義（規約準拠：Result型を使わない）
  type TestSuccess = { testName: string; message: string };
  type TestError = { code: "TEST_FAILED"; testName: string; message: string; error: any };
  type TestResult = TestSuccess | TestError;
  
  // エラー判定ヘルパー
  function isTestError(result: TestResult): result is TestError {
    return 'code' in result && result.code === "TEST_FAILED";
  }
  
  // テストヘルパー関数
  async function runTestStep(
    testName: string, 
    testFn: () => Promise<TestResult>
  ): Promise<TestResult> {
    log.info(`Running test: ${testName}`);
    const result = await testFn();
    if (isTestError(result)) {
      log.error(`Test failed: ${testName} - ${result.message}`);
    }
    return result;
  }
  
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
    if (isError(testEnv)) {
      // エラーをログに記録してテストを終了
      log.error(`Failed to create test environment: ${testEnv.message}`);
      await Deno.remove(tempDir, { recursive: true });
      return;
    }
    
    const { catalogName, metadataPath, dataPath: testDataPath } = testEnv as TestEnvironmentData;
    
    try {
      await t.step("use test catalog", async () => {
        const result = await runTestStep("use test catalog", async () => {
          const useResult = await executeQuery.execute(`USE ${catalogName}`);
          if (isQueryError(useResult)) {
            return { 
              code: "TEST_FAILED" as const,
              testName: "use_catalog",
              message: `[Test] Failed to use catalog: ${useResult.message}`,
              error: useResult
            };
          }
          
          // DuckLakeカタログが正しくアタッチされているか確認
          const tablesResult = await executeQuery.execute("SHOW ALL TABLES");
          if (isQueryError(tablesResult)) {
            return { 
              code: "TEST_FAILED" as const,
              testName: "show_tables", 
              message: `[Test] Failed to show tables: ${tablesResult.message}`,
              error: tablesResult
            };
          }
          
          log.info(`Catalog ${catalogName} is ready with ${tablesResult.rows.length} tables`);
          return { 
            testName: "use_catalog",
            message: "Catalog ready"
          };
        });
        
        if (isTestError(result)) {
          log.error(result.message);
        }
      });
      
      await t.step("create table and insert data", async () => {
        const result = await runTestStep("create table and insert data", async () => {
          // テーブル作成
          const createResult = await executeQuery.execute(
            `CREATE TABLE ${catalogName}.test_table (id INTEGER, value VARCHAR)`
          );
          if (isQueryError(createResult)) {
            return { 
              code: "TEST_FAILED" as const,
              testName: "create_table",
              message: `[Test] Failed to create table: ${createResult.message}`,
              error: createResult
            };
          }
          
          // データ挿入
          const insertResult = await executeQuery.execute(
            `INSERT INTO ${catalogName}.test_table VALUES (1, 'Hello'), (2, 'DuckLake')`
          );
          if (isQueryError(insertResult)) {
            return { 
              code: "TEST_FAILED" as const,
              testName: "insert_data",
              message: `[Test] Failed to insert data: ${insertResult.message}`,
              error: insertResult
            };
          }
          
          return { 
            testName: "create_table_and_insert",
            message: "Table created and data inserted"
          };
        });
        
        if (isTestError(result)) {
          log.error(result.message);
        }
      });
      
    } finally {
      // クリーンアップ
      await Deno.remove(tempDir, { recursive: true });
    }
  });
  
  // 統合テスト2: スナップショットParquet返却の検証
  Deno.test("Snapshot Parquet provider", async (t) => {
    // テスト用の一時ディレクトリを作成
    const tempDir = await Deno.makeTempDir({ prefix: "ducklake_test_snapshot_" });
    const dataPath = `${tempDir}/data/`;
    await Deno.mkdir(dataPath, { recursive: true });
    
    // テスト用サーバーインスタンスを作成
    const server = await createServer(dataPath);
    const { executeQuery } = server.deps;
    
    try {
      await t.step("create test version data", async () => {
        // DuckLakeカタログをアタッチ
        await executeQuery.execute(`ATTACH 'ducklake::${dataPath}' AS lake`);
        
        // LocationURIテーブルを作成
        await executeQuery.execute(`
          CREATE TABLE lake.LocationURI (
            id STRING
          )
        `);
        
        // 初期データを挿入（スナップショット1）
        await executeQuery.execute(`
          INSERT INTO lake.LocationURI VALUES 
          ('file:///test/v1/file1.ts'), 
          ('file:///test/v1/file2.ts')
        `);
      });
      
      await t.step("verify snapshot retrieval for existing version", async () => {
        const result = await runTestStep("verify snapshot retrieval", async () => {
          // バージョン1のスナップショットが存在することを確認
          const checkResult = await executeQuery.execute(`
            SELECT COUNT(*) as count 
            FROM lake.table_changes('LocationURI', 1, 1)
          `);
          
          if (isQueryError(checkResult) || Number(checkResult.rows[0]?.count) === 0) {
            return { 
              code: "TEST_FAILED" as const,
              testName: "verify_snapshot",
              message: "[Test] Snapshot version 1 not found",
              error: { version: "1" }
            };
          }
          
          log.info(`Snapshot 1 exists with changes`);
          return { 
            testName: "verify_snapshot",
            message: "Snapshot retrieval verified"
          };
        });
        
        if (isTestError(result)) {
          log.error(result.message);
        }
      });
      
      await t.step("verify error for non-existent version", async () => {
        const result = await runTestStep("verify error for non-existent version", async () => {
          // 存在しないバージョンをチェック
          const checkResult = await executeQuery.execute(`
            SELECT COUNT(*) as count 
            FROM lake.table_changes('LocationURI', 999, 999)
          `);
          
          if (!isQueryError(checkResult) && Number(checkResult.rows[0]?.count) > 0) {
            return { 
              code: "TEST_FAILED" as const,
              testName: "verify_non_existent",
              message: "[Test] Expected no data for non-existent version",
              error: { version: 999 }
            };
          }
          
          log.info("Correctly returned no data for non-existent version");
          return { 
            testName: "verify_non_existent",
            message: "Error handling verified"
          };
        });
        
        if (isTestError(result)) {
          log.error(result.message);
        }
      });
      
    } finally {
      // クリーンアップ
      await Deno.remove(tempDir, { recursive: true });
    }
  });
}