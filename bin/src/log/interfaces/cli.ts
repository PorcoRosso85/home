import { createSqlClient } from "../mod.ts";
import { DB_PATH } from "../infrastructure/variables.ts";

// ヘルプメッセージ
const showHelp = () => {
  console.log(`
DuckDB SQL CLI - シンプルなSQLクエリ実行ツール

使用方法:
  sql <コマンド> [オプション]

コマンド:
  exec <query>        - SQLクエリを実行
  init                - 基本的なログテーブルを初期化
  help                - このヘルプを表示

オプション:
  --json              - 結果をJSON形式で出力
  --csv               - 結果をCSV形式で出力
  --verbose           - 詳細情報を表示

例:
  sql exec "CREATE TABLE logs (id INTEGER, message TEXT, created_at TIMESTAMP)"
  sql exec "INSERT INTO logs VALUES (1, 'テストメッセージ', CURRENT_TIMESTAMP)"
  sql exec "SELECT * FROM logs"
  sql init
  `);
};

// テーブル初期化SQLの定義
const INIT_SQL = `
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  level VARCHAR,
  message TEXT,
  metadata JSON
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
`;

// メイン関数
const main = async () => {
  const args = Deno.args;
  const verbose = args.includes("--verbose");
  const jsonOutput = args.includes("--json");
  const csvOutput = args.includes("--csv");
  
  // verboseモードの場合は詳細情報を表示
  if (verbose) {
    console.log("Verbose mode enabled");
    console.log("Args:", args);
    console.log("Database path:", DB_PATH);
  }
  
  // ヘルプの表示またはコマンドなしの場合
  if (args.length === 0 || args[0] === "help") {
    showHelp();
    return;
  }
  
  // SQLクライアントの初期化
  const sqlClient = createSqlClient();
  
  // コマンド処理
  switch (args[0]) {
    // SQLクエリの実行
    case "exec": {
      if (args.length < 2) {
        console.error("エラー: SQLクエリが必要です");
        showHelp();
        return;
      }
      
      const sqlQuery = args[1];
      if (verbose) console.log(`実行するSQL: ${sqlQuery}`);
      
      // SQLクエリの実行
      const result = await sqlClient.execute(sqlQuery);
      
      // エラーの場合
      if (!result.ok) {
        console.error(`SQLエラー: ${result.error.message}`);
        if (result.error.code) console.error(`エラーコード: ${result.error.code}`);
        return;
      }
      
      // 結果の表示
      const rows = result.value;
      
      if (rows.length === 0) {
        console.log("結果: 0件");
        return;
      }
      
      // 出力形式に応じた表示
      if (jsonOutput) {
        // DuckDBの結果をそのままJSON形式で出力
        console.log(JSON.stringify(rows, null, 2));
      } else if (csvOutput) {
        // 簡易的なCSV出力
        const headers = Object.keys(rows[0]);
        console.log(headers.join(","));
        
        for (const row of rows) {
          const values = headers.map(header => {
            const value = row[header];
            if (value === null || value === undefined) return '';
            if (typeof value === 'string') return `"${value.replace(/"/g, '""')}"`;
            return String(value);
          });
          console.log(values.join(","));
        }
      } else {
        // DuckDBの結果をそのままコンソールに出力
        console.log("\n===== DuckDB 結果 =====");
        console.log(rows);
        console.log("\n結果のサイズ: " + rows.length + "件");
      }
      
      console.log(`\nデータベース: ${DB_PATH}`);
      break;
    }
    
    // テーブル初期化
    case "init": {
      if (verbose) console.log("テーブルを初期化します...");
      
      const result = await sqlClient.execute(INIT_SQL);
      
      if (!result.ok) {
        console.error(`初期化エラー: ${result.error.message}`);
        return;
      }
      
      console.log("テーブルが初期化されました");
      console.log(`データベース: ${DB_PATH}`);
      break;
    }
    
    // 不明なコマンド
    default:
      console.error(`不明なコマンド: ${args[0]}`);
      showHelp();
      break;
  }
};

// CLIの実行
await main();
