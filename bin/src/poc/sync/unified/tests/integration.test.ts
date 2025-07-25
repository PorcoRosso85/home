/**
 * Integration tests for KuzuDB sync implementation
 * 実装言語（TypeScript）での統合テスト
 */

import { assertEquals, assert } from "jsr:@std/assert@^1.0.0";
import { SyncClient } from "../websocketClient.ts";

// WebSocketサーバーの型定義をインポート
interface ServerState {
  activeConnections: number;
  clientIds: string[];
  totalEventsProcessed: number;
}

// サーバー状態を取得するヘルパー関数
async function getServerState(): Promise<ServerState> {
  const response = await fetch("http://localhost:8080/state");
  return await response.json();
}

// テスト用のWebSocketサーバー管理
class TestServer {
  private process: Deno.ChildProcess | null = null;
  private stdout: ReadableStream<Uint8Array> | null = null;
  private stderr: ReadableStream<Uint8Array> | null = null;
  
  async start(port: number = 8080): Promise<void> {
    const denoPath = Deno.env.get("DENO_PATH") || "deno";
    const command = new Deno.Command(denoPath, {
      args: ["run", "--allow-net", "./websocketServer.ts"],
      stdout: "piped",
      stderr: "piped",
    });
    
    this.process = command.spawn();
    this.stdout = this.process.stdout;
    this.stderr = this.process.stderr;
    
    // stdout/stderrの読み取りを開始（バッファに溜まらないように）
    this.consumeStream(this.stdout);
    this.consumeStream(this.stderr);
    
    // サーバーの起動を待つ
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  private async consumeStream(stream: ReadableStream<Uint8Array>): Promise<void> {
    const reader = stream.getReader();
    try {
      while (true) {
        const { done } = await reader.read();
        if (done) break;
      }
    } catch (error) {
      // ストリームが閉じられた場合のエラーは無視
      if (!(error instanceof TypeError && error.message.includes("closed"))) {
        console.error("Stream consumption error:", error);
      }
    } finally {
      reader.releaseLock();
    }
  }
  
  async stop(): Promise<void> {
    if (this.process) {
      // プロセスを終了
      this.process.kill("SIGTERM");
      
      // ストリームを適切にキャンセル
      if (this.stdout) {
        try {
          await this.stdout.cancel();
        } catch (error) {
          // 既にキャンセル済みの場合は無視
        }
        this.stdout = null;
      }
      
      if (this.stderr) {
        try {
          await this.stderr.cancel();
        } catch (error) {
          // 既にキャンセル済みの場合は無視
        }
        this.stderr = null;
      }
      
      // プロセスの終了を待つ
      await this.process.status;
      this.process = null;
    }
  }
}

// テストケース
Deno.test("WebSocket client connection and disconnection", async () => {
  const server = new TestServer();
  await server.start();
  
  try {
    const client = new SyncClient("test-client-1");
    
    // 接続テスト
    await client.connect();
    assert(client.isConnected(), "Client should be connected");
    
    // サーバー状態の確認
    const state = await getServerState();
    assertEquals(state.activeConnections, 1);
    assert(state.clientIds.includes("test-client-1"));
    
    // 切断テスト
    await client.disconnect();
    assert(!client.isConnected(), "Client should be disconnected");
    
  } finally {
    await server.stop();
  }
});

Deno.test("Event sending and history", async () => {
  const server = new TestServer();
  await server.start();
  
  try {
    const client = new SyncClient("test-client-2");
    await client.connect();
    
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
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // 履歴を確認
    const history = await client.requestHistory({ fromPosition: 0 });
    assertEquals(history.events.length, 1);
    assertEquals(history.events[0].id, testEvent.id);
    assertEquals(history.events[0].template, testEvent.template);
    
    await client.disconnect();
    
  } finally {
    await server.stop();
  }
});

Deno.test("Multiple clients synchronization", async () => {
  const server = new TestServer();
  await server.start();
  
  try {
    // 2つのクライアントを接続
    const client1 = new SyncClient("multi-client-1");
    const client2 = new SyncClient("multi-client-2");
    
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
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Client2がイベントを受信したことを確認
    assertEquals(receivedEvents.length, 1);
    assertEquals(receivedEvents[0].id, event.id);
    assertEquals(receivedEvents[0].params.message, "Hello from client1");
    
    await client1.disconnect();
    await client2.disconnect();
    
  } finally {
    await server.stop();
  }
});

Deno.test("Subscription filtering", async () => {
  const server = new TestServer();
  await server.start();
  
  try {
    const client = new SyncClient("subscription-client");
    await client.connect();
    
    const userEvents: any[] = [];
    const systemEvents: any[] = [];
    
    // USER_EVENTのみサブスクライブ
    client.subscribe("USER_EVENT", (event) => {
      userEvents.push(event);
    });
    
    // 別クライアントから異なるタイプのイベントを送信
    const sender = new SyncClient("sender-client");
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
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // USER_EVENTのみ受信されていることを確認
    assertEquals(userEvents.length, 1);
    assertEquals(userEvents[0].template, "USER_EVENT");
    
    await client.disconnect();
    await sender.disconnect();
    
  } finally {
    await server.stop();
  }
});

Deno.test("History pagination", async () => {
  const server = new TestServer();
  await server.start();
  
  try {
    const client = new SyncClient("pagination-client");
    await client.connect();
    
    // 複数のイベントを送信
    for (let i = 0; i < 10; i++) {
      await client.sendEvent({
        id: crypto.randomUUID(),
        template: "PAGE_EVENT",
        params: { index: i },
        clientId: "pagination-client",
        timestamp: Date.now()
      });
      // 各イベント送信後に短い遅延を追加
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    
    // すべてのイベントが処理されるのを待つ
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // ページネーションテスト
    const page1 = await client.requestHistoryPage({ fromPosition: 0, limit: 5 });
    assertEquals(page1.events.length, 5);
    assertEquals(page1.events[0].params.index, 0);
    
    const page2 = await client.requestHistoryPage({ fromPosition: 5, limit: 5 });
    assertEquals(page2.events.length, 5);
    assertEquals(page2.events[0].params.index, 5);
    
    await client.disconnect();
    
  } finally {
    await server.stop();
  }
});

// エラーハンドリングのテスト
Deno.test("Error handling", async () => {
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