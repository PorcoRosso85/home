/**
 * Test Runner with Server Lifecycle Management
 * サーバーの起動と停止を管理するテストランナー
 */

/**
 * Test Runner with Server Lifecycle Management
 * サーバーの起動と停止を管理するテストランナー
 */

// サーバープロセスを起動
const serverProcess = new Deno.Command("deno", {
  args: ["run", "--allow-net", "websocket-server.ts"],
  stdout: "piped",
  stderr: "piped"
}).spawn();

// サーバー起動を待つ
await new Promise(resolve => setTimeout(resolve, 2000));

console.log("=== Server started, running tests ===");

try {
  // テスト実行
  const testProcess = new Deno.Command("deno", {
    args: ["test", "--allow-net", "--allow-read", "--no-check", "test_multi_browser_sync_spec.ts"],
    stdout: "inherit",
    stderr: "inherit"
  }).spawn();
  
  const testStatus = await testProcess.status;
  
  if (!testStatus.success) {
    Deno.exit(1);
  }
} finally {
  console.log("=== Stopping server ===");
  serverProcess.kill();
  await serverProcess.status;
}