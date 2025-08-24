import { describe, it, expect, beforeAll, afterAll } from "bun:test";
import * as kuzu from "kuzu-wasm";

describe("KuzuDB with Bun", () => {
  let db: any;
  let conn: any;

  beforeAll(async () => {
    console.log("Initializing in-memory database...");
    db = new kuzu.Database(":memory:", 1 << 28 /* 256MB */);
    conn = new kuzu.Connection(db, 4);
  });

  afterAll(async () => {
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
      expect(result).toBeDefined();
      await result.close();
    });

    it("should create edge tables", async () => {
      const result = await conn.query(
        "CREATE REL TABLE Knows(FROM Person TO Person, since INT64)"
      );
      expect(result).toBeDefined();
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
        expect(result).toBeDefined();
        await result.close();
      }
    });

    it("should insert edges", async () => {
      const result = await conn.query(
        "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:Knows {since: 2020}]->(b)"
      );
      expect(result).toBeDefined();
      await result.close();
    });

    it("should query nodes", async () => {
      const result = await conn.query("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
      const rows = await result.getAllObjects();
      
      expect(rows).toHaveLength(3);
      expect(rows[0]["p.name"]).toBe("Bob");
      expect(rows[0]["p.age"]).toBe(25);
      expect(rows[1]["p.name"]).toBe("Alice");
      expect(rows[1]["p.age"]).toBe(30);
      expect(rows[2]["p.name"]).toBe("Charlie");
      expect(rows[2]["p.age"]).toBe(35);
      
      await result.close();
    });

    it("should query relationships", async () => {
      const result = await conn.query(
        "MATCH (a:Person)-[k:Knows]->(b:Person) RETURN a.name, k.since, b.name"
      );
      const rows = await result.getAllObjects();
      
      expect(rows).toHaveLength(1);
      expect(rows[0]["a.name"]).toBe("Alice");
      expect(rows[0]["k.since"]).toBe(2020);
      expect(rows[0]["b.name"]).toBe("Bob");
      
      await result.close();
    });
  });

  describe("Aggregation Operations", () => {
    it("should perform count aggregation", async () => {
      const result = await conn.query("MATCH (p:Person) RETURN count(*) as total");
      const rows = await result.getAllObjects();
      
      expect(rows[0]["total"]).toBe(3);
      
      await result.close();
    });

    it("should perform avg aggregation", async () => {
      const result = await conn.query("MATCH (p:Person) RETURN avg(p.age) as avg_age");
      const rows = await result.getAllObjects();
      
      expect(rows[0]["avg_age"]).toBe(30);
      
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
      expect(rows[0]["p.age"]).toBe(40);
      await checkResult.close();
      
      await conn.query("ROLLBACK");
      
      const afterRollback = await conn.query("MATCH (p:Person {name: 'David'}) RETURN p.age");
      const rowsAfter = await afterRollback.getAllObjects();
      expect(rowsAfter).toHaveLength(0);
      await afterRollback.close();
    });
  });
});