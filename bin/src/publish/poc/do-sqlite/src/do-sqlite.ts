/**
 * Durable Object with SQLite storage
 * 概念実証: Durable ObjectsでのSQLite利用
 */

export class SQLiteDurableObject {
  private state: DurableObjectState;
  private sql: SqlStorage;

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
    this.sql = state.storage.sql;
    
    // Initialize schema on first run
    this.state.blockConcurrencyWhile(async () => {
      await this.initializeSchema();
    });
  }

  async initializeSchema() {
    // Create table if not exists
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS kv_store (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        created_at INTEGER DEFAULT (unixepoch()),
        updated_at INTEGER DEFAULT (unixepoch())
      )
    `);
    
    // Create index for timestamp queries
    this.sql.exec(`
      CREATE INDEX IF NOT EXISTS idx_updated_at ON kv_store(updated_at)
    `);
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "GET" && path === "/get") {
      const key = url.searchParams.get("key");
      if (!key) {
        return new Response("Missing key parameter", { status: 400 });
      }
      
      const result = this.sql.exec(`
        SELECT value FROM kv_store WHERE key = ?
      `, key).toArray();
      
      if (result.length === 0) {
        return new Response("Key not found", { status: 404 });
      }
      
      return new Response(result[0].value as string);
    }

    if (request.method === "POST" && path === "/set") {
      const { key, value } = await request.json<{ key: string; value: string }>();
      
      if (!key || !value) {
        return new Response("Missing key or value", { status: 400 });
      }
      
      this.sql.exec(`
        INSERT INTO kv_store (key, value) 
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET 
          value = excluded.value,
          updated_at = unixepoch()
      `, key, value);
      
      return new Response("OK");
    }

    if (request.method === "GET" && path === "/list") {
      const limit = parseInt(url.searchParams.get("limit") || "10");
      const results = this.sql.exec(`
        SELECT key, value, updated_at 
        FROM kv_store 
        ORDER BY updated_at DESC 
        LIMIT ?
      `, limit).toArray();
      
      return Response.json(results);
    }

    if (request.method === "DELETE" && path === "/delete") {
      const key = url.searchParams.get("key");
      if (!key) {
        return new Response("Missing key parameter", { status: 400 });
      }
      
      const result = this.sql.exec(`
        DELETE FROM kv_store WHERE key = ?
      `, key);
      
      return new Response("OK");
    }

    return new Response("Not found", { status: 404 });
  }
}