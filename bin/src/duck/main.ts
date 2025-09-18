/**
 * DuckLake SQLクエリ実行ツール
 * 
 * 使用方法:
 *   deno run --allow-all main.ts "<SQL query>" [format]
 * 
 * 例:
 *   deno run --allow-all main.ts "SELECT * FROM lake.LocationURI"
 *   deno run --allow-all main.ts "SELECT * FROM lake.LocationURI" csv
 *   deno run --allow-all main.ts "SELECT * FROM lake.LocationURI" table
 *   deno run --allow-all main.ts "SELECT * FROM lake.LocationURI AT (VERSION => 1)"
 */

import { initializeDuckDB } from "./infrastructure/duckdb/initialize.ts";
import * as log from "../log/logger.ts";
import { serializeBigInt } from "./shared/utils.ts";

/**
 * シンプルなテーブル形式で出力
 */
function printTable(columns: string[], rows: any[][]) {
  // 各列の最大幅を計算
  const widths = columns.map((col, idx) => {
    let maxWidth = col.length;
    rows.forEach(row => {
      const cellValue = String(row[idx] ?? "");
      maxWidth = Math.max(maxWidth, cellValue.length);
    });
    return Math.min(maxWidth, 50); // 最大50文字
  });
  
  // ヘッダー行
  const separator = "+" + widths.map(w => "-".repeat(w + 2)).join("+") + "+";
  console.log(separator);
  console.log("|" + columns.map((col, idx) => ` ${col.padEnd(widths[idx])} `).join("|") + "|");
  console.log(separator);
  
  // データ行
  rows.forEach(row => {
    const formattedRow = row.map((cell, idx) => {
      let cellStr = String(cell ?? "");
      if (cellStr.length > widths[idx]) {
        cellStr = cellStr.substring(0, widths[idx] - 3) + "...";
      }
      return ` ${cellStr.padEnd(widths[idx])} `;
    });
    console.log("|" + formattedRow.join("|") + "|");
  });
  console.log(separator);
}

