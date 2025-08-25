import { describe, it, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";

// For Node.js environment
const kuzu = require("kuzu-wasm/nodejs");

describe("KuzuDB with Node.js", () => {
  let db: any;
  let conn: any;

  beforeEach(async () => {
    console.log("Initializing in-memory database...");
    db = new kuzu.Database(":memory:", 1 << 28 /* 256MB */);
    conn = new kuzu.Connection(db, 4);
  });

  afterEach(async () => {
    console.log("Cleaning up...");
    await conn.close();
    await db.close();
    await kuzu.close();
  });

  describe("Schema Operations", () => {
    it("should create node tables", async () => {
      const result = await conn.query(
        "CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))"
      );
      assert.ok(result);
      await result.close();
    });

    it("should create edge tables", async () => {
      const result = await conn.query(
        "CREATE REL TABLE Knows(FROM Person TO Person, since INT64)"
      );
      assert.ok(result);
      await result.close();
    });
  });

  describe("Data Operations", () => {
    it("should insert nodes", async () => {
      const insertQueries = [
        "CREATE (:Person {name: 'Alice', age: 30})",
        "CREATE (:Person {name: 'Bob', age: 25})",
        "CREATE (:Person {name: 'Charlie', age: 35})"
      ];

      for (const query of insertQueries) {
        const result = await conn.query(query);
        assert.ok(result);
        await result.close();
      }
    });

    it("should insert edges", async () => {
      const result = await conn.query(
        "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:Knows {since: 2020}]->(b)"
      );
      assert.ok(result);
      await result.close();
    });

    it("should query nodes", async () => {
      const result = await conn.query("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
      const rows = await result.getAllObjects();
      
      assert.strictEqual(rows.length, 3);
      assert.strictEqual(rows[0]["p.name"], "Bob");
      assert.strictEqual(rows[0]["p.age"], 25);
      assert.strictEqual(rows[1]["p.name"], "Alice");
      assert.strictEqual(rows[1]["p.age"], 30);
      assert.strictEqual(rows[2]["p.name"], "Charlie");
      assert.strictEqual(rows[2]["p.age"], 35);
      
      await result.close();
    });

    it("should query relationships", async () => {
      const result = await conn.query(
        "MATCH (a:Person)-[k:Knows]->(b:Person) RETURN a.name, k.since, b.name"
      );
      const rows = await result.getAllObjects();
      
      assert.strictEqual(rows.length, 1);
      assert.strictEqual(rows[0]["a.name"], "Alice");
      assert.strictEqual(rows[0]["k.since"], 2020);
      assert.strictEqual(rows[0]["b.name"], "Bob");
      
      await result.close();
    });
  });

  describe("Aggregation Operations", () => {
    it("should perform count aggregation", async () => {
      const result = await conn.query("MATCH (p:Person) RETURN count(*) as total");
      const rows = await result.getAllObjects();
      
      assert.strictEqual(rows[0]["total"], 3);
      
      await result.close();
    });

    it("should perform avg aggregation", async () => {
      const result = await conn.query("MATCH (p:Person) RETURN avg(p.age) as avg_age");
      const rows = await result.getAllObjects();
      
      assert.strictEqual(rows[0]["avg_age"], 30);
      
      await result.close();
    });
  });

  describe("Transaction Operations", () => {
    it("should support transactions", async () => {
      await conn.query("BEGIN TRANSACTION");
      
      const result1 = await conn.query("CREATE (:Person {name: 'David', age: 40})");
      await result1.close();
      
      const checkResult = await conn.query("MATCH (p:Person {name: 'David'}) RETURN p.age");
      const rows = await checkResult.getAllObjects();
      assert.strictEqual(rows[0]["p.age"], 40);
      await checkResult.close();
      
      await conn.query("ROLLBACK");
      
      const afterRollback = await conn.query("MATCH (p:Person {name: 'David'}) RETURN p.age");
      const rowsAfter = await afterRollback.getAllObjects();
      assert.strictEqual(rowsAfter.length, 0);
      await afterRollback.close();
    });
  });
});