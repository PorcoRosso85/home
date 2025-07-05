/**
 * Refactored Tests - モック最小化
 * インターフェースベースのテスト
 */

import { assertEquals, assert, assertExists } from "jsr:@std/assert@^1.0.0";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import { 
  BrowserClientRefactored, 
  StorageFactory, 
  KuzuStorageFactory 
} from "./browser_client_refactored.ts";
import { 
  InMemoryGraphStorage, 
  testStorageImplementation,
  type GraphStorage 
} from "./test_storage_interface.ts";
import {
  ServerEventStoreImpl,
  ConflictResolverImpl,
  MetricsCollectorImpl
} from "./mod.ts";

// テスト用ストレージファクトリー
class TestStorageFactory implements StorageFactory {
  async createStorage(): Promise<GraphStorage> {
    return new InMemoryGraphStorage();
  }
}

// ========== 1. ストレージ実装のテスト ==========

Deno.test("test_storage_implementation_inmemory", async () => {
  const storage = new InMemoryGraphStorage();
  await testStorageImplementation(storage);
});

// ========== 2. ブラウザクライアントのテスト（ストレージ非依存） ==========

Deno.test("test_browser_client_with_template_execution", async () => {
  const client = new BrowserClientRefactored(new TestStorageFactory());
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
  
  const state = await client.getLocalState();
  assertEquals(state.users.length, 1);
  assertEquals(state.users[0].name, "Alice");
});

// ========== 3. イベントストアのテスト（純粋なロジック） ==========

Deno.test("test_event_store_with_checksum_validation", async () => {
  const store = new ServerEventStoreImpl();
  const client = new BrowserClientRefactored(new TestStorageFactory());
  await client.initialize();
  
  const event = await client.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice"
  });
  
  // 正常なイベントは受け入れられる
  await store.appendEvent(event);
  const events = await store.getEventsSince(0);
  assertEquals(events.length, 1);
  
  // 改ざんされたイベントは拒否される
  const tamperedEvent = { ...event, params: { ...event.params, name: "Bob" } };
  try {
    await store.appendEvent(tamperedEvent);
    assert(false, "Should reject tampered event");
  } catch (error) {
    assert(error instanceof Error && error.message.includes("checksum"));
  }
});

// ========== 4. 同期ロジックのテスト（WebSocket非依存） ==========

interface SyncChannel {
  send(event: TemplateEvent): void;
  onReceive(handler: (event: TemplateEvent) => void): void;
}

class LocalSyncChannel implements SyncChannel {
  private handlers: Array<(event: TemplateEvent) => void> = [];
  
  send(event: TemplateEvent): void {
    // 他のハンドラーに配信
    this.handlers.forEach(handler => handler(event));
  }
  
  onReceive(handler: (event: TemplateEvent) => void): void {
    this.handlers.push(handler);
  }
}

Deno.test("test_multi_client_sync_with_local_channel", async () => {
  const channel = new LocalSyncChannel();
  
  const client1 = new BrowserClientRefactored(new TestStorageFactory());
  const client2 = new BrowserClientRefactored(new TestStorageFactory());
  
  await client1.initialize();
  await client2.initialize();
  
  // Client2がイベントを受信する設定
  channel.onReceive(async (event) => {
    await client2.executeTemplate(event.template, event.params);
  });
  
  let receivedEvent: TemplateEvent | null = null;
  client2.onRemoteEvent((event) => {
    receivedEvent = event;
  });
  
  // Client1でイベント作成
  const event = await client1.executeTemplate("CREATE_USER", {
    id: "u1",
    name: "Alice"
  });
  
  // チャンネル経由で送信
  channel.send(event);
  
  // Client2に反映確認
  await new Promise(resolve => setTimeout(resolve, 10));
  assertExists(receivedEvent);
  assert(receivedEvent !== null);
  assertEquals(receivedEvent.template, "CREATE_USER");
  
  const state2 = await client2.getLocalState();
  assertEquals(state2.users.length, 1);
  assertEquals(state2.users[0].name, "Alice");
});

// ========== 5. メトリクス収集のテスト ==========

// シンプルなメトリクス実装
class SimpleMetrics {
  private totalEvents = 0;
  private eventTypes: Record<string, number> = {};
  
  trackEvent(event: TemplateEvent): void {
    this.totalEvents++;
    this.eventTypes[event.template] = (this.eventTypes[event.template] || 0) + 1;
  }
  
  getStats() {
    return {
      totalEvents: this.totalEvents,
      eventTypes: { ...this.eventTypes }
    };
  }
}

Deno.test("test_metrics_collection_with_interface", async () => {
  const metrics = new SimpleMetrics();
  const client = new BrowserClientRefactored(new TestStorageFactory());
  
  await client.initialize();
  
  // イベントハンドラーでメトリクスを収集
  client.onRemoteEvent((event) => {
    metrics.trackEvent(event);
  });
  
  await client.executeTemplate("CREATE_USER", { id: "u1", name: "Alice" });
  await client.executeTemplate("CREATE_POST", { id: "p1", content: "Test" });
  await client.executeTemplate("FOLLOW_USER", { followerId: "u1", targetId: "u2" });
  
  const stats = metrics.getStats();
  assertEquals(stats.totalEvents, 3);
  assertEquals(stats.eventTypes.CREATE_USER, 1);
  assertEquals(stats.eventTypes.CREATE_POST, 1);
  assertEquals(stats.eventTypes.FOLLOW_USER, 1);
});

// ========== 実行 ==========

if (import.meta.main) {
  console.log("=== Refactored Tests - モック最小化 ===");
}