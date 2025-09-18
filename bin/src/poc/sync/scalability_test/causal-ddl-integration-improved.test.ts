import { assertEquals, assert } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createCausalSyncClient, disconnect } from "./causal-sync-client.ts";

// Track all clients and intervals for cleanup
const activeClients: any[] = [];
const activeIntervals: number[] = [];

// Helper function to create test clients with tracking
async function createTestClient(clientId: string) {
  const client = await createCausalSyncClient({
    clientId,
    dbPath: `:memory:`,
    wsUrl: "ws://localhost:8083",
  });
  activeClients.push(client);
  
  // Track cleanup timer
  if (client._internal?.cleanupTimer) {
    activeIntervals.push(client._internal.cleanupTimer);
  }
  
  return client;
}

// Comprehensive cleanup function
async function cleanupAll() {
  // 1. Disconnect all clients gracefully
  for (const client of activeClients) {
    try {
      await disconnect(client);
    } catch (e) {
      // Ignore disconnection errors
    }
  }
  
  // 2. Clear all intervals
  for (const interval of activeIntervals) {
    clearInterval(interval);
  }
  
  // 3. Clear arrays
  activeClients.length = 0;
  activeIntervals.length = 0;
  
  // 4. Wait for pending operations to complete
  await new Promise(resolve => setTimeout(resolve, 100));
}

// Helper delay function
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

