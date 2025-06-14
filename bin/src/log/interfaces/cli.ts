import { createSqlClient, info, warn, error as logError } from "../mod.ts";
import { DB_PATH, VALIDATION_RULES } from "../infrastructure/variables.ts";

// ヘルプメッセージ
const showHelp = (command?: string, verbose = false) => {
  // 基本のヘルプ
  if (!command) {
    console.log(`
DuckDB SQL CLI - シンプルなSQLクエリ実行ツール

使用方法:
  sql <コマンド> [オプション]

コマンド:
  exec <query>          - SQLクエリを実行
  init                  - 基本的なログテーブルを初期化
  help [command] [-v]   - ヘルプを表示 (コマンド指定で詳細表示)

オプション:
  --json                - 結果をJSON形式で出力
  --csv                 - 結果をCSV形式で出力
  --verbose, -v         - 詳細情報を表示

例:
  sql exec "SELECT * FROM logs"
  sql exec "INSERT INTO logs VALUES (...)"
  sql init
  sql help exec
  sql help -v
`);

    // 詳細なヘルプが要求された場合
    if (verbose) {
      console.log(`
詳細なコマンド情報:

  exec:
    SQLクエリを実行します。SELECTクエリの場合は結果を表示し、
    その他のクエリ(INSERT/UPDATE/CREATE等)は影響を受けた行数を表示します。
    プレースホルダーパラメータにも対応しています。

  init:
    基本的なログテーブルを作成します。すでに存在する場合は何も変更しません。
    テーブル構造: id, timestamp, level, message, metadata

  help:
    ヘルプを表示します。コマンド名を指定すると、そのコマンドの詳細を表示します。
    -v または --verbose オプションを指定すると、より詳細な情報を表示します。

データベース:
  現在のデータベースパス: ${DB_PATH}
  (このパスは infrastructure/variables.ts で変更できます)

バリデーション:
  SQLクエリは実行前に安全性をチェックします。
  - 最大クエリ長: ${VALIDATION_RULES.MAX_QUERY_LENGTH}文字
  - ブロックされる操作: ${VALIDATION_RULES.BLACKLISTED_STATEMENTS.join(', ')}

実行時のフラグ:
  Denoで実行する際には次のフラグが必要です:
  --allow-read --allow-write --allow-env --allow-net --allow-ffi
`);
    }
    return;
  }

  // 特定コマンドのヘルプ
  switch (command.toLowerCase()) {
    case "exec":
      console.log(`
コマンド: exec <query>
説明: SQLクエリを実行します

使用方法:
  sql exec "SELECT * FROM logs"
  sql exec "INSERT INTO logs (id, level, message) VALUES (1, 'INFO', 'テストメッセージ')"

オプション:
  --json      - 結果をJSON形式で出力
  --csv       - 結果をCSV形式で出力
  --verbose   - 詳細なデバッグ情報を表示

例:
  sql exec "SELECT * FROM logs WHERE level = 'ERROR'"
  sql exec "SELECT * FROM logs" --json
  sql exec "CREATE INDEX idx_logs_level ON logs(level)"
`);
      break;
    
    case "init":
      console.log(`
コマンド: init
説明: 基本的なログテーブルを初期化します

使用方法:
  sql init [--verbose]

作成されるテーブル構造:
  CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR,
    message TEXT,
    metadata JSON,
    code VARCHAR(3) NOT NULL CHECK (regexp_matches(code, '^[0-9]{3}$')),
    error JSON NOT NULL CHECK (json_type(error) = 'OBJECT')
  );
  
  CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
  CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
`);
      break;
      
    case "help":
      console.log(`
コマンド: help [command] [-v]
説明: ヘルプを表示します

使用方法:
  sql help            - 基本ヘルプを表示
  sql help <command>  - 特定コマンドのヘルプを表示
  sql help -v         - 詳細なヘルプを表示

例:
  sql help exec       - execコマンドの詳細を表示
  sql help --verbose  - すべてのコマンドの詳細を表示
`);
      break;
      
    default:
      console.log(`指定されたコマンド '${command}' は見つかりません。`);
      showHelp();
      break;
  }
};

// テーブル初期化SQLの定義
const INIT_SQL = `
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  level VARCHAR,
  message TEXT,
  metadata JSON,
  code VARCHAR(3) NOT NULL CHECK (regexp_matches(code, '^[0-9]{3}$')),
  error JSON NOT NULL CHECK (json_type(error) = 'OBJECT')
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
`;

// メイン関数
const main = async () => {
  const args = Deno.args;
  const verbose = args.includes("--verbose") || args.includes("-v");
  const jsonOutput = args.includes("--json");
  const csvOutput = args.includes("--csv");
  
  // verboseモードの場合は詳細情報を表示
  if (verbose) {
    console.log("Verbose mode enabled");
    console.log("Args:", args);
    console.log("Database path:", DB_PATH);
  }
  
  // ヘルプの表示またはコマンドなしの場合
  if (args.length === 0) {
    showHelp(undefined, verbose);
    return;
  }
  
  // ヘルプコマンドの処理
  if (args[0] === "help") {
    const helpCommand = args.length > 1 && !args[1].startsWith("-") ? args[1] : undefined;
    showHelp(helpCommand, verbose);
    return;
  }
  
  // SQLクライアントの初期化
  const sqlClient = createSqlClient();
  
  // ロギング開始
  info("CLI started", { args });
  
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
        logError(`SQLエラー: ${result.error.message}`, result.error);
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
        logError(`初期化エラー: ${result.error.message}`, result.error);
        console.error(`初期化エラー: ${result.error.message}`);
        return;
      }
      
      info("テーブルが初期化されました");
      
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
