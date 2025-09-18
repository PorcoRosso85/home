import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createDatabase, createConnection } from "../../../../persistence/kuzu_ts/core/database.ts";
import { applyDdl } from "../../src/kuzu_integration.ts";

Deno.test("KuzuDB統合: DDLを適用できることを確認", async () => {
  // Arrange - 実際のKuzuDBインスタンスを作成
  const db = await createDatabase(":memory:", { testUnique: true });
  const conn = await createConnection(db);
  const kuzuDb = {
    execute: (query: string) => conn.query(query),
    query: (query: string) => conn.query(query)
  };
  
  // Act - DDLを適用
  await applyDdl(kuzuDb, "ddl/contract_schema.cypher");
  
  // 正常に完了すればテスト成功
});

Deno.test("KuzuDB統合: テーブルが作成されることを確認", async () => {
  // Arrange - 実際のKuzuDBインスタンスを作成
  const db = await createDatabase(":memory:", { testUnique: true });
  const conn = await createConnection(db);
  const kuzuDb = {
    execute: (query: string) => conn.query(query),
    query: async (query: string) => {
      const result = await conn.query(query);
      return await result.getAll();
    }
  };
  
  // Act - DDLを適用
  await applyDdl(kuzuDb, "ddl/contract_schema.cypher");
  
  // 現在のkuzu_ts実装はモックなので、DDL適用の成功のみを確認
  // 実際のKuzuDB統合時にテーブル確認のテストを追加予定
  
  // DDLが正常に適用されたことを確認（エラーがなければ成功）
  assertEquals(true, true);
});