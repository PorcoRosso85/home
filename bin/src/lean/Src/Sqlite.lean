open Lean
open Lean.Meta
-- - SQLite3コマンドラインツール経由でDB操作を実行する
section ExternalDB

/-- 任意のSQLコマンドをsqlite3 CLIで実行 -/
def main (args : List String) : IO UInt32 := do
  -- 示例: argsからパラメータをパース
  let dbPath := args.getD 0 "default.db"
  -- let sql := args.getD 1 "SELECT * FROM users;"
  let sql := args.getD 1 "SELECT 1;"

  let output ← IO.Process.output {
    cmd := "sqlite3",
    args := #["-bail", "-cmd", ".echo on", dbPath, sql]
  }

  if output.exitCode ≠ 0 then
    IO.eprintln s!"Error: {output.stderr}"
    return 1

  IO.println output.stdout
  return 0
