/**
 * WebSocket Move Validation Test
 * Tests that WebSocket functionality works correctly after moving to core/websocket/
 * This is a RED test - it should fail initially because files haven't been moved yet.
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.210.0/assert/mod.ts";

// Import WebSocket components from the NEW location (core/websocket/)
// These imports should fail initially (RED test)
import { WebSocketSyncImpl } from "../core/websocket/sync.ts";
import { 
  SyncClient, 
  connectToServer, 
  getServerState as getClientServerState,
  waitFor 
} from "../core/websocket/client.ts";
import { getServerState } from "../core/websocket/server.ts";

// Also verify that types are available from the new location
import type { 
  WebSocketSync, 
  WebSocketMessage 
} from "../core/websocket/types.ts";

Deno.test("WebSocket imports resolve from core/websocket/", () => {
  // Verify that all imports are available
  assertExists(WebSocketSyncImpl, "WebSocketSyncImpl should be importable");
  assertExists(SyncClient, "SyncClient should be importable");
  assertExists(connectToServer, "connectToServer function should be importable");
  assertExists(getServerState, "getServerState function should be importable");
  assertExists(getClientServerState, "getClientServerState function should be importable");
  assertExists(waitFor, "waitFor function should be importable");
});

Deno.test("WebSocketSyncImpl can be instantiated", () => {
  const wsSync = new WebSocketSyncImpl();
  assertExists(wsSync, "WebSocketSyncImpl instance should be created");
  
  // Verify it implements the WebSocketSync interface
  assertEquals(typeof wsSync.connect, "function", "connect method should exist");
  assertEquals(typeof wsSync.disconnect, "function", "disconnect method should exist");
  assertEquals(typeof wsSync.sendEvent, "function", "sendEvent method should exist");
  assertEquals(typeof wsSync.onEvent, "function", "onEvent method should exist");
  assertEquals(typeof wsSync.isConnected, "function", "isConnected method should exist");
});

Deno.test("Public API is preserved after move", () => {
  // Verify that the public API structure is maintained
  const wsSync: WebSocketSync = new WebSocketSyncImpl();
  
  // This ensures the interface contract is preserved
  assertExists(wsSync, "WebSocketSync interface should be satisfied");
});

Deno.test("WebSocket client exports are available", () => {
  // Verify client-specific exports
  assertEquals(typeof SyncClient, "function", "SyncClient class should be available");
  assertEquals(typeof connectToServer, "function", "connectToServer should be a function");
  assertEquals(typeof getClientServerState, "function", "getClientServerState should be a function");
  assertEquals(typeof waitFor, "function", "waitFor should be a function");
});

Deno.test("WebSocket server exports are available", () => {
  // Verify server-specific exports
  assertEquals(typeof getServerState, "function", "getServerState should be a function");
});

// Integration test to ensure characterization test can still work
Deno.test("Characterization test compatibility", async () => {
  // This test verifies that the characterization test will still work
  // after the move by checking the same functionality
  
  const wsSync = new WebSocketSyncImpl();
  
  // Basic lifecycle test
  assertEquals(wsSync.isConnected(), false, "Should not be connected initially");
  
  // Note: We can't test actual connection without a server,
  // but we can verify the API is intact
});