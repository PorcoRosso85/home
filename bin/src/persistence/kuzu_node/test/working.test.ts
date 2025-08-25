import { test } from "node:test";
import assert from "node:assert/strict";
import {
  loadKuzu,
  detectEnvironment,
  createKuzuDatabase,
  cleanupKuzu,
  executeQuery,
  executeQueries,
  queryOne,
  createSchema,
  loadData,
  beginTransaction,
  commitTransaction,
  rollbackTransaction
} from "../mod";

test("Environment Detection", () => {
  const env = detectEnvironment();
  assert.strictEqual(env, 'node');
});

test("Basic database operations", async () => {
  const kuzu = await loadKuzu();
  const { db, conn } = createKuzuDatabase(kuzu);
  
  try {
    await createSchema(conn, [
      "CREATE NODE TABLE Person(id INT64, name STRING, age INT64, PRIMARY KEY(id))"
    ]);
    
    await loadData(conn, [
      "CREATE (:Person {id: 1, name: 'Alice', age: 30})",
      "CREATE (:Person {id: 2, name: 'Bob', age: 25})"
    ]);
    
    const results = await executeQuery(conn, 
      "MATCH (p:Person) RETURN p.id as id, p.name as name, p.age as age ORDER BY p.id"
    );
    
    assert.strictEqual(results.length, 2);
    assert.strictEqual(results[0].name, 'Alice');
    assert.strictEqual(results[1].name, 'Bob');
  } finally {
    await cleanupKuzu({ conn, db, kuzu });
  }
});

test("queryOne function", async () => {
  const kuzu = await loadKuzu();
  const { db, conn } = createKuzuDatabase(kuzu);
  
  try {
    await createSchema(conn, [
      "CREATE NODE TABLE City(name STRING, population INT64, PRIMARY KEY(name))"
    ]);
    
    await loadData(conn, [
      "CREATE (:City {name: 'Tokyo', population: 14000000})",
      "CREATE (:City {name: 'Osaka', population: 2700000})"
    ]);
    
    const result = await queryOne(conn, 
      "MATCH (c:City) RETURN c.name as name ORDER BY c.population DESC LIMIT 1"
    );
    
    assert.strictEqual(result.name, 'Tokyo');
  } finally {
    await cleanupKuzu({ conn, db, kuzu });
  }
});

test("Transaction rollback", async () => {
  const kuzu = await loadKuzu();
  const { db, conn } = createKuzuDatabase(kuzu);
  
  try {
    await createSchema(conn, [
      "CREATE NODE TABLE Counter(id INT64, value INT64, PRIMARY KEY(id))"
    ]);
    
    await loadData(conn, [
      "CREATE (:Counter {id: 1, value: 100})"
    ]);
    
    await beginTransaction(conn);
    await executeQueries(conn, [
      "MATCH (c:Counter {id: 1}) SET c.value = 200"
    ]);
    
    const inTxResult = await queryOne(conn, 
      "MATCH (c:Counter {id: 1}) RETURN c.value as value"
    );
    assert.strictEqual(inTxResult.value, 200);
    
    await rollbackTransaction(conn);
    
    const afterRollback = await queryOne(conn, 
      "MATCH (c:Counter {id: 1}) RETURN c.value as value"
    );
    assert.strictEqual(afterRollback.value, 100);
  } finally {
    await cleanupKuzu({ conn, db, kuzu });
  }
});

test("Transaction commit", async () => {
  const kuzu = await loadKuzu();
  const { db, conn } = createKuzuDatabase(kuzu);
  
  try {
    await createSchema(conn, [
      "CREATE NODE TABLE Product(id INT64, stock INT64, PRIMARY KEY(id))"
    ]);
    
    await loadData(conn, [
      "CREATE (:Product {id: 1, stock: 50})"
    ]);
    
    await beginTransaction(conn);
    await executeQueries(conn, [
      "MATCH (p:Product {id: 1}) SET p.stock = p.stock - 10"
    ]);
    await commitTransaction(conn);
    
    const result = await queryOne(conn, 
      "MATCH (p:Product {id: 1}) RETURN p.stock as stock"
    );
    assert.strictEqual(result.stock, 40);
  } finally {
    await cleanupKuzu({ conn, db, kuzu });
  }
});

test("Relationships", async () => {
  const kuzu = await loadKuzu();
  const { db, conn } = createKuzuDatabase(kuzu);
  
  try {
    await createSchema(conn, [
      "CREATE NODE TABLE User(id INT64, name STRING, PRIMARY KEY(id))",
      "CREATE REL TABLE Follows(FROM User TO User, since DATE)"
    ]);
    
    await loadData(conn, [
      "CREATE (:User {id: 1, name: 'Alice'})",
      "CREATE (:User {id: 2, name: 'Bob'})",
      "CREATE (:User {id: 3, name: 'Charlie'})",
      "MATCH (a:User {id: 1}), (b:User {id: 2}) CREATE (a)-[:Follows {since: date('2023-01-01')}]->(b)",
      "MATCH (b:User {id: 2}), (c:User {id: 3}) CREATE (b)-[:Follows {since: date('2023-06-01')}]->(c)"
    ]);
    
    const results = await executeQuery(conn, `
      MATCH (u1:User)-[f:Follows]->(u2:User)
      RETURN u1.name as follower, u2.name as followed
      ORDER BY u1.id
    `);
    
    assert.strictEqual(results.length, 2);
    assert.strictEqual(results[0].follower, 'Alice');
    assert.strictEqual(results[0].followed, 'Bob');
  } finally {
    await cleanupKuzu({ conn, db, kuzu });
  }
});

test("Aggregations", async () => {
  const kuzu = await loadKuzu();
  const { db, conn } = createKuzuDatabase(kuzu);
  
  try {
    await createSchema(conn, [
      "CREATE NODE TABLE Sale(id INT64, amount DOUBLE, category STRING, PRIMARY KEY(id))"
    ]);
    
    await loadData(conn, [
      "CREATE (:Sale {id: 1, amount: 100.0, category: 'Electronics'})",
      "CREATE (:Sale {id: 2, amount: 200.0, category: 'Electronics'})",
      "CREATE (:Sale {id: 3, amount: 150.0, category: 'Books'})"
    ]);
    
    const result = await queryOne(conn, `
      MATCH (s:Sale)
      WHERE s.category = 'Electronics'
      RETURN count(*) as count, sum(s.amount) as total, avg(s.amount) as average
    `);
    
    assert.strictEqual(result.count, 2);
    assert.strictEqual(result.total, 300.0);
    assert.strictEqual(result.average, 150.0);
  } finally {
    await cleanupKuzu({ conn, db, kuzu });
  }
});

test("Application layer - runInMemoryExample", async () => {
  const { runInMemoryExample } = await import("../application");
  const results = await runInMemoryExample();
  
  assert.strictEqual(results.length, 2);
  assert.strictEqual(results[0]['p.name'], 'Bob');
  assert.strictEqual(results[0]['p.age'], 25);
  assert.strictEqual(results[1]['p.name'], 'Alice');
  assert.strictEqual(results[1]['p.age'], 30);
});