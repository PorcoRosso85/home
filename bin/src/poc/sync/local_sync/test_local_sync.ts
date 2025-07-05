/**
 * Local Sync Engine - TDD Red Phase Tests
 * 単一サーバーでの複数クライアント同期の基礎実装
 */

// テストで使用するアサーション関数をインポート
import { assertEquals, assertExists, assert, assertThrows, assertRejects } from "jsr:@std/assert@^1.0.0";

// 実装をインポート
import { LocalSyncServer, SyncClient, SyncEvent } from "./local_sync_server.ts";

// Utility function
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// ========== 型定義はlocal_sync_server.tsから取得 ==========

// ========== 基本的な同期機能 ==========

Deno.test("単一クライアントのイベント送信", () => {
  const server = new LocalSyncServer();
  const client = server.connect("client1");
  
  const event = client.send({
    operation: "CREATE",
    data: { type: "user", name: "Alice" }
  });
  
  assert(typeof event.id === "string");
  assertEquals(event.clientId, "client1");
  assertEquals(event.vectorClock["client1"], 1);
});

Deno.test("複数クライアント間でのイベント同期", async () => {
  const server = new LocalSyncServer();
  const client1 = server.connect("client1");
  const client2 = server.connect("client2");
  
  // client1がイベント送信
  client1.send({
    operation: "CREATE",
    data: { id: "doc1", content: "Hello" }
  });
  
  // client2が受信
  const events = await client2.sync();
  assertEquals(events.length, 1);
  assertEquals(events[0].data.content, "Hello");
});

Deno.test("ベクタークロックによる因果関係追跡", async () => {
  const server = new LocalSyncServer();
  const client1 = server.connect("client1");
  const client2 = server.connect("client2");
  
  // 初期状態
  assertEquals(client1.getVectorClock(), { client1: 0 });
  assertEquals(client2.getVectorClock(), { client2: 0 });
  
  // client1がイベント送信
  client1.send({ operation: "CREATE", data: {} });
  assertEquals(client1.getVectorClock(), { client1: 1 });
  
  // client2が同期
  await client2.sync();
  assertEquals(client2.getVectorClock(), { client1: 1, client2: 0 });
});

// ========== 競合検出と解決 ==========

Deno.test("同時編集の競合検出", () => {
  const server = new LocalSyncServer();
  const client1 = server.connect("client1");
  const client2 = server.connect("client2");
  
  // 同じドキュメントを同時編集
  const event1 = client1.send({
    operation: "UPDATE",
    data: { id: "doc1", content: "Version A" }
  });
  
  const event2 = client2.send({
    operation: "UPDATE", 
    data: { id: "doc1", content: "Version B" }
  });
  
  const conflicts = server.detectConflicts([event1, event2]);
  assertEquals(conflicts.length, 1);
  assertEquals(conflicts[0].type, "CONFLICT");
});

Deno.test("Last Write Wins競合解決", () => {
  const server = new LocalSyncServer();
  server.setConflictStrategy("LAST_WRITE_WINS");
  
  const event1 = {
    id: "evt1",
    timestamp: 1000,
    data: { id: "doc1", value: "A" }
  };
  
  const event2 = {
    id: "evt2", 
    timestamp: 1001,
    data: { id: "doc1", value: "B" }
  };
  
  const resolution = server.resolveConflict(event1, event2);
  assertEquals(resolution.winner, event2);
  assertEquals(resolution.strategy, "LAST_WRITE_WINS");
});

Deno.test("カスタム競合解決戦略", () => {
  const server = new LocalSyncServer({
    conflictResolver: (a, b) => {
      // 文字列長が長い方を優先
      return a.data.content.length > b.data.content.length ? a : b;
    }
  });
  
  const event1 = { 
    id: "1",
    clientId: "client1",
    timestamp: 1000,
    operation: "UPDATE" as const,
    data: { content: "short" },
    vectorClock: {}
  };
  const event2 = { 
    id: "2",
    clientId: "client2", 
    timestamp: 1001,
    operation: "UPDATE" as const,
    data: { content: "much longer content" },
    vectorClock: {}
  };
  
  const resolution = server.resolveConflict(event1, event2);
  assertEquals(resolution.winner, event2);
});

// ========== リアルタイム通知 ==========

