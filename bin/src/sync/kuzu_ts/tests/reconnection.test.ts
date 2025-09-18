/**
 * TDD: Auto-reconnection feature tests
 * 仕様: WebSocket切断後3秒で自動再接続を開始する
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

// WebSocketサーバーの起動を待つ中間クラスはtest_utils.tsから使用

// アクティブなクライアントとタイマーを追跡
const activeClients: SyncClient[] = [];
const activeTimers: number[] = [];

// クリーンアップフック
if (!SKIP_WEBSOCKET_TESTS) {
  afterEach(async () => {
  // 全てのクライアントを切断
  for (const client of activeClients) {
    try {
      await client.close(); // closeを使用して自動再接続も停止
    } catch (error) {
      // 既に切断されている場合は無視
    }
  }
  activeClients.length = 0;
  
  // 全てのタイマーをクリア
  for (const timer of activeTimers) {
    clearTimeout(timer);
  }
  activeTimers.length = 0;
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

websocketTest("WebSocket auto-reconnection after disconnection", async () => {
  // Server is already running externally
  
  try {
    // 再接続可能なクライアントを作成
    const client = new SyncClient("reconnect-test", {
      autoReconnect: true,
      reconnectDelay: 1000, // 1秒後に再接続（テスト時間短縮）
    });
    activeClients.push(client);

    // 接続状態を追跡
    let connectionAttempts = 0;
    client.on("connecting", () => {
      connectionAttempts++;
    });

    // 初回接続
    await client.connect("ws://localhost:8080");
    assertEquals(connectionAttempts, 1, "Initial connection should be made");

    // 接続を強制的に切断
    await client.disconnect();
    
    // 1秒待つ前は再接続されない
    await safeSetTimeout(() => {}, 500);
    assertEquals(connectionAttempts, 1, "Should not reconnect before delay");

    // 1秒後に再接続が試みられる
    await safeSetTimeout(() => {}, 600);
    assertEquals(connectionAttempts, 2, "Should attempt reconnection after delay");

    // クリーンアップ
    await client.close();
  } finally {
    // Server managed externally
  }
});

websocketTest("Reconnection maintains client ID", async () => {
  // Server is already running externally
  
  try {
    const clientId = "persistent-client";
    const client = new SyncClient(clientId, {
      autoReconnect: true,
      reconnectDelay: 1000,
    });
    activeClients.push(client);

    await client.connect("ws://localhost:8080");
    const originalId = client.getClientId();
    
    // 切断して再接続
    await client.disconnect();
    await safeSetTimeout(() => {}, 1100);
    
    // クライアントIDが維持されていることを確認
    assertEquals(client.getClientId(), originalId, "Client ID should be maintained after reconnection");
    
    await client.close();
  } finally {
    // Server managed externally
  }
});

websocketTest("Reconnection emits reconnected event", async () => {
  // Server is already running externally
  
  try {
    const client = new SyncClient("event-test", {
      autoReconnect: true,
      reconnectDelay: 1000,
    });
    activeClients.push(client);

    let reconnectedEventFired = false;
    client.on("reconnected", () => {
      reconnectedEventFired = true;
    });

    await client.connect("ws://localhost:8080");
    
    // 切断して再接続
    await client.disconnect();
    await safeSetTimeout(() => {}, 1200);
    
    // 再接続イベントが発火されることを確認
    assert(reconnectedEventFired, "Reconnected event should be fired");
    
    await client.close();
  } finally {
    // Server managed externally
  }
});