import { assertEquals, assertExists } from "https://deno.land/std@0.224.0/assert/mod.ts";

// Step 3: Cypherクエリ実行テスト
// syncバージョンでデータベース操作を実現

Deno.test("Initialize sync version", async () => {
  const kuzu = await import("npm:kuzu-wasm/sync");
  const kuzuModule = kuzu.default;
  
  // 初期化が必要
  await kuzuModule.init();
  
  const version = await kuzuModule.getVersion();
  assertExists(version);
  console.log(`Kuzu version: ${version}`);
});

Deno.test("Create in-memory database with sync API", async () => {
  const kuzu = await import("npm:kuzu-wasm/sync");
  const { Database, Connection } = kuzu.default;
  
  // 初期化
  await kuzu.default.init();
  
  // インメモリデータベース作成
  const db = new Database(":memory:");
  assertExists(db);
  
  const conn = new Connection(db);
  assertExists(conn);
  
  // スキーマ作成
  const createTableResult = conn.query(
    "CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))"
  );
  assertExists(createTableResult);
  
  // データ挿入
  const insertResult = conn.query(
    "CREATE (n:Person {name: 'Alice', age: 30})"
  );
  assertExists(insertResult);
  
  // データ検索
  const selectResult = conn.query("MATCH (n:Person) RETURN n.name, n.age");
  assertExists(selectResult);
  
  // 結果取得
  const rows = selectResult.getAllObjects();
  assertEquals(rows.length, 1);
  assertEquals(rows[0]["n.name"], "Alice");
  assertEquals(rows[0]["n.age"], 30);
  
  // クリーンアップ
  selectResult.close();
  conn.close();
  db.close();
  
  console.log("✅ Database operations successful");
});

Deno.test("Complex graph queries", async () => {
  const kuzu = await import("npm:kuzu-wasm/sync");
  const { Database, Connection } = kuzu.default;
  
  await kuzu.default.init();
  
  const db = new Database(":memory:");
  const conn = new Connection(db);
  
  // ユーザーと都市のグラフを作成
  conn.query("CREATE NODE TABLE User(name STRING, PRIMARY KEY(name))");
  conn.query("CREATE NODE TABLE City(name STRING, PRIMARY KEY(name))");
  conn.query("CREATE REL TABLE LivesIn(FROM User TO City)");
  
  // データ挿入
  conn.query("CREATE (u:User {name: 'Bob'})");
  conn.query("CREATE (u:User {name: 'Charlie'})");
  conn.query("CREATE (c:City {name: 'Tokyo'})");
  conn.query("CREATE (c:City {name: 'Osaka'})");
  
  // リレーションシップ作成
  conn.query("MATCH (u:User {name: 'Bob'}), (c:City {name: 'Tokyo'}) CREATE (u)-[:LivesIn]->(c)");
  conn.query("MATCH (u:User {name: 'Charlie'}), (c:City {name: 'Osaka'}) CREATE (u)-[:LivesIn]->(c)");
  
  // クエリ実行
  const result = conn.query("MATCH (u:User)-[:LivesIn]->(c:City) RETURN u.name, c.name ORDER BY u.name");
  const rows = result.getAllObjects();
  
  assertEquals(rows.length, 2);
  assertEquals(rows[0]["u.name"], "Bob");
  assertEquals(rows[0]["c.name"], "Tokyo");
  assertEquals(rows[1]["u.name"], "Charlie");
  assertEquals(rows[1]["c.name"], "Osaka");
  
  result.close();
  conn.close();
  db.close();
  
  console.log("✅ Complex graph queries successful");
});