Deno.test("イベント発生時のリアルタイム通知", async () => {
  const server = new LocalSyncServer();
  const client1 = server.connect("client1");
  const client2 = server.connect("client2");
  
  const received: SyncEvent[] = [];
  client2.on("event", (event) => {
    received.push(event);
  });
  
  client1.send({ operation: "CREATE", data: { msg: "Hello" } });
  
  // 非同期で通知が届く
  await delay(10);
  assertEquals(received.length, 1);
  assertEquals(received[0].data.msg, "Hello");
});

Deno.test("選択的なイベント購読", async () => {
  const server = new LocalSyncServer();
  const client = server.connect("client1");
  
  const userEvents: SyncEvent[] = [];
  client.subscribe({
    filter: (event) => event.data.type === "user",
    handler: (event) => userEvents.push(event)
  });
  
  server.broadcast({ data: { type: "user", name: "Alice" } });
  server.broadcast({ data: { type: "post", title: "Hello" } });
  
  await delay(10);
  assertEquals(userEvents.length, 1);
  assertEquals(userEvents[0].data.name, "Alice");
});

// ========== 状態管理と永続化 ==========

Deno.test("サーバー側の状態スナップショット", () => {
  const server = new LocalSyncServer();
  
  // 複数のイベントを処理
  server.processEvent({ operation: "CREATE", data: { id: 1 } });
  server.processEvent({ operation: "UPDATE", data: { id: 1, name: "test" } });
  
  const snapshot = server.createSnapshot();
  assertEquals(snapshot.eventCount, 2);
  assertEquals(snapshot.clients.size, 0);
  assertExists(snapshot.timestamp);
});

Deno.test("クライアント再接続時の差分同期", async () => {
  const server = new LocalSyncServer();
  const client = server.connect("client1");
  
  // 初回同期
  await client.sync();
  const lastSync = client.getLastSync();
  
  // 新しいイベントが発生
  server.broadcast({ operation: "CREATE", data: {} });
  server.broadcast({ operation: "UPDATE", data: {} });
  
  // 差分のみ同期
  const events = await client.sync(lastSync);
  assertEquals(events.length, 2);
});

// ========== パフォーマンスとスケーラビリティ ==========

Deno.test("大量イベントのバッチ処理", async () => {
  const server = new LocalSyncServer({ batchSize: 100 });
  const client = server.connect("client1");
  
  // 1000イベントを送信
  const events = Array.from({ length: 1000 }, (_, i) => ({
    operation: "CREATE" as const,
    data: { id: i }
  }));
  
  const start = performance.now();
  await client.sendBatch(events);
  const duration = performance.now() - start;
  
  // バッチ処理により高速化
  assert(duration < 100); // 100ms以内
  assertEquals(server.getEventCount(), 1000);
});

Deno.test("メモリ効率的なイベントストリーム", async () => {
  const server = new LocalSyncServer({ maxMemoryEvents: 100 });
  
  // 200イベントを追加
  for (let i = 0; i < 200; i++) {
    server.processEvent({ operation: "CREATE", data: { id: i } });
  }
  
  // メモリ上は最新100件のみ保持
  assertEquals(server.getInMemoryEventCount(), 100);
  
  // 古いイベントはストレージから取得可能
  const allEvents = await server.getAllEvents();
  assertEquals(allEvents.length, 200);
});

// ========== エラーハンドリング ==========

Deno.test("不正なイベントデータの検証", () => {
  const server = new LocalSyncServer();
  const client = server.connect("client1");
  
  assertThrows(
    () => client.send({ operation: "INVALID" as any, data: {} }),
    Error,
    "Invalid operation"
  );
  
  assertThrows(
    () => client.send({ operation: "CREATE", data: null }),
    Error,
    "Data is required"
  );
});

Deno.test("同期タイムアウトの処理", async () => {
  const server = new LocalSyncServer({ syncTimeout: 100 });
  const client = server.connect("client1");
  
  // 遅延をシミュレート
  server.setSyncDelay(200);
  
  await assertRejects(
    () => client.sync(),
    Error,
    "Sync timeout"
  );
});

// ========== ヘルパー関数 ==========


// TDD Red Phase実行
if (import.meta.main) {
  console.log("=== Local Sync Engine - TDD Red Phase ===");
  console.log("すべてのテストが失敗することを確認してください。");
}
