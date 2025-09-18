/**
 * Basic History Sync Test
 * 履歴同期の基本動作確認
 */

import { connectToServer, waitFor } from "./websocket-client.ts";
import { assertEquals } from "jsr:@std/assert@^1.0.0";

// サーバー起動
const serverProcess = new Deno.Command("deno", {
  args: ["run", "--allow-net", "websocket-server.ts"],
  stdout: "piped",
  stderr: "piped"
}).spawn();

// サーバー起動を待つ
await new Promise(resolve => setTimeout(resolve, 2000));

try {
  console.log("=== Basic History Sync Test ===");
  
  // Client1: イベント作成
  console.log("1. Client1 creating events...");
  const client1 = await connectToServer("client1");
  
  await client1.sendEvent({
    id: "evt_1",
    template: "CREATE_USER",
    params: { id: "u1", name: "Alice" },
    clientId: "client1",
    timestamp: Date.now()
  });
  
  await client1.sendEvent({
    id: "evt_2",
    template: "CREATE_USER",
    params: { id: "u2", name: "Bob" },
    clientId: "client1",
    timestamp: Date.now()
  });
  
  console.log("✓ Events created");
  
  // Client2: 新規接続と履歴受信
  console.log("2. Client2 connecting and receiving history...");
  const client2 = await connectToServer("client2");
  
  const receivedEvents: any[] = [];
  client2.onHistoryReceived((events) => {
    console.log(`✓ Received ${events.length} historical events`);
    receivedEvents.push(...events);
  });
  
  // 履歴が自動的に受信されるまで待つ
  await waitFor(() => receivedEvents.length >= 2, 3000);
  
  // 検証
  console.log("3. Verifying history...");
  assertEquals(receivedEvents.length, 2);
  assertEquals(receivedEvents[0].id, "evt_1");
  assertEquals(receivedEvents[1].id, "evt_2");
  console.log("✓ History verified");
  
  // Client1: リアルタイムイベント
  console.log("4. Testing realtime sync after history...");
  const realtimeEvents: any[] = [];
  client2.onEvent((event) => {
    console.log("✓ Received realtime event");
    realtimeEvents.push(event);
  });
  
  await client1.sendEvent({
    id: "evt_3",
    template: "CREATE_USER",
    params: { id: "u3", name: "Charlie" },
    clientId: "client1",
    timestamp: Date.now()
  });
  
  await waitFor(() => realtimeEvents.length > 0);
  assertEquals(realtimeEvents[0].id, "evt_3");
  console.log("✓ Realtime sync working");
  
  // クリーンアップ
  await client1.disconnect();
  await client2.disconnect();
  
  console.log("\n✅ All tests passed!");
  
} catch (error) {
  console.error("❌ Test failed:", error);
  Deno.exit(1);
} finally {
  serverProcess.kill();
  await serverProcess.status;
}