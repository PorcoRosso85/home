import SQLite

def main : IO Unit := do
  -- データベースに接続（メモリ上に仮作成）
  let db ← SQLite.open_db ":memory:"

  -- 接続確認用クエリの実行
  try
    let stmt ← db.prepare "SELECT 1;"
    let result ← stmt.query {}
    match result with
    | #[#[1]] => IO.println "✅ SQLite connection successful"
    | _ => IO.println "❌ Unexpected result"
  finally
    -- 接続のクローズ
    db.close

  return ()
