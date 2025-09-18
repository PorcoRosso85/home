import { describe, it, expect } from 'vitest';

const kuzu = require("kuzu-wasm/nodejs");

describe("Simple KuzuDB Test", () => {
  it("should create and query database without cleanup", async () => {
    console.log("Creating database...");
    const db = new kuzu.Database(":memory:", 1 << 28);
    const conn = new kuzu.Connection(db, 4);
    
    console.log("Creating table...");
    const result = await conn.query(
      "CREATE NODE TABLE Test(id INT64, PRIMARY KEY(id))"
    );
    await result.close();
    
    console.log("Inserting data...");
    const insertResult = await conn.query("CREATE (:Test {id: 1})");
    await insertResult.close();
    
    console.log("Querying data...");
    const queryResult = await conn.query("MATCH (t:Test) RETURN t.id");
    const rows = await queryResult.getAllObjects();
    await queryResult.close();
    
    expect(rows).toHaveLength(1);
    // Handle Number object from kuzu-wasm
    const id = rows[0]["t.id"];
    expect(Number(id)).toBe(1);
    
    console.log("Closing connection...");
    await conn.close();
    
    console.log("Closing database...");
    await db.close();
    
    console.log("Test completed successfully");
    // Skip kuzu.close() to avoid timeout
  });
});