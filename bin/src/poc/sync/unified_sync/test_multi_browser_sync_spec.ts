/**
 * Multi-Browser Sync Specification - TDD Red Phase
 * 複数ブラウザ同期の仕様定義とテスト
 * 
 * 規約準拠:
 * - test_{機能}_{条件}_{結果} 命名規則
 * - ESモジュールのみ使用
 * - 視覚的要素なし（データ構造のみ）
 */

import { assertEquals, assert, assertExists } from "jsr:@std/assert@^1.0.0";
import { connectToServer, getServerState, waitFor } from "./websocket-client.ts";

// ========== 1. 複数クライアントからの同時接続 ==========

Deno.test("test_server_with_multiple_clients_accepts_concurrent_connections", async () => {
  // 3つのクライアントが同時に接続
  const client1 = await connectToServer("client1");
  const client2 = await connectToServer("client2");
  const client3 = await connectToServer("client3");
  
  try {
    // 全てのクライアントが接続状態
    assert(client1.isConnected());
    assert(client2.isConnected());
    assert(client3.isConnected());
    
    // サーバーは3つの接続を管理
    const serverState = await getServerState();
    assertEquals(serverState.activeConnections, 3);
    assertEquals(serverState.clientIds.length, 3);
  } finally {
    // クリーンアップ
    await client1.disconnect();
    await client2.disconnect();
    await client3.disconnect();
  }
});

// ========== 2. イベントのブロードキャスト ==========

Deno.test("test_server_with_event_from_one_client_broadcasts_to_others", async () => {
  const client1 = await connectToServer("client1");
  const client2 = await connectToServer("client2");
  const client3 = await connectToServer("client3");
  
  try {
    const receivedEvents: Map<string, any[]> = new Map([
      ["client2", []],
      ["client3", []]
    ]);
    
    // Client2, 3でイベント受信設定
    client2.onEvent((event) => receivedEvents.get("client2")!.push(event));
    client3.onEvent((event) => receivedEvents.get("client3")!.push(event));
    
    // Client1からイベント送信
    const event = {
      id: "evt_1",
      template: "CREATE_USER",
      params: { id: "u1", name: "Alice" },
      clientId: "client1",
      timestamp: Date.now()
    };
    
    await client1.sendEvent(event);
    
    // 送信元以外のクライアントがイベントを受信
    await waitFor(() => receivedEvents.get("client2")!.length > 0);
    await waitFor(() => receivedEvents.get("client3")!.length > 0);
    
    assertEquals(receivedEvents.get("client2")![0].id, "evt_1");
    assertEquals(receivedEvents.get("client3")![0].id, "evt_1");
  } finally {
    await client1.disconnect();
    await client2.disconnect();
    await client3.disconnect();
  }
});

// ========== 3. イベントの永続化と履歴 ==========

Deno.test("test_server_with_events_persists_and_provides_history", async () => {
  const client1 = await connectToServer("client1");
  
  try {
    // 複数イベントを送信
    const events = [
      { id: "evt_1", template: "CREATE_USER", params: { id: "u1", name: "Alice" } },
      { id: "evt_2", template: "CREATE_USER", params: { id: "u2", name: "Bob" } },
      { id: "evt_3", template: "UPDATE_USER", params: { id: "u1", name: "Alice Updated" } }
    ];
    
    for (const event of events) {
      await client1.sendEvent({ ...event, clientId: "client1", timestamp: Date.now() });
    }
    
    // 新しいクライアントが接続して履歴を要求
    const client2 = await connectToServer("client2");
    
    try {
      const history = await client2.requestHistory({ fromPosition: 0 });
      
      assertEquals(history.events.length, 3);
      assertEquals(history.events[0].id, "evt_1");
      assertEquals(history.events[2].template, "UPDATE_USER");
    } finally {
      await client2.disconnect();
    }
  } finally {
    await client1.disconnect();
  }
});

// ========== 4. 同時書き込みの順序保証 ==========

Deno.test("test_server_with_concurrent_writes_maintains_order", async () => {
  const client1 = await connectToServer("client1");
  const client2 = await connectToServer("client2");
  
  try {
    const allReceivedEvents: any[] = [];
    
    // 両クライアントでイベント受信設定
    const eventHandler = (event: any) => allReceivedEvents.push(event);
    client1.onEvent(eventHandler);
    client2.onEvent(eventHandler);
    
    // 同時にイベント送信（Promise.all）
    await Promise.all([
      client1.sendEvent({
        id: "evt_c1_1",
        template: "CREATE_POST",
        params: { id: "p1", content: "From Client1" },
        clientId: "client1",
        timestamp: Date.now()
      }),
      client2.sendEvent({
        id: "evt_c2_1", 
        template: "CREATE_POST",
        params: { id: "p2", content: "From Client2" },
        clientId: "client2",
        timestamp: Date.now()
      })
    ]);
    
    // 順序が保証されている（タイムスタンプ順）
    await waitFor(() => allReceivedEvents.length >= 2);
    
    const sortedEvents = allReceivedEvents.sort((a, b) => a.timestamp - b.timestamp);
    assertEquals(sortedEvents[0].id, allReceivedEvents[0].id);
    assertEquals(sortedEvents[1].id, allReceivedEvents[1].id);
  } finally {
    await client1.disconnect();
    await client2.disconnect();
  }
});

// ========== 5. クライアント切断とリソース管理 ==========

