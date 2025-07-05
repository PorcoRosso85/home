/**
 * Node.js Integration Test - モックフリー
 * 実際のKuzuDB Node.js版を使用した統合テスト
 */

const assert = require('assert');

// CommonJSで各モジュールを読み込む
async function runTests() {
  console.log("=== Node.js Integration Test (No Mocks) ===\n");

  try {
    // 1. KuzuDB Node.js版テスト
    console.log("1. Testing KuzuDB Node.js...");
    const { KuzuNodeStorage } = require('./kuzu_storage.cts');
    const storage = new KuzuNodeStorage();
    await storage.initialize();
    
    // CREATE_USER
    await storage.executeTemplate("CREATE_USER", {
      id: "u1",
      name: "Alice",
      email: "alice@example.com"
    });
    
    // UPDATE_USER  
    await storage.executeTemplate("UPDATE_USER", {
      id: "u1",
      name: "Alice Updated"
    });
    
    // CREATE_POST
    await storage.executeTemplate("CREATE_POST", {
      id: "p1",
      content: "Hello KuzuDB",
      authorId: "u1"
    });
    
    // Verify
    const state = await storage.getLocalState();
    assert.strictEqual(state.users.length, 1);
    assert.strictEqual(state.users[0].name, "Alice Updated");
    assert.strictEqual(state.posts.length, 1);
    console.log("✅ KuzuDB tests passed\n");
    
    // 2. Event Store テスト
    console.log("2. Testing Event Store...");
    const { ServerEventStoreImpl } = await import('./server_event_store.ts');
    const store = new ServerEventStoreImpl();
    
    const event = {
      id: "evt_1",
      template: "CREATE_USER",
      params: { id: "u2", name: "Bob" },
      timestamp: Date.now(),
      clientId: "test",
      checksum: "abc123" // 実際は計算が必要
    };
    
    // チェックサム計算
    const content = JSON.stringify({ template: event.template, params: event.params });
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    event.checksum = Math.abs(hash).toString(16);
    
    await store.appendEvent(event);
    const events = await store.getEventsSince(0);
    assert.strictEqual(events.length, 1);
    console.log("✅ Event Store tests passed\n");
    
    // 3. WebSocket Sync テスト（サーバーなし）
    console.log("3. Testing WebSocket Sync (offline mode)...");
    const { WebSocketSyncImpl } = await import('./websocket_sync.ts');
    const wsSync = new WebSocketSyncImpl();
    
    // オフラインでのイベントキューイング
    await wsSync.sendEvent(event);
    const pending = await wsSync.getPendingEvents();
    assert.strictEqual(pending.length, 1);
    console.log("✅ WebSocket Sync tests passed\n");
    
    console.log("🎉 All tests passed without mocks!");
    
  } catch (error) {
    console.error("❌ Test failed:", error);
    process.exit(1);
  }
}

runTests();