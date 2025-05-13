#!/usr/bin/env -S nix run nixpkgs#deno -- run --allow-net --allow-run

/**
 * claude-code-proxy.ts
 * Claude Code MCPサーバーをHTTP/SSEプロキシ経由で実行するスクリプト
 */

import { createProxy, startProxy } from "./mod.ts";

const CLAUDE_CODE_COMMAND = "pnpx";
const CLAUDE_CODE_ARGS = ["@anthropic-ai/claude-code", "mcp", "serve"];

// コマンドライン引数の処理
const args = Deno.args;
let address = "0.0.0.0";
let port = 8080;
let verbose = false;

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg === "--address" || arg === "-a") {
    address = args[++i] || address;
  } else if (arg === "--port" || arg === "-p") {
    const portArg = parseInt(args[++i] || "8080", 10);
    if (!isNaN(portArg)) {
      port = portArg;
    }
  } else if (arg === "--verbose" || arg === "-v") {
    verbose = true;
  } else if (arg === "--help" || arg === "-h") {
    console.log("Claude Code MCPサーバープロキシ");
    console.log("");
    console.log("使用方法: claude-code-proxy.ts [オプション]");
    console.log("");
    console.log("オプション:");
    console.log("  --address, -a <address>  リッスンするアドレス (デフォルト: 0.0.0.0)");
    console.log("  --port, -p <port>        リッスンするポート (デフォルト: 8080)");
    console.log("  --verbose, -v            詳細なログ出力を有効にする");
    console.log("  --help, -h               このヘルプメッセージを表示");
    console.log("");
    console.log("例:");
    console.log("  claude-code-proxy.ts --port 3000 --verbose");
    Deno.exit(0);
  }
}

// Claude Code MCPサーバーのプロキシ作成
console.log(`Claude Code MCPサーバーの起動 (HTTP/SSEプロキシ: ${address}:${port})`);

// プロキシ設定
const proxy = createProxy({
  address,
  port,
  command: CLAUDE_CODE_COMMAND,
  args: CLAUDE_CODE_ARGS,
  verbose,
});

// シグナルハンドリングの設定
const cleanup = () => {
  console.log("\nシャットダウン中...");
  Deno.exit(0);
};

Deno.addSignalListener("SIGINT", cleanup);
Deno.addSignalListener("SIGTERM", cleanup);

// プロキシの起動
try {
  const result = await startProxy(proxy);
  
  if (!result.ok) {
    console.error(`プロキシの起動に失敗しました: ${result.error.message}`);
    Deno.exit(1);
  }
  
  console.log(`Claude Code MCPサーバーが起動しました`);
  console.log(`プロキシは ${address}:${port} でリッスン中です`);
  console.log("Ctrl+Cで停止できます");
  
  // プロセスを実行し続ける
  await new Promise(() => {});
} catch (error) {
  console.error("予期しないエラーが発生しました:", error);
  Deno.exit(1);
}
