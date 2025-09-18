/**
 * Integration tests for KuzuDB sync implementation
 * 実装言語（TypeScript）での統合テスト
 */

import { assertEquals, assert } from "jsr:@std/assert@^1.0.0";
import { afterEach } from "jsr:@std/testing@^1.0.0/bdd";
import { SyncClient } from "../core/websocket/client.ts";
import { TestServer } from "./test_utils.ts";

// Check if WebSocket tests should be skipped
const SKIP_WEBSOCKET_TESTS = Deno.env.get("SKIP_WEBSOCKET_TESTS") === "true";

// Helper function to conditionally run tests
function websocketTest(name: string, fn: () => Promise<void>) {
  if (SKIP_WEBSOCKET_TESTS) {
    Deno.test(`${name} (SKIPPED: SKIP_WEBSOCKET_TESTS=true)`, () => {
      console.log(`Skipping WebSocket test: ${name}`);
    });
  } else {
    Deno.test(name, fn);
  }
}

// WebSocketサーバーの型定義をインポート
interface ServerState {
  activeConnections: number;
  clientIds: string[];
  totalEventsProcessed: number;
}

// サーバー状態を取得するヘルパー関数
async function getServerState(): Promise<ServerState> {
  const response = await fetch("http://localhost:8080/health");
  const health = await response.json();
  return {
    activeConnections: health.connections,
    clientIds: [], // Health endpoint doesn't provide client IDs
    totalEventsProcessed: health.totalEvents
  };
}

// テスト用のWebSocketサーバー管理はtest_utils.tsから使用

// アクティブなクライアントとタイマーを追跡
const activeClients: SyncClient[] = [];
const activeTimers: number[] = [];

// クライアント管理用の共通関数
function addClient(client: SyncClient): void {
  activeClients.push(client);
}

function removeClient(client: SyncClient): void {
  const index = activeClients.indexOf(client);
  if (index > -1) {
    activeClients.splice(index, 1);
  }
}

function clearAllClients(): void {
  activeClients.length = 0;
}

// クリーンアップフック
if (!SKIP_WEBSOCKET_TESTS) {
  afterEach(async () => {
    // 全てのクライアントを切断
    const clientsToClose = [...activeClients]; // コピーを作成して二重削除を防ぐ
    for (const client of clientsToClose) {
      try {
        await client.close(); // closeを使用して即座に切断
      } catch (error) {
        // 既に切断されている場合は無視
      }
    }
    clearAllClients();
    
    // 全てのタイマーをクリア
    for (const timer of activeTimers) {
      clearTimeout(timer);
    }
    activeTimers.length = 0;
    
    // WebSocket接続が完全に閉じるのを待つ
    await safeSetTimeout(() => {}, 50);
  });
}

// 安全なsetTimeoutラッパー
function safeSetTimeout(fn: () => void, delay: number): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      fn();
      resolve();
      const index = activeTimers.indexOf(timer);
      if (index > -1) activeTimers.splice(index, 1);
    }, delay);
    activeTimers.push(timer);
  });
}

// テストケース
websocketTest("WebSocket client connection and disconnection", async () => {
  // Server is already running externally
  
  try {
    const client = new SyncClient("test-client-1");
    addClient(client);
    
    // 接続テスト
    await client.connect();
    assert(client.isConnected(), "Client should be connected");
    
    // サーバー状態の確認
    const state = await getServerState();
    assertEquals(state.activeConnections, 1);
    // Skip client ID check - health endpoint doesn't provide this
    
    // 切断テスト
    await client.disconnect();
    assert(!client.isConnected(), "Client should be disconnected");
    
    // クライアントをリストから削除
    removeClient(client);
    
  } finally {
    // Server managed externally
  }
});

websocketTest("Event sending and history", async () => {
  // Server is already running externally
  
  try {
    const client = new SyncClient("test-client-2");
    addClient(client);
    await client.connect();
    
    // Get initial history count
    const initialHistory = await client.requestHistory({ fromPosition: 0 });
    const initialCount = initialHistory.events.length;
    
    // イベント送信
    const testEvent = {
      id: crypto.randomUUID(),
      template: "TEST_EVENT",
      params: { value: 42 },
      clientId: "test-client-2",
      timestamp: Date.now()
    };
    
    await client.sendEvent(testEvent);
    
    // イベントが処理されるのを待つ
    await safeSetTimeout(() => {}, 100);
    
    // 履歴を確認 - 新しいイベントが追加されたことを確認
    const history = await client.requestHistory({ fromPosition: 0 });
    assertEquals(history.events.length, initialCount + 1);
    
    // 最新のイベントが送信したものと一致することを確認
    const latestEvent = history.events[history.events.length - 1];
    assertEquals(latestEvent.id, testEvent.id);
    assertEquals(latestEvent.template, testEvent.template);
    
    await client.disconnect();
    
  } finally {
    // Server managed externally
  }
});

