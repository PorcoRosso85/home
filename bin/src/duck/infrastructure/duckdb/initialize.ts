/**
 * DuckDB/DuckLake初期化
 * DuckDBインスタンスの作成とDuckLake拡張の設定
 */

import { DuckDBInstance } from "npm:@duckdb/node-api@1.3.0-alpha.21";
import * as log from "../../../log/logger.ts";
import { 
  DUCKLAKE_CATALOG_TYPE,
  DUCKLAKE_CATALOG_PATH,
  DUCKLAKE_CATALOG_CONNECTION,
  DATA_FILES_PATH
} from "../variables.ts";

export type DuckDBConnection = {
  run: (query: string) => Promise<any>;
  runAndReadAll: (query: string) => Promise<{
    getRows: () => any[][];
    columnCount: number;
    columnName: (index: number) => string | null;
  }>;
};

export type InitializeResult = {
  instance: DuckDBInstance;
  connection: DuckDBConnection;
};

/**
 * DuckDBとDuckLakeを初期化
 */
export async function initializeDuckDB(): Promise<InitializeResult> {
  log.info("Initializing DuckDB...");
  
  // DuckDBインスタンスを作成（インメモリ）
  const instance = await DuckDBInstance.create("");
  const connection = await instance.connect();
  
  // バージョン確認
  try {
    const versionReader = await connection.runAndReadAll("SELECT version() as version");
    const rows = versionReader.getRows();
    if (rows.length > 0) {
      log.info(`DuckDB version: ${rows[0][0]}`);
    }
  } catch (err) {
    log.warn("Failed to get DuckDB version:", err);
  }
  
  // DuckLake拡張のインストールとロード
  try {
    await connection.run("INSTALL ducklake");
    await connection.run("LOAD ducklake");
    log.info("DuckLake extension loaded successfully");
  } catch (err) {
    log.error("Failed to load DuckLake extension:", err);
    throw err;
  }
  
  // DuckLakeカタログのアタッチ
  try {
    let attachQuery: string;
    
    switch (DUCKLAKE_CATALOG_TYPE) {
      case "postgres":
        attachQuery = `ATTACH 'ducklake:${DUCKLAKE_CATALOG_CONNECTION}' AS lake (DATA_PATH '${DATA_FILES_PATH}')`;
        await connection.run("INSTALL postgres");
        break;
        
      case "mysql":
        attachQuery = `ATTACH 'ducklake:${DUCKLAKE_CATALOG_CONNECTION}' AS lake (DATA_PATH '${DATA_FILES_PATH}')`;
        await connection.run("INSTALL mysql");
        break;
        
      case "sqlite":
        attachQuery = `ATTACH 'ducklake:sqlite:${DUCKLAKE_CATALOG_PATH}' AS lake (DATA_PATH '${DATA_FILES_PATH}')`;
        await connection.run("INSTALL sqlite");
        break;
        
      case "duckdb":
      default:
        attachQuery = `ATTACH 'ducklake:${DUCKLAKE_CATALOG_PATH}' AS lake (DATA_PATH '${DATA_FILES_PATH}')`;
        break;
    }
    
    await connection.run(attachQuery);
    log.info(`DuckLake catalog attached as 'lake' (type: ${DUCKLAKE_CATALOG_TYPE})`);
  } catch (err) {
    // カタログが存在しない場合は新規作成される
    log.info("DuckLake catalog will be created if it doesn't exist");
  }
  
  return { instance, connection };
}