async function main() {
  // コマンドライン引数の取得
  let query = Deno.args[0];
  let format = Deno.args[1]?.toLowerCase() || "table";
  
  // --txオプションのチェック
  const hasTxOption = Deno.args.includes("--tx");
  if (hasTxOption) {
    // --txを除外してフォーマットを再取得
    const args = Deno.args.filter(arg => arg !== "--tx");
    query = args[0];
    format = args[1]?.toLowerCase() || "table";
  }
  
  // 引数チェック
  if (!query) {
    console.error("Usage: deno run main.ts '<query>' [format] [--tx]");
    console.error("");
    console.error("Formats:");
    console.error("  table   - ASCII table format (default)");
    console.error("  json    - JSON format");
    console.error("  csv     - CSV format with headers");
    console.error("  parquet - Parquet file format");
    console.error("");
    console.error("Options:");
    console.error("  --tx    - Wrap query in BEGIN/COMMIT transaction");
    console.error("");
    console.error("Examples:");
    console.error("  deno run main.ts \"SELECT * FROM lake.LocationURI\"");
    console.error("  deno run main.ts \"INSERT INTO lake.LocationURI VALUES ('x')\" --tx");
    console.error("  deno run main.ts \"BEGIN; INSERT INTO lake.LocationURI VALUES ('x'); COMMIT;\"");
    Deno.exit(1);
  }
  
  // --txオプションがある場合、クエリをトランザクションで囲む
  if (hasTxOption && !query.toUpperCase().includes("BEGIN")) {
    query = `BEGIN; ${query}; COMMIT;`;
  }
  
  try {
    // DuckDB/DuckLake初期化
    const { connection } = await initializeDuckDB();
    
    // セミコロンで複数のクエリに分割（末尾のセミコロンと空白を除去）
    const queries = query.split(';')
      .map(q => q.trim())
      .filter(q => q.length > 0);
    
    // 複数クエリの場合
    if (queries.length > 1) {
      let hasError = false;
      const results: any[] = [];
      
      for (const singleQuery of queries) {
        try {
          // 各クエリを実行
          await connection.run(singleQuery);
          results.push({
            query: singleQuery,
            success: true
          });
        } catch (error) {
          hasError = true;
          results.push({
            query: singleQuery,
            success: false,
            error: error instanceof Error ? error.message : String(error)
          });
          break; // エラーが発生したら中断
        }
      }
      
      // 結果を出力
      console.log(JSON.stringify({
        success: !hasError,
        message: hasError ? "Transaction failed" : "All queries executed successfully",
        results: results
      }));
      
      if (hasError) {
        Deno.exit(1);
      }
      return;
    }
    
    // 単一クエリの処理（以下は既存のコード）
    let upperQuery = query.trim().toUpperCase();
    
    // SHOW TABLESをSHOW ALL TABLESに正規化
    if (upperQuery === "SHOW TABLES") {
      query = "SHOW ALL TABLES";
      upperQuery = "SHOW ALL TABLES";
    }
    
    const isSelectQuery = upperQuery.startsWith("SELECT") ||
                         upperQuery.startsWith("FROM") ||
                         upperQuery.startsWith("WITH");
    
    // メタデータクエリかどうかを判定（COPYが使えない）
    const isMetadataQuery = upperQuery.startsWith("SHOW") ||
                           upperQuery.startsWith("DESCRIBE") ||
                           upperQuery.startsWith("PRAGMA");
    
    if (isSelectQuery && format !== "table") {
      // SELECT系のクエリは指定フォーマットで出力（table以外）
      let outputQuery: string;
      
      switch (format) {
        case "csv":
          outputQuery = `COPY (${query}) TO '/dev/stdout' (FORMAT CSV, HEADER)`;
          break;
        case "parquet":
          outputQuery = `COPY (${query}) TO '/dev/stdout' (FORMAT PARQUET)`;
          break;
        case "json":
        default:
          outputQuery = `COPY (${query}) TO '/dev/stdout' (FORMAT JSON)`;
          break;
      }
      
      await connection.run(outputQuery);
    } else if (isSelectQuery || isMetadataQuery) {
      // SELECTクエリのtable形式、またはメタデータクエリは直接実行して結果を取得
      const reader = await connection.runAndReadAll(query);
      const rows = reader.getRows();
      const columnCount = reader.columnCount;
      const columns: string[] = [];
      
      for (let i = 0; i < columnCount; i++) {
        columns.push(reader.columnName(i) || `col_${i}`);
      }
      
      // 結果をJSON形式で出力
      const result = rows.map(row => {
        const obj: Record<string, any> = {};
        columns.forEach((col, idx) => {
          obj[col] = row[idx];
        });
        return obj;
      });
      
      // SHOW ALL TABLESまたはSHOW TABLESの場合、lakeデータベースのテーブルのみフィルタリング
      let filteredRows = rows;
      let filteredResult = result;
      if (upperQuery === "SHOW ALL TABLES" || upperQuery === "SHOW TABLES") {
        filteredRows = rows.filter(row => {
          // databaseカラムのインデックスを取得
          const dbIdx = columns.indexOf("database");
          return dbIdx >= 0 && row[dbIdx] === "lake";
        });
        filteredResult = result.filter(r => r.database === "lake");
        
        // lakeにテーブルがない場合のメッセージ
        if (filteredRows.length === 0 && format === "table") {
          console.log("No tables found in 'lake' database.");
          console.log("");
          console.log("To create a table:");
          console.log("  deno run --allow-all main.ts \"CREATE TABLE lake.LocationURI (id VARCHAR)\"");
          return;
        }
      }
      
      if (format === "csv") {
        // CSV形式で出力
        console.log(columns.join(","));
        filteredRows.forEach(row => {
          console.log(row.join(","));
        });
      } else if (format === "table") {
        // テーブル形式で出力
        printTable(columns, filteredRows);
      } else {
        // JSON形式で出力（BigInt対応）
        const serialized = serializeBigInt(filteredResult);
        console.log(JSON.stringify(serialized));
      }
    } else {
      // DML/DDL操作は直接実行
      await connection.run(query);
      
      // 成功メッセージ（JSON形式で統一）
      const successMessage = {
        success: true,
        message: "Query executed successfully",
        query: query
      };
      console.log(JSON.stringify(serializeBigInt(successMessage)));
    }
  } catch (error) {
    // エラー出力
    const errorMessage = {
      success: false,
      error: error instanceof Error ? error.message : String(error),
      query: query
    };
    console.error(JSON.stringify(serializeBigInt(errorMessage)));
    Deno.exit(1);
  }
}

// メインエントリポイント
if (import.meta.main) {
  main().catch(console.error);
}