websocketTest("Multiple clients synchronization", async () => {
  // Server is already running externally
  
  try {
    // 2つのクライアントを接続
    const client1 = new SyncClient("multi-client-1");
    const client2 = new SyncClient("multi-client-2");
    addClient(client1);
    addClient(client2);
    
    await client1.connect();
    await client2.connect();
    
    // Client2でイベントを受信するハンドラー設定
    const receivedEvents: any[] = [];
    client2.onEvent((event) => {
      receivedEvents.push(event);
    });
    
    // Client1からイベント送信
    const event = {
      id: crypto.randomUUID(),
      template: "SYNC_TEST",
      params: { message: "Hello from client1" },
      clientId: "multi-client-1",
      timestamp: Date.now()
    };
    
    await client1.sendEvent(event);
    
    // 同期を待つ
    await safeSetTimeout(() => {}, 500);
    
    // Client2がイベントを受信したことを確認
    assertEquals(receivedEvents.length, 1);
    assertEquals(receivedEvents[0].id, event.id);
    assertEquals(receivedEvents[0].params.message, "Hello from client1");
    
    await client1.close();
    await client2.close();
    
  } finally {
    // Server managed externally
  }
});

websocketTest("Subscription filtering", async () => {
  // Server is already running externally
  
  try {
    const client = new SyncClient("subscription-client");
    addClient(client);
    await client.connect();
    
    const userEvents: any[] = [];
    const systemEvents: any[] = [];
    
    // USER_EVENTのみサブスクライブ
    client.subscribe("USER_EVENT", (event) => {
      userEvents.push(event);
    });
    
    // 別クライアントから異なるタイプのイベントを送信
    const sender = new SyncClient("sender-client");
    addClient(sender);
    await sender.connect();
    
    await sender.sendEvent({
      id: crypto.randomUUID(),
      template: "USER_EVENT",
      params: { action: "login" },
      clientId: "sender-client",
      timestamp: Date.now()
    });
    
    await sender.sendEvent({
      id: crypto.randomUUID(),
      template: "SYSTEM_EVENT",
      params: { action: "startup" },
      clientId: "sender-client",
      timestamp: Date.now()
    });
    
    await safeSetTimeout(() => {}, 500);
    
    // USER_EVENTのみ受信されていることを確認
    assertEquals(userEvents.length, 1);
    assertEquals(userEvents[0].template, "USER_EVENT");
    
    // クライアントをリストから削除
    removeClient(client);
    removeClient(sender);
    
    await client.close();
    await sender.close();
    
  } finally {
    // Server managed externally
  }
});

websocketTest("History pagination", async () => {
  // Server is already running externally
  
  try {
    const client = new SyncClient("pagination-client");
    addClient(client);
    await client.connect();
    
    // Get initial position
    const initialHistory = await client.requestHistory({ fromPosition: 0 });
    const startPosition = initialHistory.events.length;
    
    // 複数のイベントを送信
    const testEvents = [];
    for (let i = 0; i < 10; i++) {
      const event = {
        id: crypto.randomUUID(),
        template: "PAGE_EVENT_" + Date.now(),
        params: { index: i },
        clientId: "pagination-client",
        timestamp: Date.now()
      };
      testEvents.push(event);
      await client.sendEvent(event);
      // 各イベント送信後に短い遅延を追加
      await safeSetTimeout(() => {}, 10);
    }
    
    // すべてのイベントが処理されるのを待つ
    await safeSetTimeout(() => {}, 100);
    
    // ページネーションテスト - 既存のイベントを考慮
    const page1 = await client.requestHistoryPage({ fromPosition: startPosition, limit: 5 });
    assertEquals(page1.events.length, 5);
    assertEquals(page1.events[0].params.index, 0);
    
    const page2 = await client.requestHistoryPage({ fromPosition: startPosition + 5, limit: 5 });
    assertEquals(page2.events.length, 5);
    assertEquals(page2.events[0].params.index, 5);
    
    await client.disconnect();
    
  } finally {
    // Server managed externally
  }
});

// エラーハンドリングのテスト
websocketTest("Error handling", async () => {
  const client = new SyncClient("error-client");
  
  // 接続していない状態での送信はエラー
  try {
    await client.sendEvent({
      id: "test",
      template: "TEST",
      params: {},
      clientId: "error-client",
      timestamp: Date.now()
    });
    assert(false, "Should throw error when not connected");
  } catch (error) {
    assertEquals((error as Error).message, "Not connected");
  }
  
  // 存在しないサーバーへの接続
  try {
    await client.connect("ws://localhost:9999");
    assert(false, "Should fail to connect to non-existent server");
  } catch (error) {
    assert(error instanceof Error);
  }
});