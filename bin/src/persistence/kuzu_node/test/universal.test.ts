import { describe, it, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { UniversalKuzu } from "../src/kuzu-universal";

describe("UniversalKuzu - Universal Implementation", () => {
  let kuzu: UniversalKuzu;

  beforeEach(async () => {
    kuzu = new UniversalKuzu();
    await kuzu.initialize();
  });

  afterEach(async () => {
    await kuzu.cleanup();
  });

  describe("Environment Detection", () => {
    it("should detect the current environment", () => {
      const env = UniversalKuzu.getEnvironment();
      assert.ok(['browser', 'node'].includes(env));
      console.log(`Running in: ${env} environment`);
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
      assert.strictEqual(result.name, "Alice");
    });

    it("should support queryObjects method", async () => {
      await kuzu.executeMany([
        "CREATE (:Person {id: 2, name: 'Bob', age: 25})",
        "CREATE (:Person {id: 3, name: 'Charlie', age: 35})"
      ]);

      const people = await kuzu.queryObjects(
        "MATCH (p:Person) RETURN p.id as id, p.name as name, p.age as age ORDER BY p.id"
      );

      assert.strictEqual(people.length, 3);
      assert.strictEqual(people[0].name, "Alice");
      assert.strictEqual(people[1].name, "Bob");
      assert.strictEqual(people[2].name, "Charlie");
    });

    it("should support queryOne method", async () => {
      const oldest = await kuzu.queryOne(
        "MATCH (p:Person) RETURN p.name as name, p.age as age ORDER BY p.age DESC LIMIT 1"
      );

      assert.strictEqual(oldest.name, "Charlie");
      assert.strictEqual(oldest.age, 35);
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
      assert.strictEqual(beforeRollback?.name, "Transient");
      
      // Rollback
      await kuzu.rollback();
      
      // Verify it's gone after rollback
      const afterRollback = await kuzu.queryOne(
        "MATCH (p:Person {id: 99}) RETURN p.name as name"
      );
      assert.strictEqual(afterRollback, null);
    });

    it("should commit transactions", async () => {
      await kuzu.beginTransaction();
      await kuzu.query("CREATE (:City {name: 'Tokyo', population: 14000000})");
      await kuzu.commit();
      
      const city = await kuzu.queryOne(
        "MATCH (c:City {name: 'Tokyo'}) RETURN c.population as pop"
      );
      assert.strictEqual(city.pop, 14000000);
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

      assert.strictEqual(results.length, 2);
      assert.deepStrictEqual(results[0], { person: "Alice", city: "Tokyo" });
      assert.deepStrictEqual(results[1], { person: "Bob", city: "Paris" });
    });

    it("should handle aggregations", async () => {
      const stats = await kuzu.queryOne(
        "MATCH (p:Person) RETURN count(*) as total, avg(p.age) as avgAge"
      );

      assert.strictEqual(stats.total, 3);
      assert.strictEqual(stats.avgAge, 30);
    });
  });
});