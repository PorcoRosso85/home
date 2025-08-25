import { describe, it, beforeEach, afterEach, expect } from "vitest";

// For Node.js environment
const kuzu = require("kuzu-wasm/nodejs");

describe("KuzuDB with Vitest", () => {
  let db: any;
  let conn: any;

  beforeEach(async () => {
    console.log("Initializing in-memory database...");
    db = new kuzu.Database(":memory:", 1 << 28 /* 256MB */);
    conn = new kuzu.Connection(db, 4);
    
    // Create schema for all tests that need it
    const schemaResult = await conn.query(
      "CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))"
    );
    await schemaResult.close();
    
    const relResult = await conn.query(
      "CREATE REL TABLE Knows(FROM Person TO Person, since INT64)"
    );
    await relResult.close();
  });

  afterEach(async () => {
    console.log("Cleaning up...");
    await conn.close();
    await db.close();
    // Skip kuzu.close() to avoid timeout issues
  });

  describe("Schema Operations", () => {
    it("should verify table creation", async () => {
      // Tables are created in beforeEach, just verify they work
      const result = await conn.query("CREATE (:Person {name: 'Test', age: 20})");
      expect(result).toBeTruthy();
      await result.close();
      
      const query = await conn.query("MATCH (p:Person {name: 'Test'}) RETURN p.age");
      const rows = await query.getAllObjects();
      expect(Number(rows[0]["p.age"])).toBe(20);
      await query.close();
    });

    it("should verify relationship creation", async () => {
      // Create test nodes
      await conn.query("CREATE (:Person {name: 'A', age: 30})");
      await conn.query("CREATE (:Person {name: 'B', age: 40})");
      
      // Create relationship
      const result = await conn.query(
        "MATCH (a:Person {name: 'A'}), (b:Person {name: 'B'}) CREATE (a)-[:Knows {since: 2023}]->(b)"
      );
      expect(result).toBeTruthy();
      await result.close();
    });
  });

  describe("Data Operations", () => {
    beforeEach(async () => {
      // Insert test data for this suite
      const insertQueries = [
        "CREATE (:Person {name: 'Alice', age: 30})",
        "CREATE (:Person {name: 'Bob', age: 25})",
        "CREATE (:Person {name: 'Charlie', age: 35})"
      ];

      for (const query of insertQueries) {
        const result = await conn.query(query);
        await result.close();
      }
    });
    
    it("should insert nodes", async () => {
      // Just verify the data is there
      const result = await conn.query("MATCH (p:Person) RETURN count(*) as count");
      const rows = await result.getAllObjects();
      expect(Number(rows[0]["count"])).toBe(3);
      await result.close();
    });

    it("should insert edges", async () => {
      const result = await conn.query(
        "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:Knows {since: 2020}]->(b)"
      );
      expect(result).toBeTruthy();
      await result.close();
    });

    it("should query nodes", async () => {
      const result = await conn.query("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
      const rows = await result.getAllObjects();
      
      expect(rows).toHaveLength(3);
      expect(rows[0]["p.name"]).toBe("Bob");
      expect(Number(rows[0]["p.age"])).toBe(25);
      expect(rows[1]["p.name"]).toBe("Alice");
      expect(Number(rows[1]["p.age"])).toBe(30);
      expect(rows[2]["p.name"]).toBe("Charlie");
      expect(Number(rows[2]["p.age"])).toBe(35);
      
      await result.close();
    });

    it("should query relationships", async () => {
      // First create the relationship
      const createResult = await conn.query(
        "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:Knows {since: 2020}]->(b)"
      );
      await createResult.close();
      
      // Then query it
      const result = await conn.query(
        "MATCH (a:Person)-[k:Knows]->(b:Person) RETURN a.name, k.since, b.name"
      );
      const rows = await result.getAllObjects();
      
      expect(rows).toHaveLength(1);
      expect(rows[0]["a.name"]).toBe("Alice");
      expect(Number(rows[0]["k.since"])).toBe(2020);
      expect(rows[0]["b.name"]).toBe("Bob");
      
      await result.close();
    });
  });

  describe("Aggregation Operations", () => {
    beforeEach(async () => {
      // Insert test data for aggregation
      const insertQueries = [
        "CREATE (:Person {name: 'Alice', age: 30})",
        "CREATE (:Person {name: 'Bob', age: 25})",
        "CREATE (:Person {name: 'Charlie', age: 35})"
      ];

      for (const query of insertQueries) {
        const result = await conn.query(query);
        await result.close();
      }
    });

    it("should perform count aggregation", async () => {
      const result = await conn.query("MATCH (p:Person) RETURN count(*) as total");
      const rows = await result.getAllObjects();
      
      expect(Number(rows[0]["total"])).toBe(3);
      
      await result.close();
    });

    it("should perform avg aggregation", async () => {
      const result = await conn.query("MATCH (p:Person) RETURN avg(p.age) as avg_age");
      const rows = await result.getAllObjects();
      
      expect(Number(rows[0]["avg_age"])).toBe(30);
      
      await result.close();
    });
  });

  describe("Transaction Operations", () => {
    beforeEach(async () => {
      // Insert initial data for transaction tests
      const result = await conn.query("CREATE (:Person {name: 'Alice', age: 30})");
      await result.close();
    });

    it("should support transactions", async () => {
      await conn.query("BEGIN TRANSACTION");
      
      const result1 = await conn.query("CREATE (:Person {name: 'David', age: 40})");
      await result1.close();
      
      const checkResult = await conn.query("MATCH (p:Person {name: 'David'}) RETURN p.age");
      const rows = await checkResult.getAllObjects();
      expect(Number(rows[0]["p.age"])).toBe(40);
      await checkResult.close();
      
      await conn.query("ROLLBACK");
      
      const afterRollback = await conn.query("MATCH (p:Person {name: 'David'}) RETURN p.age");
      const rowsAfter = await afterRollback.getAllObjects();
      expect(rowsAfter).toHaveLength(0);
      await afterRollback.close();
    });
  });
});