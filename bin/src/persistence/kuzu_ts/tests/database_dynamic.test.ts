import { assertEquals } from "jsr:@std/assert@^1.0.0";
import {
  createDatabaseDynamic,
  createConnectionDynamic,
  closeDatabaseSafe,
  closeConnectionSafe
} from "../core/database_dynamic.ts";
import { isDatabase, isConnection, isValidationError } from "../core/result_types.ts";

Deno.test("createDatabaseDynamic - in-memory database creation", async () => {
  const result = await createDatabaseDynamic(":memory:");
  
  assertEquals(isDatabase(result), true);
  
  // クリーンアップ
  await closeDatabaseSafe(result);
});

Deno.test("createConnectionDynamic - connection creation", async () => {
  const dbResult = await createDatabaseDynamic(":memory:");
  
  if (isDatabase(dbResult)) {
    const connResult = await createConnectionDynamic(dbResult);
    
    assertEquals(isConnection(connResult), true);
    
    // クリーンアップ
    await closeConnectionSafe(connResult);
    await closeDatabaseSafe(dbResult);
  }
});

Deno.test("dynamic import - basic CRUD operations", async () => {
  const dbResult = await createDatabaseDynamic(":memory:");
  
  if (isDatabase(dbResult)) {
    const connResult = await createConnectionDynamic(dbResult);
    
    if (isConnection(connResult)) {
      // テーブル作成
      await connResult.query("CREATE NODE TABLE TestNode(id INT64, name STRING, PRIMARY KEY(id))");
      
      // データ挿入
      await connResult.query("CREATE (n:TestNode {id: 1, name: 'Test'})");
      
      // データ取得
      const result = await connResult.query("MATCH (n:TestNode) RETURN n.id, n.name");
      const rows = await result.getAll();
      
      assertEquals(rows.length, 1);
      assertEquals(rows[0]["n.id"], 1);
      assertEquals(rows[0]["n.name"], "Test");
      
      // クリーンアップ
      await closeConnectionSafe(connResult);
    }
    
    await closeDatabaseSafe(dbResult);
  }
});

Deno.test("createDatabaseDynamic - validation errors", async () => {
  // 空のパス
  const emptyResult = await createDatabaseDynamic("");
  assertEquals(isValidationError(emptyResult), true);
  
  // nullパス
  const nullResult = await createDatabaseDynamic(null as any);
  assertEquals(isValidationError(nullResult), true);
});

Deno.test("createConnectionDynamic - validation errors", async () => {
  // 無効なデータベース
  const invalidResult = await createConnectionDynamic(null);
  assertEquals(isValidationError(invalidResult), true);
  
  // 文字列を渡す
  const stringResult = await createConnectionDynamic("not a database" as any);
  assertEquals(isValidationError(stringResult), true);
});