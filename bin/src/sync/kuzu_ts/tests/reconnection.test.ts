/**
 * TDD: Auto-reconnection feature tests
 * 仕様: WebSocket切断後3秒で自動再接続を開始する
 */

import { assertEquals, assert } from "jsr:@std/assert@^1.0.0";
import { SyncClient } from "../websocketClient.ts";

// WebSocketサーバーの起動を待つ
class TestServer {
  private process: Deno.ChildProcess | null = null;
  
  async start(): Promise<void> {
    const denoPath = Deno.env.get("DENO_PATH") || "deno";
    const command = new Deno.Command(denoPath, {
      args: ["run", "--allow-net", "./websocketServer.ts"],
      stdout: "piped",
      stderr: "piped",
    });
    
    this.process = command.spawn();
    
    // stdout/stderrを消費（リーク防止）
    this.consumeStream(this.process.stdout);
    this.consumeStream(this.process.stderr);
    
    // サーバー起動を待つ
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  private async consumeStream(stream: ReadableStream<Uint8Array>): Promise<void> {
    const reader = stream.getReader();
    (async () => {
      try {
        while (true) {
          const { done } = await reader.read();
          if (done) break;
        }
      } catch (error) {
        // Stream was cancelled
      } finally {
        reader.releaseLock();
      }
    })();
  }
  
  async stop(): Promise<void> {
    if (this.process) {
      this.process.kill();
      await this.process.status;
    }
  }
}

Deno.test("WebSocket auto-reconnection after disconnection", async () => {
  const server = new TestServer();
  await server.start();
  
  try {
    // 再接続可能なクライアントを作成
    const client = new SyncClient("reconnect-test", {
      autoReconnect: true,
      reconnectDelay: 1000, // 1秒後に再接続（テスト時間短縮）
    });

    // 接続状態を追跡
    let connectionAttempts = 0;
    client.on("connecting", () => {
      connectionAttempts++;
    });

    // 初回接続
    await client.connect("ws://localhost:8080");
    assertEquals(connectionAttempts, 1, "Initial connection should be made");

    // 接続を強制的に切断
    client.disconnect();
    
    // 1秒待つ前は再接続されない
    await new Promise(resolve => setTimeout(resolve, 500));
    assertEquals(connectionAttempts, 1, "Should not reconnect before delay");

    // 1秒後に再接続が試みられる
    await new Promise(resolve => setTimeout(resolve, 600));
    assertEquals(connectionAttempts, 2, "Should attempt reconnection after delay");

    // クリーンアップ
    client.close();
  } finally {
    await server.stop();
  }
});

Deno.test("Reconnection maintains client ID", async () => {
  const server = new TestServer();
  await server.start();
  
  try {
    const clientId = "persistent-client";
    const client = new SyncClient(clientId, {
      autoReconnect: true,
      reconnectDelay: 1000,
    });

    await client.connect("ws://localhost:8080");
    const originalId = client.getClientId();
    
    // 切断して再接続
    client.disconnect();
    await new Promise(resolve => setTimeout(resolve, 1100));
    
    // クライアントIDが維持されていることを確認
    assertEquals(client.getClientId(), originalId, "Client ID should be maintained after reconnection");
    
    client.close();
  } finally {
    await server.stop();
  }
});

Deno.test("Reconnection emits reconnected event", async () => {
  const server = new TestServer();
  await server.start();
  
  try {
    const client = new SyncClient("event-test", {
      autoReconnect: true,
      reconnectDelay: 1000,
    });

    let reconnectedEventFired = false;
    client.on("reconnected", () => {
      reconnectedEventFired = true;
    });

    await client.connect("ws://localhost:8080");
    
    // 切断して再接続
    client.disconnect();
    await new Promise(resolve => setTimeout(resolve, 1200));
    
    // 再接続イベントが発火されることを確認
    assert(reconnectedEventFired, "Reconnected event should be fired");
    
    client.close();
  } finally {
    await server.stop();
  }
});