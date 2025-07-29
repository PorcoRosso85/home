import { assertEquals, assertExists } from "https://deno.land/std@0.218.0/assert/mod.ts";
import { createDatabase, createConnection } from "../core/database.ts";

// Contract Service用のテストケース - 報告された期待動作を検証
Deno.test("Contract Service - Provider Registration", async () => {
  const db = await createDatabase(":memory:");
  const conn = await createConnection(db);
  
  // スキーマ作成
  await conn.query(`
    CREATE NODE TABLE LocationURI (id STRING, PRIMARY KEY (id))
  `);
  await conn.query(`
    CREATE NODE TABLE App (id STRING, PRIMARY KEY (id))
  `);
  await conn.query(`
    CREATE NODE TABLE Schema (id STRING, schema_content STRING, PRIMARY KEY (id))
  `);
  await conn.query(`
    CREATE REL TABLE LOCATES (FROM LocationURI TO App)
  `);
  await conn.query(`
    CREATE REL TABLE PROVIDES (FROM App TO Schema, schema_role STRING)
  `);
  
  // Weather Service登録
  await conn.query(`
    CREATE (:LocationURI {id: 'weather/v1'})
  `);
  await conn.query(`
    CREATE (:App {id: 'weather-service-v1'})
  `);
  await conn.query(`
    CREATE (:Schema {
      id: 'weather-output-schema',
      schema_content: '{"type": "object", "properties": {"temp": {"type": "number"}}}'
    })
  `);
  
  // リレーション作成
  await conn.query(`
    MATCH (uri:LocationURI {id: 'weather/v1'})
    MATCH (app:App {id: 'weather-service-v1'})
    CREATE (uri)-[:LOCATES]->(app)
  `);
  
  await conn.query(`
    MATCH (app:App {id: 'weather-service-v1'})
    MATCH (schema:Schema {id: 'weather-output-schema'})
    CREATE (app)-[:PROVIDES {schema_role: 'output'}]->(schema)
  `);
  
  // 検証
  const result = await conn.query(`
    MATCH (uri:LocationURI)-[:LOCATES]->(app:App)-[:PROVIDES]->(schema:Schema)
    WHERE uri.id = 'weather/v1'
    RETURN app.id, schema.id, schema.schema_content
  `);
  
  const rows = await result.getAll();
  assertEquals(rows.length, 1);
  assertEquals(rows[0]["app.id"], "weather-service-v1");
  assertEquals(rows[0]["schema.id"], "weather-output-schema");
});

Deno.test("Contract Service - Consumer Registration and Matching", async () => {
  const db = await createDatabase(":memory:");
  const conn = await createConnection(db);
  
  // スキーマ作成（完全版）
  await conn.query(`
    CREATE NODE TABLE LocationURI (id STRING, PRIMARY KEY (id))
  `);
  await conn.query(`
    CREATE NODE TABLE App (id STRING, endpoint STRING, PRIMARY KEY (id))
  `);
  await conn.query(`
    CREATE NODE TABLE Schema (id STRING, schema_content STRING, PRIMARY KEY (id))
  `);
  await conn.query(`
    CREATE REL TABLE LOCATES (FROM LocationURI TO App)
  `);
  await conn.query(`
    CREATE REL TABLE PROVIDES (FROM App TO Schema, schema_role STRING)
  `);
  await conn.query(`
    CREATE REL TABLE EXPECTS (FROM App TO Schema, schema_role STRING)
  `);
  await conn.query(`
    CREATE REL TABLE CAN_COMMUNICATE_WITH (FROM App TO App, transform_rules STRING, compatibility_score DOUBLE)
  `);
  
  // Provider登録
  await conn.query(`
    CREATE (:App {id: 'weather-service-v1', endpoint: 'http://weather:8080'})
  `);
  await conn.query(`
    CREATE (:Schema {
      id: 'weather-output-schema',
      schema_content: '{"type": "object", "properties": {"temp": {"type": "number"}}}'
    })
  `);
  await conn.query(`
    MATCH (app:App {id: 'weather-service-v1'})
    MATCH (schema:Schema {id: 'weather-output-schema'})
    CREATE (app)-[:PROVIDES {schema_role: 'output'}]->(schema)
  `);
  
  // Consumer登録
  await conn.query(`
    CREATE (:App {id: 'dashboard-v2', endpoint: 'http://dashboard:3000'})
  `);
  await conn.query(`
    CREATE (:Schema {
      id: 'dashboard-expects-schema',
      schema_content: '{"type": "object", "properties": {"temperature": {"type": "number"}}}'
    })
  `);
  await conn.query(`
    MATCH (app:App {id: 'dashboard-v2'})
    MATCH (schema:Schema {id: 'dashboard-expects-schema'})
    CREATE (app)-[:EXPECTS {schema_role: 'output'}]->(schema)
  `);
  
  // 互換性リレーション作成
  await conn.query(`
    MATCH (consumer:App {id: 'dashboard-v2'})
    MATCH (provider:App {id: 'weather-service-v1'})
    CREATE (consumer)-[:CAN_COMMUNICATE_WITH {
      transform_rules: '{"temp": "temperature"}',
      compatibility_score: 0.95
    }]->(provider)
  `);
  
  // ルーティング検証
  const result = await conn.query(`
    MATCH (consumer:App {id: 'dashboard-v2'})-[rel:CAN_COMMUNICATE_WITH]->(provider:App)
    RETURN provider.id, provider.endpoint, rel.transform_rules, rel.compatibility_score
    ORDER BY rel.compatibility_score DESC
    LIMIT 1
  `);
  
  const rows = await result.getAll();
  assertEquals(rows.length, 1);
  assertEquals(rows[0]["provider.id"], "weather-service-v1");
  assertEquals(rows[0]["provider.endpoint"], "http://weather:8080");
  assertEquals(rows[0]["rel.transform_rules"], '{"temp": "temperature"}');
  assertEquals(rows[0]["rel.compatibility_score"], 0.95);
});

Deno.test("Import verification - Connection is exported", async () => {
  // 名前付きインポートが動作することを確認
  const { Database, Connection } = await import("kuzu");
  
  assertExists(Database, "Database is exported");
  assertExists(Connection, "Connection is exported");
  
  // インスタンス作成が可能
  const db = new Database(":memory:");
  assertExists(db);
  
  const conn = new Connection(db);
  assertExists(conn);
  assertEquals(typeof conn.query, "function", "Connection has query method");
});