/**
 * Real KuzuDB Test with CTS
 * 実際のKuzuDB Node.js版を使用したテスト
 */

import { assertEquals, assert } from "jsr:@std/assert@^1.0.0";
import { testStorageImplementation } from "./test_storage_interface.ts";
import { KuzuNodeStorageFactory } from "./kuzu_storage_factory.ts";
import { BrowserClientRefactored } from "./browser_client_refactored.ts";

// Node.js環境でのみ実行（Denoテスト環境では実行しない）
const isNode = false; // Deno環境では常にfalse

Deno.test({
  name: "test_real_kuzu_nodejs_with_cts",
  ignore: !isNode, // Node.js環境でのみ実行
  fn: async () => {
    console.log("=== Testing Real KuzuDB Node.js (CTS) ===");
    
    // WARNING: KuzuDB Node.js版はCommonJSのみサポート
    // CTSファイルを介して使用
    const factory = new KuzuNodeStorageFactory();
    const storage = await factory.createStorage();
    
    // 標準テストスイートを実行
    await testStorageImplementation(storage);
    
    console.log("✅ Real KuzuDB Node.js test passed!");
  }
});

Deno.test({
  name: "test_browser_client_with_real_kuzu",
  ignore: !isNode, // Node.js環境でのみ実行
  fn: async () => {
    console.log("=== Testing Browser Client with Real KuzuDB ===");
    
    const client = new BrowserClientRefactored(new KuzuNodeStorageFactory());
    await client.initialize();
    
    // CREATE_USER
    const event1 = await client.executeTemplate("CREATE_USER", {
      id: "u1",
      name: "Alice",
      email: "alice@example.com"
    });
    
    assertEquals(event1.template, "CREATE_USER");
    assert(event1.id.startsWith("evt_"));
    
    // UPDATE_USER
    const event2 = await client.executeTemplate("UPDATE_USER", {
      id: "u1",
      name: "Alice Updated"
    });
    
    // CREATE_POST
    const event3 = await client.executeTemplate("CREATE_POST", {
      id: "p1",
      content: "Hello from KuzuDB",
      authorId: "u1"
    });
    
    // FOLLOW_USER
    await client.executeTemplate("CREATE_USER", {
      id: "u2",
      name: "Bob",
      email: "bob@example.com"
    });
    
    const event4 = await client.executeTemplate("FOLLOW_USER", {
      followerId: "u1",
      targetId: "u2"
    });
    
    // 最終状態確認
    const state = await client.getLocalState();
    
    assertEquals(state.users.length, 2);
    assertEquals(state.users.find(u => u.id === "u1")?.name, "Alice Updated");
    assertEquals(state.posts.length, 1);
    assertEquals(state.posts[0].content, "Hello from KuzuDB");
    assertEquals(state.follows.length, 1);
    assertEquals(state.follows[0].followerId, "u1");
    assertEquals(state.follows[0].targetId, "u2");
    
    console.log("✅ Browser client with real KuzuDB test passed!");
  }
});

// 環境情報表示
if (import.meta.main) {
  console.log("\n=== KuzuDB ESM/CTS Status ===");
  console.log("KuzuDB Node.js版: CommonJSのみ（ESM非対応）");
  console.log("KuzuDB Browser版: ESMサポートあり");
  console.log("解決策: CTSファイルでCommonJSをラップ");
  console.log("\nWARNING: KuzuDB公式ドキュメントより:");
  console.log("\"It is distributed as a CommonJS module rather than an ES module to maximize compatibility\"");
}