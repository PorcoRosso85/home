/**
 * Bun client tests
 */

import { expect, test, describe, beforeAll, afterAll } from "bun:test";
import { KuzuSyncClient } from "./bun_client.ts";

describe("KuzuSyncClient", () => {
  let client: KuzuSyncClient;

  beforeAll(async () => {
    client = new KuzuSyncClient("test_client");
    await client.initialize();
  });

  afterAll(() => {
    client.close();
  });

  test("initializes with unique clientId", () => {
    const client1 = new KuzuSyncClient();
    const client2 = new KuzuSyncClient();
    expect(client1).toBeDefined();
    expect(client2).toBeDefined();
    // Auto-generated IDs should be different
    expect(client1).not.toBe(client2);
  });

  test("stores events locally", async () => {
    await client.sendEvent("TEST_EVENT", { value: 42 });
    
    const events = await client.getLocalEvents();
    expect(events.length).toBeGreaterThan(0);
    
    const lastEvent = events[0];
    expect(lastEvent.template).toBe("TEST_EVENT");
    expect(lastEvent.params.value).toBe(42);
    expect(lastEvent.synced).toBe(false); // Not connected to server
  });

  test("maintains event structure compatibility", async () => {
    await client.sendEvent("USER_ACTION", { 
      action: "login", 
      user: "test_user" 
    });
    
    const events = await client.getLocalEvents(1);
    const event = events[0];
    
    // Same structure as Deno version
    expect(event).toHaveProperty("id");
    expect(event).toHaveProperty("template");
    expect(event).toHaveProperty("params");
    expect(event).toHaveProperty("timestamp");
    expect(event).toHaveProperty("synced");
    
    // Types match
    expect(typeof event.id).toBe("string");
    expect(typeof event.template).toBe("string");
    expect(typeof event.params).toBe("object");
    expect(typeof event.timestamp).toBe("number");
    expect(typeof event.synced).toBe("boolean");
  });

  test("KuzuDB works in Bun", async () => {
    // Use require pattern for Bun
    const kuzu = require("kuzu");
    const { Database, Connection } = kuzu;
    const db = new Database(":memory:");
    const conn = new Connection(db);
    
    await conn.query(`CREATE NODE TABLE Test(id INT64, PRIMARY KEY(id))`);
    await conn.query(`CREATE (:Test {id: 1})`);
    
    // Use getAll() with column alias for Bun compatibility
    const result = await conn.query(`MATCH (t:Test) RETURN t.id as id`);
    const rows = await result.getAll();
    expect(rows.length).toBe(1);
    expect(rows[0].id).toBe(1);
    
    conn.close();
  });
});