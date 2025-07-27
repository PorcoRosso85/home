#!/usr/bin/env -S deno run --allow-net

/**
 * Minimal KuzuDB Sync Client
 * WebSocket経由でサーバーと同期
 */

const serverUrl = Deno.args[0] || "ws://localhost:8080";
const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;

console.log(`🔌 Connecting to ${serverUrl} as ${clientId}...`);

const ws = new WebSocket(`${serverUrl}?clientId=${clientId}`);

ws.addEventListener("open", () => {
  console.log("✅ Connected to server");
  
  // Interactive prompt
  console.log("\nCommands:");
  console.log("  event <template> <params> - Send event");
  console.log("  history                   - Request history");
  console.log("  exit                      - Disconnect");
  console.log("");
});

ws.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case "connected":
      console.log(`📊 Server state: ${data.state.activeConnections} active connections`);
      break;
      
    case "event":
      console.log(`📨 Received event: ${data.payload.template} from ${data.payload.clientId}`);
      break;
      
    case "history":
      console.log(`📜 History: ${data.events.length} events`);
      data.events.forEach((e: any) => {
        console.log(`  - ${e.template} (${e.clientId})`);
      });
      break;
  }
});

ws.addEventListener("close", () => {
  console.log("❌ Disconnected from server");
  Deno.exit(0);
});

ws.addEventListener("error", (error) => {
  console.error("❌ WebSocket error:", error);
});

// Read from stdin
for await (const line of readLines()) {
  const [cmd, ...args] = line.split(" ");
  
  switch (cmd) {
    case "event":
      const template = args[0];
      const params = args.slice(1).join(" ");
      
      ws.send(JSON.stringify({
        type: "event",
        payload: {
          id: `evt_${Date.now()}`,
          template: template,
          params: params ? JSON.parse(params) : {},
          clientId: clientId,
          timestamp: Date.now()
        }
      }));
      break;
      
    case "history":
      ws.send(JSON.stringify({
        type: "requestHistory",
        fromPosition: 0
      }));
      break;
      
    case "exit":
      ws.close();
      break;
      
    default:
      console.log("Unknown command:", cmd);
  }
}

async function* readLines() {
  const decoder = new TextDecoder();
  const reader = Deno.stdin.readable.getReader();
  let buffer = "";
  
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      
      for (const line of lines) {
        if (line.trim()) yield line.trim();
      }
    }
  } finally {
    reader.releaseLock();
  }
}