Deno.test("DDL Integration Tests - Improved", async (t) => {
  
  await t.step("should handle DDL operations with causal ordering", async () => {
    try {
      const client = await createTestClient("ddl-client");

      // スキーマ作成
      await client.executeOperation({
        id: "create-table",
        type: "DDL",
        dependsOn: [],
        payload: {
          ddlType: "CREATE_TABLE",
          query: "CREATE NODE TABLE User (id STRING, name STRING, PRIMARY KEY(id))"
        },
        clientId: "ddl-client",
        timestamp: Date.now()
      });

      // カラム追加（テーブル作成に依存）
      await client.executeOperation({
        id: "add-email-column",
        type: "DDL",
        dependsOn: ["create-table"],
        payload: {
          ddlType: "ADD_COLUMN",
          query: "ALTER TABLE User ADD email STRING"
        },
        clientId: "ddl-client",
        timestamp: Date.now()
      });

      // Wait for operations to propagate
      await delay(100);

      // 期待: DDL操作が正しい順序で適用される
      const schema = await client.getSchemaVersion();
      assertEquals(Object.keys(schema.tables.User.columns), ["id", "name", "email"]);
    } finally {
      await cleanupAll();
    }
  });

  await t.step("should wait for schema before applying DML operations", async () => {
    try {
      const ddlClient = await createTestClient("ddl-client");
      const dmlClient = await createTestClient("dml-client");

      // DMLクライアントが先にデータ挿入を試みる（スキーマ未作成）
      const insertPromise = dmlClient.executeOperation({
        id: "insert-user",
        type: "DML",
        dependsOn: ["add-age-column"], // 存在しないカラムに依存
        payload: {
          query: "CREATE (u:User {id: 'u1', name: 'Alice', age: 30})"
        },
        clientId: "dml-client",
        timestamp: Date.now()
      });

      // しばらく待っても操作は適用されない
      await delay(500);
      const users = await dmlClient.query("MATCH (u:User) RETURN u");
      assertEquals(users.length, 0);

      // DDLクライアントがスキーマを作成
      await ddlClient.executeOperation({
        id: "create-user-table",
        type: "DDL",
        dependsOn: [],
        payload: {
          ddlType: "CREATE_TABLE",
          query: "CREATE NODE TABLE User (id STRING, name STRING, PRIMARY KEY(id))"
        },
        clientId: "ddl-client",
        timestamp: Date.now()
      });

      await ddlClient.executeOperation({
        id: "add-age-column",
        type: "DDL",
        dependsOn: ["create-user-table"],
        payload: {
          ddlType: "ADD_COLUMN",
          query: "ALTER TABLE User ADD age INT64"
        },
        clientId: "ddl-client",
        timestamp: Date.now()
      });

      // DML操作が自動的に適用される
      await insertPromise;
      await delay(200);
      
      const usersAfterDDL = await dmlClient.query("MATCH (u:User) RETURN u");
      assertEquals(usersAfterDDL.length, 1);
      assertEquals(usersAfterDDL[0].age, 30);
    } finally {
      await cleanupAll();
    }
  });

  await t.step("should handle ADD COLUMN IF NOT EXISTS", async () => {
    try {
      const client = await createTestClient("if-not-exists-client");

      // テーブル作成
      await client.executeOperation({
        id: "create-table",
        type: "DDL",
        dependsOn: [],
        payload: {
          ddlType: "CREATE_TABLE",
          query: "CREATE NODE TABLE Customer (id STRING, name STRING, PRIMARY KEY(id))"
        },
        clientId: "if-not-exists-client",
        timestamp: Date.now()
      });

      // 最初のカラム追加
      await client.executeOperation({
        id: "add-email-1",
        type: "DDL",
        dependsOn: ["create-table"],
        payload: {
          ddlType: "ADD_COLUMN",
          query: "ALTER TABLE Customer ADD email STRING"
        },
        clientId: "if-not-exists-client",
        timestamp: Date.now()
      });

      // 同じカラムをIF NOT EXISTSで追加（エラーにならない）
      await client.executeOperation({
        id: "add-email-2",
        type: "DDL",
        dependsOn: ["add-email-1"],
        payload: {
          ddlType: "ADD_COLUMN",
          query: "ALTER TABLE Customer ADD IF NOT EXISTS email STRING"
        },
        clientId: "if-not-exists-client",
        timestamp: Date.now()
      });

      await delay(100);

      // スキーマに変更がないことを確認
      const schema = await client.getSchemaVersion();
      assertEquals(Object.keys(schema.tables.Customer.columns), ["id", "name", "email"]);
    } finally {
      await cleanupAll();
    }
  });

  await t.step("should handle ADD COLUMN with DEFAULT value", async () => {
    try {
      const client = await createTestClient("default-value-client");

      // テーブル作成
      await client.executeOperation({
        id: "create-table",
        type: "DDL",
        dependsOn: [],
        payload: {
          ddlType: "CREATE_TABLE",
          query: "CREATE NODE TABLE Account (id STRING, name STRING, PRIMARY KEY(id))"
        },
        clientId: "default-value-client",
        timestamp: Date.now()
      });

      // DEFAULT値付きのカラム追加
      await client.executeOperation({
        id: "add-balance",
        type: "DDL",
        dependsOn: ["create-table"],
        payload: {
          ddlType: "ADD_COLUMN",
          query: "ALTER TABLE Account ADD balance DOUBLE DEFAULT 0.0"
        },
        clientId: "default-value-client",
        timestamp: Date.now()
      });

      await delay(100);

      // スキーマを確認
      const schema = await client.getSchemaVersion();
      assertEquals(schema.tables.Account.columns.balance.type, "DOUBLE");
      assertEquals(schema.tables.Account.columns.balance.default, "0.0");
    } finally {
      await cleanupAll();
    }
  });

  await t.step("should handle DROP COLUMN IF EXISTS", async () => {
    try {
      const client = await createTestClient("if-exists-client");

      // テーブル作成
      await client.executeOperation({
        id: "create-table",
        type: "DDL",
        dependsOn: [],
        payload: {
          ddlType: "CREATE_TABLE",
          query: "CREATE NODE TABLE Product (id STRING, name STRING, price DOUBLE, PRIMARY KEY(id))"
        },
        clientId: "if-exists-client",
        timestamp: Date.now()
      });

      // 存在しないカラムをIF EXISTSで削除（エラーにならない）
      await client.executeOperation({
        id: "drop-nonexistent",
        type: "DDL",
        dependsOn: ["create-table"],
        payload: {
          ddlType: "DROP_COLUMN",
          query: "ALTER TABLE Product DROP IF EXISTS discount"
        },
        clientId: "if-exists-client",
        timestamp: Date.now()
      });

      // 既存のカラムを削除
      await client.executeOperation({
        id: "drop-price",
        type: "DDL",
        dependsOn: ["drop-nonexistent"],
        payload: {
          ddlType: "DROP_COLUMN",
          query: "ALTER TABLE Product DROP IF EXISTS price"
        },
        clientId: "if-exists-client",
        timestamp: Date.now()
      });

      await delay(100);

      // スキーマを確認
      const schema = await client.getSchemaVersion();
      assertEquals(Object.keys(schema.tables.Product.columns), ["id", "name"]);
    } finally {
      await cleanupAll();
    }
  });

  await t.step("should handle RENAME TABLE", async () => {
    try {
      const client = await createTestClient("rename-table-client");

      // テーブル作成
      await client.executeOperation({
        id: "create-table",
        type: "DDL",
        dependsOn: [],
        payload: {
          ddlType: "CREATE_TABLE",
          query: "CREATE NODE TABLE OldName (id STRING, value STRING, PRIMARY KEY(id))"
        },
        clientId: "rename-table-client",
        timestamp: Date.now()
      });

      // テーブル名を変更
      await client.executeOperation({
        id: "rename-table",
        type: "DDL",
        dependsOn: ["create-table"],
        payload: {
          ddlType: "RENAME_TABLE",
          query: "ALTER TABLE OldName RENAME TO NewName"
        },
        clientId: "rename-table-client",
        timestamp: Date.now()
      });

      await delay(100);

      // スキーマを確認
      const schema = await client.getSchemaVersion();
      assert(!schema.tables.OldName); // 古い名前は存在しない
      assert(schema.tables.NewName); // 新しい名前が存在
      assertEquals(Object.keys(schema.tables.NewName.columns), ["id", "value"]);
    } finally {
      await cleanupAll();
    }
  });

  await t.step("should handle RENAME COLUMN", async () => {
    try {
      const client = await createTestClient("rename-column-client");

      // テーブル作成
      await client.executeOperation({
        id: "create-table",
        type: "DDL",
        dependsOn: [],
        payload: {
          ddlType: "CREATE_TABLE",
          query: "CREATE NODE TABLE Person (id STRING, old_name STRING, PRIMARY KEY(id))"
        },
        clientId: "rename-column-client",
        timestamp: Date.now()
      });

      // カラム名を変更
      await client.executeOperation({
        id: "rename-column",
        type: "DDL",
        dependsOn: ["create-table"],
        payload: {
          ddlType: "RENAME_COLUMN",
          query: "ALTER TABLE Person RENAME old_name TO full_name"
        },
        clientId: "rename-column-client",
        timestamp: Date.now()
      });

      await delay(100);

      // スキーマを確認
      const schema = await client.getSchemaVersion();
      assert(!schema.tables.Person.columns.old_name); // 古い名前は存在しない
      assert(schema.tables.Person.columns.full_name); // 新しい名前が存在
      assertEquals(schema.tables.Person.columns.full_name.type, "STRING");
    } finally {
      await cleanupAll();
    }
  });

  await t.step("should handle COMMENT ON TABLE", async () => {
    try {
      const client = await createTestClient("comment-client");

      // テーブル作成
      await client.executeOperation({
        id: "create-table",
        type: "DDL",
        dependsOn: [],
        payload: {
          ddlType: "CREATE_TABLE",
          query: "CREATE NODE TABLE Employee (id STRING, name STRING, PRIMARY KEY(id))"
        },
        clientId: "comment-client",
        timestamp: Date.now()
      });

      // テーブルにコメントを追加
      await client.executeOperation({
        id: "add-comment",
        type: "DDL",
        dependsOn: ["create-table"],
        payload: {
          ddlType: "COMMENT_ON_TABLE",
          query: "COMMENT ON TABLE Employee IS 'Employee information table'"
        },
        clientId: "comment-client",
        timestamp: Date.now()
      });

      await delay(100);

      // スキーマを確認
      const schema = await client.getSchemaVersion();
      assertEquals(schema.tables.Employee.comment, "Employee information table");
    } finally {
      await cleanupAll();
    }
  });

  await t.step("should handle complex DDL sequence with all features", async () => {
    try {
      const client = await createTestClient("complex-ddl-client");

      // 1. テーブル作成
      await client.executeOperation({
        id: "create-table",
        type: "DDL",
        dependsOn: [],
        payload: {
          ddlType: "CREATE_TABLE",
          query: "CREATE NODE TABLE Student (id STRING, name STRING, PRIMARY KEY(id))"
        },
        clientId: "complex-ddl-client",
        timestamp: Date.now()
      });

      // 2. コメント追加
      await client.executeOperation({
        id: "add-comment",
        type: "DDL",
        dependsOn: ["create-table"],
        payload: {
          ddlType: "COMMENT_ON_TABLE",
          query: "COMMENT ON TABLE Student IS 'Student records'"
        },
        clientId: "complex-ddl-client",
        timestamp: Date.now()
      });

      // 3. DEFAULT値付きカラム追加
      await client.executeOperation({
        id: "add-grade",
        type: "DDL",
        dependsOn: ["add-comment"],
        payload: {
          ddlType: "ADD_COLUMN",
          query: "ALTER TABLE Student ADD grade INT64 DEFAULT 0"
        },
        clientId: "complex-ddl-client",
        timestamp: Date.now()
      });

      // 4. カラム名変更
      await client.executeOperation({
        id: "rename-name",
        type: "DDL",
        dependsOn: ["add-grade"],
        payload: {
          ddlType: "RENAME_COLUMN",
          query: "ALTER TABLE Student RENAME name TO full_name"
        },
        clientId: "complex-ddl-client",
        timestamp: Date.now()
      });

      // 5. テーブル名変更
      await client.executeOperation({
        id: "rename-table",
        type: "DDL",
        dependsOn: ["rename-name"],
        payload: {
          ddlType: "RENAME_TABLE",
          query: "ALTER TABLE Student RENAME TO Learner"
        },
        clientId: "complex-ddl-client",
        timestamp: Date.now()
      });

      await delay(200);

      // 最終スキーマを確認
      const schema = await client.getSchemaVersion();
      assert(!schema.tables.Student); // 古いテーブル名は存在しない
      assert(schema.tables.Learner); // 新しいテーブル名が存在
      assertEquals(schema.tables.Learner.comment, "Student records");
      assertEquals(Object.keys(schema.tables.Learner.columns).sort(), ["full_name", "grade", "id"]);
      assertEquals(schema.tables.Learner.columns.grade.default, "0");
      assertEquals(schema.tables.Learner.columns.full_name.type, "STRING");
    } finally {
      await cleanupAll();
    }
  });

  // Final cleanup after all tests
  await cleanupAll();
});