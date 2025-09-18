import { assertEquals, assert } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { 
  withTestContext, 
  createManagedTestClient,
  waitForPendingOperations,
  gracefulShutdown 
} from "./test-helpers.ts";

Deno.test("DDL Integration Tests - Clean Version", async (t) => {
  
  await t.step("should handle DDL operations with causal ordering", async () => {
    await withTestContext(async (ctx) => {
      const client = await createManagedTestClient(ctx, "ddl-client");

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

      // Wait for operations to complete
      await waitForPendingOperations(client);

      // 期待: DDL操作が正しい順序で適用される
      const schema = await client.getSchemaVersion();
      assertEquals(Object.keys(schema.tables.User.columns), ["id", "name", "email"]);
    });
  });

  await t.step("should wait for schema before applying DML operations", async () => {
    await withTestContext(async (ctx) => {
      const ddlClient = await createManagedTestClient(ctx, "ddl-client");
      const dmlClient = await createManagedTestClient(ctx, "dml-client");

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
      await new Promise(resolve => setTimeout(resolve, 500));
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
      await waitForPendingOperations(dmlClient);
      
      const usersAfterDDL = await dmlClient.query("MATCH (u:User) RETURN u");
      assertEquals(usersAfterDDL.length, 1);
      assertEquals(usersAfterDDL[0].age, 30);
    });
  });

  await t.step("should handle ADD COLUMN IF NOT EXISTS", async () => {
    await withTestContext(async (ctx) => {
      const client = await createManagedTestClient(ctx, "if-not-exists-client");

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

      await waitForPendingOperations(client);

      // スキーマに変更がないことを確認
      const schema = await client.getSchemaVersion();
      assertEquals(Object.keys(schema.tables.Customer.columns), ["id", "name", "email"]);
    });
  });

  await t.step("should handle complex DDL sequence with all features", async () => {
    await withTestContext(async (ctx) => {
      const client = await createManagedTestClient(ctx, "complex-ddl-client");

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

      await waitForPendingOperations(client);

      // 最終スキーマを確認
      const schema = await client.getSchemaVersion();
      assert(!schema.tables.Student); // 古いテーブル名は存在しない
      assert(schema.tables.Learner); // 新しいテーブル名が存在
      assertEquals(schema.tables.Learner.comment, "Student records");
      assertEquals(Object.keys(schema.tables.Learner.columns).sort(), ["full_name", "grade", "id"]);
      assertEquals(schema.tables.Learner.columns.grade.default, "0");
      assertEquals(schema.tables.Learner.columns.full_name.type, "STRING");
    });
  });

  await t.step("should properly isolate concurrent tests", async () => {
    // Run two isolated test contexts in parallel
    const results = await Promise.all([
      withTestContext(async (ctx) => {
        const client = await createManagedTestClient(ctx, "test1-client");
        await client.executeOperation({
          id: "create-table-1",
          type: "DDL",
          dependsOn: [],
          payload: {
            ddlType: "CREATE_TABLE",
            query: "CREATE NODE TABLE Test1 (id STRING, PRIMARY KEY(id))"
          },
          clientId: "test1-client",
          timestamp: Date.now()
        });
        await waitForPendingOperations(client);
        const schema = await client.getSchemaVersion();
        return { hasTest1: !!schema.tables.Test1, hasTest2: !!schema.tables.Test2 };
      }),
      
      withTestContext(async (ctx) => {
        const client = await createManagedTestClient(ctx, "test2-client");
        await client.executeOperation({
          id: "create-table-2",
          type: "DDL",
          dependsOn: [],
          payload: {
            ddlType: "CREATE_TABLE",
            query: "CREATE NODE TABLE Test2 (id STRING, PRIMARY KEY(id))"
          },
          clientId: "test2-client",
          timestamp: Date.now()
        });
        await waitForPendingOperations(client);
        const schema = await client.getSchemaVersion();
        return { hasTest1: !!schema.tables.Test1, hasTest2: !!schema.tables.Test2 };
      })
    ]);

    // Each context should only see its own table
    assertEquals(results[0], { hasTest1: true, hasTest2: false });
    assertEquals(results[1], { hasTest1: false, hasTest2: true });
  });
});