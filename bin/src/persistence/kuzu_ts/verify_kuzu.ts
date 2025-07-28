// KuzuDBが実際に使用されていることを検証するスクリプト
import { Database, Connection } from "npm:kuzu@0.10.0";

console.log("=== KuzuDB実装検証 ===\n");

// 1. KuzuDBのバージョン情報を取得（モックには存在しない）
try {
  const kuzu = await import("npm:kuzu@0.10.0");
  console.log("1. KuzuDB VERSION:", kuzu.VERSION || "未定義");
  console.log("   STORAGE_VERSION:", kuzu.STORAGE_VERSION || "未定義");
} catch (e) {
  console.log("1. バージョン情報取得エラー:", e.message);
}

// 2. KuzuDB固有の機能を使用
const db = new Database(":memory:");
const conn = new Connection(db);

console.log("\n2. Database型:", db.constructor.name);
console.log("   Connection型:", conn.constructor.name);

// 3. KuzuDB固有のCypherクエリを実行
try {
  // KuzuDB固有の関数を使用
  await conn.query("CALL db_version() RETURN version");
  console.log("\n3. db_version()関数: ✅ 成功（KuzuDB固有）");
} catch (e) {
  console.log("\n3. db_version()関数: ❌ 失敗", e.message);
}

// 4. KuzuDB固有のデータ型を使用
try {
  await conn.query(`
    CREATE NODE TABLE TestTypes(
      id INT64,
      data BLOB,
      PRIMARY KEY (id)
    )
  `);
  console.log("4. BLOB型サポート: ✅ 成功（KuzuDB固有）");
} catch (e) {
  console.log("4. BLOB型サポート: ❌ 失敗", e.message);
}

// 5. プロセス情報から確認
console.log("\n5. プロセス情報:");
console.log("   Node modules:", Deno.env.get("NODE_PATH") || "未設定");
console.log("   LD_LIBRARY_PATH:", Deno.env.get("LD_LIBRARY_PATH") || "未設定");

console.log("\n結論: 上記の結果から判断してください");