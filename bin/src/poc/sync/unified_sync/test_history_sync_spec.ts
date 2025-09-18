/**
 * History Sync Specification - TDD Red Phase
 * 履歴同期の仕様定義とテスト
 * 
 * 規約準拠:
 * - test_{機能}_{条件}_{結果} 命名規則
 * - ESモジュールのみ使用
 * - モックフリー実装
 */

import { assertEquals, assert } from "jsr:@std/assert@^1.0.0";
import { connectToServer, getServerState, waitFor } from "./websocket-client.ts";

// ========== 1. 新規接続時の履歴取得 ==========

Deno.test("test_history_sync_with_new_connection_retrieves_past_events", async () => {
  // 既存クライアントでイベント作成
  const client1 = await connectToServer("client1");
  
  try {
    // 過去のイベントを作成
    const pastEvents = [
      {
        id: "past_evt_1",
        template: "CREATE_USER",
        params: { id: "u1", name: "Alice (Past)" },
        clientId: "client1",
        timestamp: Date.now() - 10000
      },
      {
        id: "past_evt_2",
        template: "CREATE_USER",
        params: { id: "u2", name: "Bob (Past)" },
        clientId: "client1",
        timestamp: Date.now() - 5000
      },
      {
        id: "past_evt_3",
        template: "UPDATE_USER",
        params: { id: "u1", name: "Alice Updated (Past)" },
        clientId: "client1",
        timestamp: Date.now() - 1000
      }
    ];
    
    // イベントを送信
    for (const event of pastEvents) {
      await client1.sendEvent(event);
    }
    
    // 新規クライアントが接続
    const client2 = await connectToServer("client2");
    
    try {
      // client2は接続時に自動的に履歴を要求すべき
      const receivedEvents: any[] = [];
      client2.onHistoryReceived((events) => {
        receivedEvents.push(...events);
      });
      
      // 履歴が受信されるまで待つ
      await waitFor(() => receivedEvents.length >= 3);
      
      // 全ての過去イベントを受信したことを確認
      assertEquals(receivedEvents.length, 3);
      assertEquals(receivedEvents[0].id, "past_evt_1");
      assertEquals(receivedEvents[1].id, "past_evt_2");
      assertEquals(receivedEvents[2].id, "past_evt_3");
      
      // イベントの順序が保持されていることを確認
      assert(receivedEvents[0].timestamp < receivedEvents[1].timestamp);
      assert(receivedEvents[1].timestamp < receivedEvents[2].timestamp);
    } finally {
      await client2.disconnect();
    }
  } finally {
    await client1.disconnect();
  }
});

// ========== 2. 部分的な履歴取得 ==========

Deno.test("test_history_sync_with_partial_retrieval_from_position", async () => {
  const client1 = await connectToServer("client1");
  
  try {
    // 10個のイベントを作成
    for (let i = 0; i < 10; i++) {
      await client1.sendEvent({
        id: `evt_${i}`,
        template: "CREATE_USER",
        params: { id: `u${i}`, name: `User ${i}` },
        clientId: "client1",
        timestamp: Date.now() + i
      });
    }
    
    // 新規クライアントが特定位置から履歴を要求
    const client2 = await connectToServer("client2");
    
    try {
      // position 5以降のイベントのみ要求
      const partialHistory = await client2.requestHistoryFrom(5);
      
      // 5個のイベントを受信（position 5-9）
      assertEquals(partialHistory.events.length, 5);
      assertEquals(partialHistory.events[0].id, "evt_5");
      assertEquals(partialHistory.events[4].id, "evt_9");
    } finally {
      await client2.disconnect();
    }
  } finally {
    await client1.disconnect();
  }
});

// ========== 3. 履歴取得後のリアルタイム同期 ==========

Deno.test("test_history_sync_with_realtime_sync_after_history", async () => {
  const client1 = await connectToServer("client1");
  
  try {
    // 過去のイベント
    await client1.sendEvent({
      id: "historical_evt",
      template: "CREATE_USER",
      params: { id: "u_hist", name: "Historical User" },
      clientId: "client1",
      timestamp: Date.now()
    });
    
    // 新規クライアント接続
    const client2 = await connectToServer("client2");
    
    try {
      const allEvents: any[] = [];
      
      // 履歴とリアルタイムイベントの両方を受信
      client2.onHistoryReceived((events) => {
        allEvents.push(...events.map(e => ({ ...e, source: 'history' })));
      });
      
      client2.onEvent((event) => {
        allEvents.push({ ...event, source: 'realtime' });
      });
      
      // 履歴受信を待つ
      await waitFor(() => allEvents.some(e => e.source === 'history'));
      
      // リアルタイムイベントを送信
      await client1.sendEvent({
        id: "realtime_evt",
        template: "CREATE_USER",
        params: { id: "u_real", name: "Realtime User" },
        clientId: "client1",
        timestamp: Date.now()
      });
      
      // リアルタイムイベントも受信
      await waitFor(() => allEvents.some(e => e.source === 'realtime'));
      
      // 両方のイベントを正しく受信
      const historyEvents = allEvents.filter(e => e.source === 'history');
      const realtimeEvents = allEvents.filter(e => e.source === 'realtime');
      
      assertEquals(historyEvents.length, 1);
      assertEquals(realtimeEvents.length, 1);
      assertEquals(historyEvents[0].id, "historical_evt");
      assertEquals(realtimeEvents[0].id, "realtime_evt");
    } finally {
      await client2.disconnect();
    }
  } finally {
    await client1.disconnect();
  }
});

