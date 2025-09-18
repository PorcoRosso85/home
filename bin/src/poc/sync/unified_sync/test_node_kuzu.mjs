/**
 * Node.js Direct Test for KuzuDB CTS
 * Node.js環境で直接実行するテスト
 */

import { createRequire } from 'module';

async function testKuzuCTS() {
  try {
    console.log("=== Testing KuzuDB CTS Bridge ===");
    
    // CTSファイルを動的インポート
    const { KuzuNodeStorage } = await import('./kuzu_storage.cjs');
    
    console.log("✅ CTS import successful");
    
    // ストレージ作成
    const storage = new KuzuNodeStorage();
    await storage.initialize();
    
    console.log("✅ KuzuDB initialized");
    
    // テスト実行
    await storage.executeTemplate("CREATE_USER", {
      id: "u1",
      name: "Alice",
      email: "alice@example.com"
    });
    
    console.log("✅ User created");
    
    const state = await storage.getLocalState();
    console.log("State:", state);
    
    if (state.users.length === 1 && state.users[0].name === "Alice") {
      console.log("✅ All tests passed!");
    } else {
      console.error("❌ Test failed: unexpected state");
    }
    
  } catch (error) {
    console.error("❌ Error:", error);
  }
}

testKuzuCTS();