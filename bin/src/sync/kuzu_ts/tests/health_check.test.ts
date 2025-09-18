/**
 * Health Check Endpoint Tests
 * ヘルスチェックエンドポイントのテスト
 */

import { assertEquals, assert } from "jsr:@std/assert";

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

websocketTest("health check endpoint returns system status", async () => {
  // サーバーが起動していることを前提
  const response = await fetch("http://localhost:8080/health");
  
  // ステータスコードの確認
  assertEquals(response.status, 200);
  assertEquals(response.headers.get("Content-Type"), "application/json");
  
  // レスポンスボディの確認
  const health = await response.json();
  
  // 必須フィールドの確認
  assertEquals(health.status, "healthy");
  assert(health.timestamp);
  assert(typeof health.uptime === "number");
  assert(health.uptime >= 0);
  assert(typeof health.connections === "number");
  assert(typeof health.totalEvents === "number");
  
  // ヘルスチェック項目の確認
  assert(health.checks);
  assert(health.checks.database === "connected" || health.checks.database === "disconnected");
  assertEquals(health.checks.websocket, "operational");
});

websocketTest("health check responds quickly", async () => {
  const startTime = performance.now();
  const response = await fetch("http://localhost:8080/health");
  const endTime = performance.now();
  
  const responseTime = endTime - startTime;
  
  // ヘルスチェックは100ms以内に応答すべき
  assert(responseTime < 100, `Health check took ${responseTime}ms, should be under 100ms`);
  
  // レスポンスが正常であることを確認
  assertEquals(response.status, 200);
});