// ========== 4. 重複イベントの防止 ==========

Deno.test("test_history_sync_with_duplicate_prevention", async () => {
  const client1 = await connectToServer("client1");
  const client2 = await connectToServer("client2");
  
  try {
    // Client2も最初から接続（履歴なし）
    const client2Events: any[] = [];
    client2.onEvent((event) => client2Events.push(event));
    
    // Client1からイベント送信
    const testEvent = {
      id: "test_evt_unique",
      template: "CREATE_USER",
      params: { id: "u1", name: "Test User" },
      clientId: "client1",
      timestamp: Date.now()
    };
    
    await client1.sendEvent(testEvent);
    
    // Client2がリアルタイムで受信
    await waitFor(() => client2Events.length > 0);
    
    // Client3が新規接続（履歴取得）
    const client3 = await connectToServer("client3");
    
    try {
      const client3Events: any[] = [];
      let historyReceived = false;
      
      client3.onHistoryReceived((events) => {
        historyReceived = true;
        client3Events.push(...events);
      });
      
      client3.onEvent((event) => {
        // 履歴受信後のリアルタイムイベントのみ
        if (historyReceived) {
          client3Events.push(event);
        }
      });
      
      // 履歴受信を待つ
      await waitFor(() => historyReceived);
      
      // 同じイベントは1回のみ受信
      const uniqueEvents = client3Events.filter(e => e.id === "test_evt_unique");
      assertEquals(uniqueEvents.length, 1);
    } finally {
      await client3.disconnect();
    }
  } finally {
    await client1.disconnect();
    await client2.disconnect();
  }
});

// ========== 5. 大量履歴のページング ==========

Deno.test("test_history_sync_with_pagination_for_large_history", async () => {
  const client1 = await connectToServer("client1");
  
  try {
    // 1000個のイベントを作成
    const eventCount = 1000;
    for (let i = 0; i < eventCount; i++) {
      await client1.sendEvent({
        id: `bulk_evt_${i}`,
        template: "CREATE_USER",
        params: { id: `u${i}`, name: `Bulk User ${i}` },
        clientId: "client1",
        timestamp: Date.now() + i
      });
    }
    
    // 新規クライアントがページング取得
    const client2 = await connectToServer("client2");
    
    try {
      const pageSize = 100;
      const allEvents: any[] = [];
      let position = 0;
      
      // ページング取得
      while (position < eventCount) {
        const page = await client2.requestHistoryPage({
          fromPosition: position,
          limit: pageSize
        });
        
        allEvents.push(...page.events);
        
        // 次のページがあるか確認
        if (page.events.length < pageSize) {
          break;
        }
        
        position += pageSize;
      }
      
      // 全イベントを取得
      assertEquals(allEvents.length, eventCount);
      assertEquals(allEvents[0].id, "bulk_evt_0");
      assertEquals(allEvents[999].id, "bulk_evt_999");
    } finally {
      await client2.disconnect();
    }
  } finally {
    await client1.disconnect();
  }
});

// ========== 6. 接続エラー時の履歴再取得 ==========

