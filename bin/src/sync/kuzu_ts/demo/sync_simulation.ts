/**
 * Synchronization Simulation
 * テンプレートベースの同期をシミュレート
 */

import { SyncClient } from "../core/websocket/client.ts";
import * as telemetry from "../telemetry_log.ts";

const clientId = Deno.args[0] || "sim-client-1";
const clientName = Deno.args[1] || "Simulation Client 1";

telemetry.info("Starting synchronization client", {
  clientId,
  clientName,
  timestamp: new Date().toISOString()
});

const client = new SyncClient(clientId, { autoReconnect: true });

// イベントハンドラー設定
client.onEvent((event) => {
  telemetry.info("Event received", {
    clientId,
    eventId: event.id,
    template: event.template,
    params: event.params || event.data,
    timestamp: new Date().toISOString()
  });
});

client.onHistoryReceived((events) => {
  telemetry.info("History received", {
    clientId,
    eventCount: events.length,
    timestamp: new Date().toISOString()
  });
});

// サーバーに接続
try {
  await client.connect("ws://localhost:8080");
  telemetry.info("Connected to server", {
    clientId,
    timestamp: new Date().toISOString()
  });
} catch (error) {
  telemetry.error("Connection failed", {
    clientId,
    error: error.message,
    timestamp: new Date().toISOString()
  });
  Deno.exit(1);
}

// 定期的にイベントを送信
let counter = 0;
const templates = ["user_action", "data_update", "sync_request"];

setInterval(async () => {
  const template = templates[counter % templates.length];
  const event = {
    id: `${clientId}-event-${Date.now()}`,
    template: template,
    timestamp: Date.now(),
    params: {
      counter: counter++,
      source: clientName,
      value: Math.floor(Math.random() * 100)
    }
  };
  
  try {
    await client.sendEvent(event);
    telemetry.info("Event sent", {
      clientId,
      eventId: event.id,
      template: event.template,
      params: event.params,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    telemetry.error("Failed to send event", {
      clientId,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
}, 3000); // 3秒ごと

// 終了処理
process.on("SIGINT", async () => {
  telemetry.info("Shutting down", {
    clientId,
    timestamp: new Date().toISOString()
  });
  await client.close();
  Deno.exit(0);
});