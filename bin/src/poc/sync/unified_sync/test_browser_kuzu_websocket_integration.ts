/**
 * Browser KuzuDB WebSocket Integration - TDD Red Phase
 * ブラウザKuzuDB WebSocket統合のTDDレッドフェーズテスト
 * 
 * 規約準拠:
 * - test_{機能}_{条件}_{結果} 命名規則
 * - ESモジュールのみ使用
 * - 型定義を明確化
 */

import { assertEquals, assert, assertExists } from "jsr:@std/assert@^1.0.0";
import type { TemplateEvent } from "../event_sourcing/types.ts";

// ========== 型定義 ==========

type BrowserKuzuClient = {
  initialize(): Promise<void>;
  executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent>;
  getLocalState(): Promise<any>;
  onRemoteEvent(handler: (event: TemplateEvent) => void): void;
};

type WebSocketSync = {
  connect(url: string): Promise<void>;
  sendEvent(event: TemplateEvent): Promise<void>;
  onEvent(handler: (event: TemplateEvent) => void): void;
  disconnect(): void;
  isConnected(): boolean;
};

type ServerEventStore = {
  appendEvent(event: TemplateEvent): Promise<void>;
  getEventsSince(position: number): Promise<TemplateEvent[]>;
  onNewEvent(handler: (event: TemplateEvent) => void): void;
};

// ========== 1. ブラウザでのKuzuDB WASM実行とイベント生成 ==========

Deno.test("test_browser_kuzu_client_with_template_execution_generates_event", async () => {
  const client = new BrowserKuzuClient();
  await client.initialize();
  
  const event = await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice",
    email: "alice@example.com"
  });
  
  assertEquals(event.template, "CREATE_USER");
  assertEquals(event.params.name, "Alice");
  assert(event.id.startsWith("evt_"));
  assert(event.checksum);
  
  // ローカルKuzuDBに反映されている
  const state = await client.getLocalState();
  assertEquals(state.users.length, 1);
  assertEquals(state.users[0].name, "Alice");
});

// ========== 2. WebSocket経由でのイベント送信 ==========

Deno.test("test_websocket_sync_with_event_send_transmits_to_server", async () => {
  const client = new BrowserKuzuClient();
  const wsSync = new WebSocketSync();
  
  await client.initialize();
  await wsSync.connect("ws://localhost:8080");
  
  // イベント生成と送信
  const event = await client.executeTemplate("CREATE_POST", {
    id: "p1",
    content: "Hello from browser",
    authorId: "u1"
  });
  
  await wsSync.sendEvent(event);
  
  // サーバー側で受信確認（モックまたは実サーバー）
  assert(wsSync.isConnected());
});

// ========== 3. サーバーEvent Storeでの記録 ==========

Deno.test("test_server_event_store_with_append_persists_template_event", async () => {
  const store = new ServerEventStore();
  
  const event: TemplateEvent = {
    id: "evt_123",
    template: "CREATE_USER",
    params: { id: "u1", name: "Alice" },
    timestamp: Date.now(),
    clientId: "browser_1",
    checksum: "abc123"
  };
  
  await store.appendEvent(event);
  
  const events = await store.getEventsSince(0);
  assertEquals(events.length, 1);
  assertEquals(events[0].template, "CREATE_USER");
});

// ========== 4. 他のブラウザへのイベント配信 ==========

Deno.test("test_multi_browser_sync_with_event_broadcast_updates_all_clients", async () => {
  const client1 = new BrowserKuzuClient();
  const client2 = new BrowserKuzuClient();
  const wsSync1 = new WebSocketSync();
  const wsSync2 = new WebSocketSync();
  
  await client1.initialize();
  await client2.initialize();
  await wsSync1.connect("ws://localhost:8080");
  await wsSync2.connect("ws://localhost:8080");
  
  let receivedEvent: TemplateEvent | null = null;
  
  // Client2がイベントを受信する準備
  client2.onRemoteEvent((event) => {
    receivedEvent = event;
  });
  
  wsSync2.onEvent(async (event) => {
    // 受信したイベントをローカルKuzuDBに適用
    await client2.executeTemplate(event.template, event.params);
  });
  
  // Client1がイベントを送信
  const event = await client1.executeTemplate("CREATE_USER", {
    id: "u2",
    name: "Bob",
    email: "bob@example.com"
  });
  
  await wsSync1.sendEvent(event);
  
  // 非同期で配信を待つ
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // Client2に反映されている
  assertExists(receivedEvent);
  assertEquals(receivedEvent.template, "CREATE_USER");
  
  const state2 = await client2.getLocalState();
  assert(state2.users.some(u => u.name === "Bob"));
});

// ========== 5. ネットワーク障害時の耐性 ==========