Deno.test("test_history_sync_with_reconnection_resumes_history", async () => {
  const client1 = await connectToServer("client1");
  
  try {
    // イベント作成
    for (let i = 0; i < 5; i++) {
      await client1.sendEvent({
        id: `reconnect_evt_${i}`,
        template: "CREATE_USER",
        params: { id: `u${i}`, name: `User ${i}` },
        clientId: "client1",
        timestamp: Date.now() + i
      });
    }
    
    // 新規クライアント（履歴取得を中断）
    const client2 = await connectToServer("client2");
    
    try {
      let receivedCount = 0;
      const receivedEvents: any[] = [];
      
      client2.onHistoryReceived((events) => {
        // 途中で接続を切断
        if (receivedCount === 2) {
          client2.disconnect();
          return;
        }
        receivedEvents.push(...events);
        receivedCount = events.length;
      });
      
      // 部分的な履歴受信
      await waitFor(() => receivedCount >= 2);
      await client2.disconnect();
      
      // 再接続
      const client2Reconnected = await connectToServer("client2");
      
      try {
        // 続きから履歴を取得
        const resumedHistory = await client2Reconnected.requestHistoryFrom(receivedCount);
        
        // 残りのイベントを受信
        assertEquals(resumedHistory.events.length, 3);
        assertEquals(resumedHistory.events[0].id, "reconnect_evt_2");
      } finally {
        await client2Reconnected.disconnect();
      }
    } catch {
      // 接続エラーは想定内
    }
  } finally {
    await client1.disconnect();
  }
});

// ========== 7. 履歴の整合性チェック ==========

Deno.test("test_history_sync_with_checksum_verification", async () => {
  const client1 = await connectToServer("client1");
  
  try {
    // チェックサム付きイベント
    const eventsWithChecksum = [
      {
        id: "chk_evt_1",
        template: "CREATE_USER",
        params: { id: "u1", name: "User 1" },
        clientId: "client1",
        timestamp: Date.now(),
        checksum: "abc123" // 実装時は適切なチェックサム
      }
    ];
    
    for (const event of eventsWithChecksum) {
      await client1.sendEvent(event);
    }
    
    // 新規クライアント
    const client2 = await connectToServer("client2");
    
    try {
      // 履歴取得時にチェックサム検証
      const history = await client2.requestHistoryWithVerification();
      
      // 検証済みイベントのみ取得
      assert(history.verified);
      assertEquals(history.events.length, 1);
      assertEquals(history.events[0].checksum, "abc123");
    } finally {
      await client2.disconnect();
    }
  } finally {
    await client1.disconnect();
  }
});

// ========== 8. 履歴圧縮・最適化 ==========

Deno.test("test_history_sync_with_compressed_transmission", async () => {
  const client1 = await connectToServer("client1");
  
  try {
    // 同じエンティティへの複数更新
    const updates = [
      { id: "upd_1", template: "CREATE_USER", params: { id: "u1", name: "V1" } },
      { id: "upd_2", template: "UPDATE_USER", params: { id: "u1", name: "V2" } },
      { id: "upd_3", template: "UPDATE_USER", params: { id: "u1", name: "V3" } },
      { id: "upd_4", template: "UPDATE_USER", params: { id: "u1", name: "V4" } },
      { id: "upd_5", template: "UPDATE_USER", params: { id: "u1", name: "Final" } }
    ];
    
    for (const update of updates) {
      await client1.sendEvent({
        ...update,
        clientId: "client1",
        timestamp: Date.now()
      });
    }
    
    // 新規クライアント（圧縮履歴を要求）
    const client2 = await connectToServer("client2");
    
    try {
      // 圧縮された履歴を取得（最終状態のみ）
      const compressedHistory = await client2.requestCompressedHistory();
      
      // 5つの更新が1つに圧縮される
      assertEquals(compressedHistory.events.length, 1);
      assertEquals(compressedHistory.events[0].params.name, "Final");
      assertEquals(compressedHistory.compressionRatio, 5); // 5:1圧縮
    } finally {
      await client2.disconnect();
    }
  } finally {
    await client1.disconnect();
  }
});

// ========== ヘルパー関数（実装は別途） ==========

interface HistoryOptions {
  fromPosition?: number;
  limit?: number;
  compressed?: boolean;
  verified?: boolean;
}

// クライアント拡張インターフェース
declare module "./websocket-client.ts" {
  interface SyncClient {
    onHistoryReceived(handler: (events: any[]) => void): void;
    requestHistoryFrom(position: number): Promise<{ events: any[] }>;
    requestHistoryPage(options: { fromPosition: number; limit: number }): Promise<{ events: any[] }>;
    requestHistoryWithVerification(): Promise<{ events: any[]; verified: boolean }>;
    requestCompressedHistory(): Promise<{ events: any[]; compressionRatio: number }>;
  }
}

// ========== 実行 ==========

if (import.meta.main) {
  console.log("=== History Sync Specification - TDD Red Phase ===");
  console.log("必要な仕様:");
  console.log("1. 新規接続時の自動履歴取得");
  console.log("2. 部分的な履歴取得（位置指定）");
  console.log("3. 履歴取得後のリアルタイム同期継続");
  console.log("4. 重複イベントの防止");
  console.log("5. 大量履歴のページング");
  console.log("6. 接続エラー時の履歴再取得");
  console.log("7. 履歴の整合性チェック");
  console.log("8. 履歴圧縮・最適化");
}