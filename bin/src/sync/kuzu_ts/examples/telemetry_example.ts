/**
 * Example demonstrating the use of the telemetry wrapper
 * 
 * Run with: deno run --allow-write examples/telemetry_example.ts
 */

import { createTelemetryWrapper } from "../telemetry_wrapper.ts";

// Create a telemetry wrapper for the sync module
const telemetry = createTelemetryWrapper("kuzu:sync:example");

// Log basic information
telemetry.log("info", {
  message: "Starting sync example",
  timestamp: new Date().toISOString(),
});

// Simulate different contexts with dynamic URI updates
async function simulateWebSocketConnection() {
  // Change context to websocket
  telemetry.setUri("kuzu:sync:websocket");
  
  telemetry.log("debug", {
    message: "Attempting WebSocket connection",
    server: "ws://localhost:8080",
  });
  
  // Simulate connection success
  await new Promise(resolve => setTimeout(resolve, 100));
  
  telemetry.log("info", {
    message: "WebSocket connected successfully",
    connectionId: "ws-123",
  });
}

async function simulateDataSync() {
  // Change context to data sync
  telemetry.setUri("kuzu:sync:data");
  
  telemetry.log("info", {
    message: "Starting data synchronization",
    tables: ["users", "products", "orders"],
  });
  
  // Simulate sync progress
  for (let i = 1; i <= 3; i++) {
    await new Promise(resolve => setTimeout(resolve, 200));
    
    telemetry.log("debug", {
      message: `Synced table ${i} of 3`,
      progress: (i / 3) * 100,
    });
  }
  
  telemetry.log("info", {
    message: "Data synchronization completed",
    duration: "600ms",
    recordsSynced: 1500,
  });
}

async function simulateError() {
  // Change context to error handling
  telemetry.setUri("kuzu:sync:error");
  
  telemetry.log("error", {
    message: "Connection lost during sync",
    error: "ECONNRESET",
    retryCount: 3,
  });
  
  // Method chaining example
  telemetry
    .setUri("kuzu:sync:recovery")
    .log("info", {
      message: "Attempting automatic recovery",
      strategy: "exponential-backoff",
    });
}

// Run the example
async function main() {
  console.log("=== Telemetry Wrapper Example ===\n");
  
  await simulateWebSocketConnection();
  await simulateDataSync();
  await simulateError();
  
  // Back to main context
  telemetry.setUri("kuzu:sync:example");
  telemetry.log("info", {
    message: "Example completed",
    totalDuration: "1s",
  });
}

if (import.meta.main) {
  main();
}