import { describe, it, expect, beforeAll, afterAll } from "bun:test";
import { UniversalKuzu } from "../src/kuzu-universal";

describe("UniversalKuzu - Universal Implementation", () => {
  let kuzu: UniversalKuzu;

  beforeAll(async () => {
    kuzu = new UniversalKuzu();
    await kuzu.initialize();
  });

  afterAll(async () => {
    await kuzu.cleanup();
  });

  describe("Environment Detection", () => {
    it("should detect the current environment", () => {
      const env = UniversalKuzu.getEnvironment();
      expect(['browser', 'bun', 'node']).toContain(env);
      console.log(`Running in: ${env} environment`);
    });

    it("should correctly identify Bun runtime", () => {
      // In Bun test environment
      if (typeof Bun !== 'undefined') {
        expect(UniversalKuzu.isBun()).toBe(true);
        expect(UniversalKuzu.isBrowser()).toBe(false);
      }
    });
  });

  describe("Database Operations", () => {
    it("should create schema", async () => {
      const schemaStatements = [
        "CREATE NODE TABLE Person(id INT64, name STRING, age INT64, PRIMARY KEY(id))",
        "CREATE NODE TABLE City(name STRING, population INT64, PRIMARY KEY(name))",
        "CREATE REL TABLE LivesIn(FROM Person TO City)"
      ];

      await kuzu.createSchema(schemaStatements);
      
      // Verify by inserting data
      await kuzu.query("CREATE (:Person {id: 1, name: 'Alice', age: 30})");
      const result = await kuzu.queryOne("MATCH (p:Person) RETURN p.name as name");
      expect(result.name).toBe("Alice");
    });

    it("should support queryObjects method", async () => {
      await kuzu.executeMany([
        "CREATE (:Person {id: 2, name: 'Bob', age: 25})",
        "CREATE (:Person {id: 3, name: 'Charlie', age: 35})"
      ]);

      const people = await kuzu.queryObjects(
        "MATCH (p:Person) RETURN p.id as id, p.name as name, p.age as age ORDER BY p.id"
      );

      expect(people).toHaveLength(3);
      expect(people[0].name).toBe("Alice");
      expect(people[1].name).toBe("Bob");
      expect(people[2].name).toBe("Charlie");
    });

    it("should support queryOne method", async () => {
      const oldest = await kuzu.queryOne(
        "MATCH (p:Person) RETURN p.name as name, p.age as age ORDER BY p.age DESC LIMIT 1"
      );

      expect(oldest.name).toBe("Charlie");
      expect(oldest.age).toBe(35);
    });
  });

  describe("Transaction Support", () => {
    it("should handle transactions", async () => {
      await kuzu.beginTransaction();
      
      // Add a person in transaction
      await kuzu.query("CREATE (:Person {id: 99, name: 'Transient', age: 99})");
      
      // Verify it exists in transaction
      const beforeRollback = await kuzu.queryOne(
        "MATCH (p:Person {id: 99}) RETURN p.name as name"
      );
      expect(beforeRollback?.name).toBe("Transient");
      
      // Rollback
      await kuzu.rollback();
      
      // Verify it's gone after rollback
      const afterRollback = await kuzu.queryOne(
        "MATCH (p:Person {id: 99}) RETURN p.name as name"
      );
      expect(afterRollback).toBeNull();
    });

    it("should commit transactions", async () => {
      await kuzu.beginTransaction();
      await kuzu.query("CREATE (:City {name: 'Tokyo', population: 14000000})");
      await kuzu.commit();
      
      const city = await kuzu.queryOne(
        "MATCH (c:City {name: 'Tokyo'}) RETURN c.population as pop"
      );
      expect(city.pop).toBe(14000000);
    });
  });

  describe("Complex Queries", () => {
    it("should handle relationships", async () => {
      // Create relationships
      await kuzu.executeMany([
        "MATCH (p:Person {name: 'Alice'}), (c:City {name: 'Tokyo'}) CREATE (p)-[:LivesIn]->(c)",
        "CREATE (:City {name: 'Paris', population: 2200000})",
        "MATCH (p:Person {name: 'Bob'}), (c:City {name: 'Paris'}) CREATE (p)-[:LivesIn]->(c)"
      ]);

      // Query relationships
      const results = await kuzu.queryObjects(
        "MATCH (p:Person)-[:LivesIn]->(c:City) RETURN p.name as person, c.name as city ORDER BY p.name"
      );

      expect(results).toHaveLength(2);
      expect(results[0]).toEqual({ person: "Alice", city: "Tokyo" });
      expect(results[1]).toEqual({ person: "Bob", city: "Paris" });
    });

    it("should handle aggregations", async () => {
      const stats = await kuzu.queryOne(
        "MATCH (p:Person) RETURN count(*) as total, avg(p.age) as avgAge"
      );

      expect(stats.total).toBe(3);
      expect(stats.avgAge).toBe(30);
    });
  });
});