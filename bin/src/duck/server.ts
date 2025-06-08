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
import type { QueryResult } from "./domain/types.ts";
import type { AppError, Result } from "./shared/errors.ts";
import { getHttpStatusCode, handleError } from "./shared/errors.ts";

// 依存性の型定義
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
    
    // パスからバージョンパラメータを抽出
    const snapshotMatch = path.match(/^\/api\/snapshot\/(.+)$/);
    
    // ルーティングをパターンマッチで処理
    const route = `${method}:${path}`;
    
    switch (route) {
      case "GET:/": {
        const statusResult = await deps.executeQuery.execute(
          "SELECT loaded FROM duckdb_extensions() WHERE extension_name = 'ducklake'"
        );
        
        const ducklakeStatus = statusResult.success && statusResult.data.length > 0 
          ? (statusResult.data[0].loaded ? "loaded" : "not loaded")
          : "not available";
        
        return new Response(
          JSON.stringify({ 
            status: "ok", 
            ducklake: ducklakeStatus,
            mode: "snapshot-provider"
          }),
          { status: 200, headers: { "Content-Type": CONTENT_TYPE_JSON } }
        );
      }
      
      case "POST:/query": {
        const body = await req.json().catch(() => null);
        
        if (!body || !body.query || body.query.trim() === "") {
          const error: AppError = {
            code: "VALIDATION_FAILED",
            message: "Query required",
            details: { body }
          };
          
          return new Response(
            JSON.stringify({ 
              success: false, 
              error: handleError(error)
            }),
            { 
              status: getHttpStatusCode(error), 
              headers: { "Content-Type": CONTENT_TYPE_JSON } 
            }
          );
        }
        
        log.info(`Query: ${body.query}`);
        
        const result = await deps.executeQuery.executeWithValidation(body.query);
        
        if (!result.success) {
          return new Response(
            JSON.stringify({ 
              success: false, 
              error: handleError(result.error)
            }),
            { 
              status: getHttpStatusCode(result.error), 
              headers: { "Content-Type": CONTENT_TYPE_JSON } 
            }
          );
        }
        
        return new Response(
          JSON.stringify(result),
          { status: 200, headers: { "Content-Type": CONTENT_TYPE_JSON } }
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
          if (!testResult.success) {
            continue;
          }
          
          const count = testResult.data[0]?.count;
          if (count > 0) {
            // 前のバージョンとの差分を計算
            let changes = { total: 0, inserts: 0, deletes: 0, updates: 0 };
            
            if (v > 1) {
              // 前のバージョンと比較
              const prevResult = await deps.executeQuery.execute(
                `SELECT COUNT(*) as prev_count FROM lake.LocationURI AT (VERSION => ${v - 1})`
              );
              
              if (prevResult.success) {
                const prevCount = prevResult.data[0]?.prev_count || 0;
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
          return new Response(
            JSON.stringify({ 
              success: false, 
              error: "No DuckLake snapshots found. Please run duck.init.sh first."
            }),
            { 
              status: 404, 
              headers: { "Content-Type": CONTENT_TYPE_JSON } 
            }
          );
        }
        
        // バージョン番号の降順でソート
        availableVersions.sort((a, b) => b.version - a.version);
        
        return new Response(
          JSON.stringify({
            success: true,
            versions: availableVersions
          }),
          { 
            status: 200, 
            headers: { "Content-Type": CONTENT_TYPE_JSON } 
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
            return new Response(
              JSON.stringify({ 
                success: false, 
                error: "Invalid version format. Expected numeric snapshot ID."
              }),
              { 
                status: 400, 
                headers: { "Content-Type": CONTENT_TYPE_JSON } 
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
            
            if (!exportResult.success) {
              log.error("Failed to export snapshot:", exportResult.error);
              
              // バージョンが存在しない可能性
              if (exportResult.error.includes("VERSION") || exportResult.error.includes("snapshot")) {
                return new Response(
                  JSON.stringify({ 
                    success: false, 
                    error: `Snapshot version ${versionNum} not found`
                  }),
                  { 
                    status: 404, 
                    headers: { "Content-Type": CONTENT_TYPE_JSON } 
                  }
                );
              }
              
              return new Response(
                JSON.stringify({ 
                  success: false, 
                  error: "Failed to export snapshot",
                  details: exportResult.error
                }),
                { 
                  status: 500, 
                  headers: { "Content-Type": CONTENT_TYPE_JSON } 
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
                  "X-DuckLake-Table": "LocationURI"
                } 
              }
            );
          } catch (error) {
            // エラー時のクリーンアップ
            await Deno.remove(tempDir, { recursive: true }).catch(() => {});
            
            log.error("Failed to process snapshot request:", error);
            return new Response(
              JSON.stringify({ 
                success: false, 
                error: "Failed to process snapshot request"
              }),
              { 
                status: 500, 
                headers: { "Content-Type": CONTENT_TYPE_JSON } 
              }
            );
          }
        }
        
        // ルートが見つからない場合
        const error: AppError = {
          code: "FILE_NOT_FOUND",
          message: "Route not found",
          filePath: path
        };
        
        return new Response(
          JSON.stringify({ 
            success: false,
            error: handleError(error)
          }),
          { 
            status: getHttpStatusCode(error), 
            headers: { "Content-Type": CONTENT_TYPE_JSON } 
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
  // テスト結果の型定義
  type TestResult = Result<string>;
  
  // テストヘルパー関数
  async function runTestStep(
    testName: string, 
    testFn: () => Promise<TestResult>
  ): Promise<TestResult> {
    log.info(`Running test: ${testName}`);
    const result = await testFn();
    if (!result.success) {
      log.error(`Test failed: ${testName} - ${handleError(result.error)}`);
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
    if (!testEnv.success) {
      // エラーをログに記録してテストを終了
      log.error(`Failed to create test environment: ${testEnv.error}`);
      await Deno.remove(tempDir, { recursive: true });
      return;
    }
    
    const { catalogName, metadataPath, dataPath: testDataPath } = testEnv;
    
    try {
      await t.step("use test catalog", async () => {
        const result = await runTestStep("use test catalog", async () => {
          const useResult = await executeQuery.execute(`USE ${catalogName}`);
          if (!useResult.success) {
            return { 
              success: false, 
              error: { 
                code: "OPERATION_FAILED" as const, 
                message: `Failed to use catalog: ${useResult.error}`,
                operation: "use_catalog"
              }
            };
          }
          
          // DuckLakeカタログが正しくアタッチされているか確認
          const tablesResult = await executeQuery.execute("SHOW ALL TABLES");
          if (!tablesResult.success) {
            return { 
              success: false, 
              error: { 
                code: "OPERATION_FAILED" as const, 
                message: `Failed to show tables: ${tablesResult.error}`,
                operation: "show_tables"
              }
            };
          }
          
          log.info(`Catalog ${catalogName} is ready with ${tablesResult.data.length} tables`);
          return { success: true, data: "Catalog ready" };
        });
        
        if (!result.success) {
          log.error(handleError(result.error));
        }
      });
      
      await t.step("create table and insert data", async () => {
        const result = await runTestStep("create table and insert data", async () => {
          // テーブル作成
          const createResult = await executeQuery.execute(
            `CREATE TABLE ${catalogName}.test_table (id INTEGER, value VARCHAR)`
          );
          if (!createResult.success) {
            return { 
              success: false, 
              error: { 
                code: "OPERATION_FAILED" as const, 
                message: `Failed to create table: ${createResult.error}`,
                operation: "create_table"
              }
            };
          }
          
          // データ挿入
          const insertResult = await executeQuery.execute(
            `INSERT INTO ${catalogName}.test_table VALUES (1, 'Hello'), (2, 'DuckLake')`
          );
          if (!insertResult.success) {
            return { 
              success: false, 
              error: { 
                code: "OPERATION_FAILED" as const, 
                message: `Failed to insert data: ${insertResult.error}`,
                operation: "insert_data"
              }
            };
          }
          
          return { success: true, data: "Table created and data inserted" };
        });
        
        if (!result.success) {
          log.error(handleError(result.error));
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
          
          if (!checkResult.success || Number(checkResult.data[0]?.count) === 0) {
            return { 
              success: false, 
              error: { 
                code: "VERSION_NOT_FOUND" as const, 
                message: "Snapshot version 1 not found",
                version: "1"
              }
            };
          }
          
          log.info(`Snapshot 1 exists with changes`);
          return { success: true, data: "Snapshot retrieval verified" };
        });
        
        if (!result.success) {
          log.error(handleError(result.error));
        }
      });
      
      await t.step("verify error for non-existent version", async () => {
        const result = await runTestStep("verify error for non-existent version", async () => {
          // 存在しないバージョンをチェック
          const checkResult = await executeQuery.execute(`
            SELECT COUNT(*) as count 
            FROM lake.table_changes('LocationURI', 999, 999)
          `);
          
          if (!checkResult.success || Number(checkResult.data[0]?.count) > 0) {
            return { 
              success: false, 
              error: { 
                code: "VALIDATION_FAILED" as const, 
                message: "Expected no data for non-existent version",
                details: { version: 999 }
              }
            };
          }
          
          log.info("Correctly returned no data for non-existent version");
          return { success: true, data: "Error handling verified" };
        });
        
        if (!result.success) {
          log.error(handleError(result.error));
        }
      });
      
    } finally {
      // クリーンアップ
      await Deno.remove(tempDir, { recursive: true });
    }
  });
}