Deno.test("test_network_failure_with_disconnection_queues_events", async () => {
  const client = new BrowserKuzuClient();
  const wsSync = new WebSocketSync();
  
  await client.initialize();
  await wsSync.connect("ws://localhost:8080");
  
  // 接続を切断
  wsSync.disconnect();
  assert(!wsSync.isConnected());
  
  // オフライン中にイベント生成
  const event1 = await client.executeTemplate("CREATE_USER", {
    id: "u3",
    name: "Charlie"
  });
  
  const event2 = await client.executeTemplate("CREATE_POST", {
    id: "p2",
    content: "Offline post"
  });
  
  // 再接続
  await wsSync.connect("ws://localhost:8080");
  
  // キューされたイベントが送信される
  const pendingEvents = await wsSync.getPendingEvents();
  assertEquals(pendingEvents.length, 2);
});

// ========== 6. Cypherインジェクション対策 ==========

Deno.test("test_template_validation_with_injection_attempt_rejects_dangerous_params", async () => {
  const client = new BrowserKuzuClient();
  await client.initialize();
  
  try {
    await client.executeTemplate("CREATE_USER", {
      id: "u1",
      name: "Alice'; DROP TABLE users; --",
      email: "alice@example.com"
    });
    assert(false, "Should have thrown error");
  } catch (error) {
    assert(error.message.includes("Invalid parameter"));
  }
});

// ========== 7. チェックサムによる整合性検証 ==========

Deno.test("test_event_integrity_with_checksum_validates_unchanged_content", async () => {
  const client = new BrowserKuzuClient();
  const wsSync = new WebSocketSync();
  const store = new ServerEventStore();
  
  await client.initialize();
  await wsSync.connect("ws://localhost:8080");
  
  const event = await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice"
  });
  
  // イベントを改ざん
  const tamperedEvent = { ...event, params: { ...event.params, name: "Bob" } };
  
  try {
    await store.appendEvent(tamperedEvent);
    assert(false, "Should have rejected tampered event");
  } catch (error) {
    assert(error.message.includes("checksum"));
  }
});

// ========== 8. 競合解決 ==========

Deno.test("test_concurrent_updates_with_same_entity_resolves_conflict", async () => {
  const client1 = new BrowserKuzuClient();
  const client2 = new BrowserKuzuClient();
  const resolver = new ConflictResolver();
  
  await client1.initialize();
  await client2.initialize();
  
  // 同じユーザーを同時に更新
  const event1 = await client1.executeTemplate("UPDATE_USER", {
    id: "u1",
    name: "Alice Updated by Client1"
  });
  
  const event2 = await client2.executeTemplate("UPDATE_USER", {
    id: "u1",
    name: "Alice Updated by Client2"
  });
  
  // 競合解決
  const resolution = resolver.resolve([event1, event2]);
  assertEquals(resolution.strategy, "LAST_WRITE_WINS");
  assertEquals(resolution.winner.params.name, "Alice Updated by Client2");
});

// ========== 9. スナップショットからの高速初期化 ==========

Deno.test("test_snapshot_initialization_with_large_dataset_loads_quickly", async () => {
  const client = new BrowserKuzuClient();
  const store = new ServerEventStore();
  
  // 1000イベントを生成
  for (let i = 0; i < 1000; i++) {
    await store.appendEvent({
      id: `evt_${i}`,
      template: "CREATE_USER",
      params: { id: `u${i}`, name: `User ${i}` },
      timestamp: Date.now(),
      clientId: "seed"
    });
  }
  
  // スナップショットから初期化
  const startTime = Date.now();
  await client.initializeFromSnapshot(store.getSnapshot());
  const loadTime = Date.now() - startTime;
  
  // 100ms以内に初期化完了
  assert(loadTime < 100);
  
  const state = await client.getLocalState();
  assertEquals(state.users.length, 1000);
});

// ========== 10. メトリクス収集 ==========

Deno.test("test_metrics_collection_with_event_tracking_provides_insights", async () => {
  const metrics = new MetricsCollector();
  const client = new BrowserKuzuClient();
  
  await client.initialize();
  metrics.startTracking(client);
  
  // 複数のイベントを実行
  await client.executeTemplate("CREATE_USER", { id: "u1", name: "Alice" });
  await client.executeTemplate("CREATE_POST", { id: "p1", content: "Test" });
  await client.executeTemplate("FOLLOW_USER", { followerId: "u1", targetId: "u2" });
  
  const stats = metrics.getStats();
  assertEquals(stats.totalEvents, 3);
  assertEquals(stats.eventTypes.CREATE_USER, 1);
  assertEquals(stats.eventTypes.CREATE_POST, 1);
  assertEquals(stats.eventTypes.FOLLOW_USER, 1);
  assert(stats.averageLatency > 0);
});

// ========== ヘルパー型定義（実装時に移動） ==========

type ConflictResolver = {
  resolve(events: TemplateEvent[]): {
    strategy: string;
    winner: TemplateEvent;
  };
};

type MetricsCollector = {
  startTracking(client: BrowserKuzuClient): void;
  getStats(): {
    totalEvents: number;
    eventTypes: Record<string, number>;
    averageLatency: number;
  };
};

// ========== 実行 ==========

if (import.meta.main) {
  console.log("=== Browser KuzuDB WebSocket Integration - TDD Red Phase ===");
  console.log("全てのテストが失敗することを確認してください");
}