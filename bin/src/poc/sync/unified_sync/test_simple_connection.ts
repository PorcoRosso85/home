/**
 * Simple Connection Test
 * 接続テスト
 */

import { connectToServer } from "./websocket-client.ts";

// サーバー起動
const serverProcess = new Deno.Command("deno", {
  args: ["run", "--allow-net", "websocket-server.ts"],
  stdout: "piped", 
  stderr: "piped"
}).spawn();

// サーバー起動を待つ
await new Promise(resolve => setTimeout(resolve, 2000));

try {
  console.log("Connecting to server...");
  const client = await connectToServer("test_client");
  console.log("Connected:", client.isConnected());
  
  await client.disconnect();
  console.log("Test passed!");
} catch (error) {
  console.error("Test failed:", error);
} finally {
  serverProcess.kill();
  await serverProcess.status;
}