Deno.test("test_server_with_client_disconnect_cleans_up_resources", async () => {
  const client1 = await connectToServer("client1");
  const client2 = await connectToServer("client2");
  
  try {
    // 初期状態
    let serverState = await getServerState();
    assertEquals(serverState.activeConnections, 2);
    
    // Client1切断
    await client1.disconnect();
    
    // サーバー状態更新
    serverState = await getServerState();
    assertEquals(serverState.activeConnections, 1);
    assert(!serverState.clientIds.includes("client1"));
    assert(serverState.clientIds.includes("client2"));
    
    // Client2は引き続きイベント送受信可能
    const testEvent = {
      id: "evt_after_disconnect",
      template: "CREATE_USER",
      params: { id: "u3", name: "Charlie" },
      clientId: "client2",
      timestamp: Date.now()
    };
    
    await client2.sendEvent(testEvent);
    assert(client2.isConnected());
  } finally {
    // client1は既に切断済み
    await client2.disconnect();
  }
});

// ========== 6. エラーハンドリングと耐障害性 ==========

Deno.test("test_server_with_malformed_event_rejects_and_continues", async () => {
  const client1 = await connectToServer("client1");
  const client2 = await connectToServer("client2");
  
  try {
    let errorReceived = false;
    client1.onError((error) => {
      errorReceived = true;
    });
    
    // 不正なイベント送信
    try {
      await client1.sendEvent({
        // idなし（必須フィールド）
        template: "CREATE_USER",
        params: { name: "Invalid" },
        clientId: "client1",
        timestamp: Date.now()
      } as any);
    } catch (error: any) {
      assert(error.message.includes("Invalid event"));
    }
    
    // サーバーは動作継続
    const validEvent = {
      id: "evt_valid",
      template: "CREATE_USER", 
      params: { id: "u1", name: "Valid User" },
      clientId: "client2",
      timestamp: Date.now()
    };
    
    await client2.sendEvent(validEvent);
    
    const serverState = await getServerState();
    assertEquals(serverState.activeConnections, 2);
  } finally {
    await client1.disconnect();
    await client2.disconnect();
  }
});

// ========== 7. スケーラビリティテスト ==========

Deno.test("test_server_with_many_clients_handles_load", async () => {
  const clientCount = 50;
  const clients: any[] = [];
  
  try {
    // 50クライアント同時接続
    for (let i = 0; i < clientCount; i++) {
      const client = await connectToServer(`client_${i}`);
      clients.push(client);
    }
    
    // 全クライアントが接続状態
    assertEquals(clients.filter(c => c.isConnected()).length, clientCount);
    
    // 各クライアントからイベント送信
    const sendPromises = clients.map((client, index) => 
      client.sendEvent({
        id: `evt_${index}`,
        template: "CREATE_USER",
        params: { id: `u${index}`, name: `User${index}` },
        clientId: client.id,
        timestamp: Date.now()
      })
    );
    
    await Promise.all(sendPromises);
    
    // サーバー状態確認
    const serverState = await getServerState();
    assertEquals(serverState.totalEventsProcessed, clientCount);
    assertEquals(serverState.activeConnections, clientCount);
  } finally {
    // 全クライアントをクリーンアップ
    await Promise.all(clients.map(c => c.disconnect()));
  }
});

// ========== 8. イベントフィルタリング ==========

Deno.test("test_server_with_event_subscription_filters_by_template", async () => {
  const client1 = await connectToServer("client1");
  const client2 = await connectToServer("client2");
  
  try {
    const userEvents: any[] = [];
    const postEvents: any[] = [];
    
    // Client2で特定テンプレートのみ受信
    client2.subscribe("CREATE_USER", (event) => userEvents.push(event));
    client2.subscribe("CREATE_POST", (event) => postEvents.push(event));
    
    // 異なるタイプのイベント送信
    await client1.sendEvent({
      id: "evt_u1",
      template: "CREATE_USER",
      params: { id: "u1", name: "Alice" },
      clientId: "client1",
      timestamp: Date.now()
    });
    
    await client1.sendEvent({
      id: "evt_p1",
      template: "CREATE_POST",
      params: { id: "p1", content: "Hello" },
      clientId: "client1",
      timestamp: Date.now()
    });
    
    await client1.sendEvent({
      id: "evt_f1",
      template: "FOLLOW_USER",
      params: { followerId: "u1", targetId: "u2" },
      clientId: "client1",
      timestamp: Date.now()
    });
    
    await waitFor(() => userEvents.length > 0 && postEvents.length > 0);
    
    assertEquals(userEvents.length, 1);
    assertEquals(postEvents.length, 1);
    assertEquals(userEvents[0].template, "CREATE_USER");
    assertEquals(postEvents[0].template, "CREATE_POST");
  } finally {
    await client1.disconnect();
    await client2.disconnect();
  }
});

// ========== 実行 ==========

if (import.meta.main) {
  console.log("=== Multi-Browser Sync Specification - TDD Red Phase ===");
  console.log("必要な仕様:");
  console.log("1. 複数クライアントの同時接続管理");
  console.log("2. イベントの選択的ブロードキャスト（送信元除外）");
  console.log("3. イベント永続化と履歴提供");
  console.log("4. 同時書き込みの順序保証");
  console.log("5. クライアント切断時のリソース管理");
  console.log("6. エラーハンドリングと耐障害性");
  console.log("7. 多数クライアントのスケーラビリティ");
  console.log("8. イベントタイプ別のサブスクリプション");
}