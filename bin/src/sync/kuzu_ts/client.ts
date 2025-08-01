#!/usr/bin/env bun

/**
 * Minimal KuzuDB Sync Client
 * WebSocket経由でサーバーと同期
 */

import * as telemetry from "./telemetry_log.ts";
import { createInterface } from "readline";

const serverUrl = process.argv[2] || "ws://localhost:8080";
const clientName = process.env.CLIENT_NAME || process.argv[3];
const clientId = clientName || `client_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;

telemetry.info(`🔌 Connecting to ${serverUrl} as ${clientId}...`);

const ws = new WebSocket(`${serverUrl}?clientId=${clientId}`);

ws.addEventListener("open", () => {
  telemetry.info("✅ Connected to server");
  
  // Interactive prompt
  telemetry.info("\nCommands:");
  telemetry.info("  event <template> <params> - Send event");
  telemetry.info("  query <counterId>         - Query counter value");
  telemetry.info("  increment <counterId> [amount] - Increment counter");
  telemetry.info("  history                   - Request history");
  telemetry.info("  exit                      - Disconnect");
  telemetry.info("");
});

ws.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case "connected":
      telemetry.info(`📊 Server state: ${data.state.activeConnections} active connections`);
      break;
      
    case "event":
      if (data.payload.template === "COUNTER_VALUE") {
        telemetry.info(`📊 Counter ${data.payload.params.counterId} = ${data.payload.params.value}`);
      } else {
        telemetry.info(`📨 Received event: ${data.payload.template} from ${data.payload.clientId}`);
      }
      break;
      
    case "history":
      telemetry.info(`📜 History: ${data.events.length} events`);
      data.events.forEach((e: any) => {
        telemetry.info(`  - ${e.template} (${e.clientId})`);
      });
      break;
  }
});

ws.addEventListener("close", () => {
  telemetry.info("❌ Disconnected from server");
  process.exit(0);
});

ws.addEventListener("error", (error) => {
  telemetry.error("❌ WebSocket error:", { error: error });
});

// Create readline interface for stdin
const rl = createInterface({
  input: process.stdin,
  output: process.stdout
});

// Create async iterator for readline
async function* readLines() {
  for await (const line of rl) {
    yield line;
  }
}

// Process commands
(async () => {
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
        
      case "query":
        const queryCounterId = args[0];
        if (!queryCounterId) {
          telemetry.info("Usage: query <counterId>");
          break;
        }
        
        ws.send(JSON.stringify({
          type: "event",
          payload: {
            id: `evt_${Date.now()}`,
            template: "QUERY_COUNTER",
            params: { counterId: queryCounterId },
            clientId: clientId,
            timestamp: Date.now()
          }
        }));
        break;
        
      case "increment":
        const incCounterId = args[0];
        const amount = args[1] ? parseInt(args[1]) : 1;
        
        if (!incCounterId) {
          telemetry.info("Usage: increment <counterId> [amount]");
          break;
        }
        
        ws.send(JSON.stringify({
          type: "event",
          payload: {
            id: `evt_${Date.now()}`,
            template: "INCREMENT_COUNTER",
            params: { counterId: incCounterId, amount: amount },
            clientId: clientId,
            timestamp: Date.now()
          }
        }));
        telemetry.info(`✅ Incremented ${incCounterId} by ${amount}`);
        break;
        
      case "history":
        ws.send(JSON.stringify({
          type: "requestHistory",
          fromPosition: 0
        }));
        break;
        
      case "exit":
        rl.close();
        ws.close();
        break;
        
      default:
        telemetry.warn("Unknown command:", { command: cmd });
    }
  }
})();