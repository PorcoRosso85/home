import { assertEquals, assertExists } from "https://deno.land/std@0.218.0/assert/mod.ts";
import { createDatabase, createConnection } from "../core/database.ts";

// KuzuDB TypeScript/Deno 使用方法の完全なサンプル
Deno.test("【使い方サンプル】基本的なKuzuDB操作", async () => {
  // 1. データベース作成
  const db = await createDatabase(":memory:");  // インメモリDB
  // const db = await createDatabase("./mydb");  // 永続化DB
  
  // 2. コネクション作成
  const conn = await createConnection(db);
  
  // 3. スキーマ定義（ノードテーブル）
  await conn.query(`
    CREATE NODE TABLE Person(
      name STRING, 
      age INT64, 
      PRIMARY KEY (name)
    )
  `);
  
  // 4. データ挿入
  await conn.query(`CREATE (:Person {name: 'Alice', age: 30})`);
  await conn.query(`CREATE (:Person {name: 'Bob', age: 25})`);
  
  // 5. クエリ実行
  const result = await conn.query(`
    MATCH (p:Person) 
    RETURN p.name, p.age 
    ORDER BY p.age
  `);
  
  // 6. 結果取得
  const rows = await result.getAll();
  assertEquals(rows.length, 2);
  assertEquals(rows[0]["p.name"], "Bob");
  assertEquals(rows[0]["p.age"], 25);
});

Deno.test("【使い方サンプル】グラフ構造の作成", async () => {
  const db = await createDatabase(":memory:");
  const conn = await createConnection(db);
  
  // ノードテーブル定義
  await conn.query(`CREATE NODE TABLE User(id STRING, name STRING, PRIMARY KEY (id))`);
  await conn.query(`CREATE NODE TABLE Project(id STRING, title STRING, PRIMARY KEY (id))`);
  
  // リレーションテーブル定義
  await conn.query(`CREATE REL TABLE WORKS_ON(FROM User TO Project, role STRING)`);
  
  // データ作成
  await conn.query(`CREATE (:User {id: 'u1', name: 'Alice'})`);
  await conn.query(`CREATE (:User {id: 'u2', name: 'Bob'})`);
  await conn.query(`CREATE (:Project {id: 'p1', title: 'KuzuDB Integration'})`);
  
  // リレーション作成
  await conn.query(`
    MATCH (u:User {id: 'u1'}), (p:Project {id: 'p1'})
    CREATE (u)-[:WORKS_ON {role: 'Developer'}]->(p)
  `);
  
  await conn.query(`
    MATCH (u:User {id: 'u2'}), (p:Project {id: 'p1'})
    CREATE (u)-[:WORKS_ON {role: 'Tester'}]->(p)
  `);
  
  // グラフトラバーサル
  const result = await conn.query(`
    MATCH (u:User)-[w:WORKS_ON]->(p:Project)
    WHERE p.title = 'KuzuDB Integration'
    RETURN u.name, w.role
    ORDER BY u.name
  `);
  
  const rows = await result.getAll();
  assertEquals(rows.length, 2);
  assertEquals(rows[0]["u.name"], "Alice");
  assertEquals(rows[0]["w.role"], "Developer");
});

Deno.test("【使い方サンプル】Contract Service実装パターン", async () => {
  const db = await createDatabase(":memory:");
  const conn = await createConnection(db);
  
  // Contract Service用のスキーマ
  await conn.query(`CREATE NODE TABLE Service(id STRING, endpoint STRING, PRIMARY KEY (id))`);
  await conn.query(`CREATE NODE TABLE Schema(id STRING, content STRING, PRIMARY KEY (id))`);
  await conn.query(`CREATE REL TABLE PROVIDES(FROM Service TO Schema)`);
  await conn.query(`CREATE REL TABLE EXPECTS(FROM Service TO Schema)`);
  
  // サービス登録関数
  async function registerProvider(serviceId: string, endpoint: string, schemaContent: string) {
    const schemaId = `${serviceId}-output-schema`;
    
    await conn.query(`CREATE (:Service {id: $serviceId, endpoint: $endpoint})`, 
      { serviceId, endpoint });
    await conn.query(`CREATE (:Schema {id: $schemaId, content: $schemaContent})`, 
      { schemaId, schemaContent });
    await conn.query(`
      MATCH (s:Service {id: $serviceId}), (sch:Schema {id: $schemaId})
      CREATE (s)-[:PROVIDES]->(sch)
    `, { serviceId, schemaId });
  }
  
  // 使用例
  await registerProvider(
    'weather-v1', 
    'http://weather:8080',
    JSON.stringify({ type: 'object', properties: { temp: { type: 'number' } } })
  );
  
  // 検証
  const result = await conn.query(`
    MATCH (s:Service)-[:PROVIDES]->(sch:Schema)
    RETURN s.id, s.endpoint, sch.content
  `);
  
  const rows = await result.getAll();
  assertEquals(rows.length, 1);
  assertEquals(rows[0]["s.id"], "weather-v1");
  assertExists(JSON.parse(rows[0]["sch.content"]));
});

// このファイルの実行方法：
// nix develop -c deno test --allow-all tests/usage_example_test.ts