#!/usr/bin/env -S nix run nixpkgs#deno -- run --allow-net --allow-run --allow-env

/**
 * mcp-proxy-cli.ts
 * 任意のMCPサーバーをHTTP/SSEプロキシ経由で実行するCLIスクリプト
 */

import { createProxy, startProxy } from "./mod.ts";

// ヘルプ表示関数
function showHelp() {
  console.log("MCP Transport Proxy CLI");
  console.log("");
  console.log("使用方法: mcp-proxy-cli.ts [オプション] -- <MCPサーバーコマンド> [MCPサーバー引数...]");
  console.log("");
  console.log("オプション:");
  console.log("  --address, -a <address>  リッスンするアドレス (デフォルト: 0.0.0.0)");
  console.log("  --port, -p <port>        リッスンするポート (デフォルト: 8080)");
  console.log("  --verbose, -v            詳細なログ出力を有効にする");
  console.log("  --help, -h               このヘルプメッセージを表示");
  console.log("");
  console.log("例:");
  console.log("  ./mcp-proxy-cli.ts -- pnpx @anthropic-ai/claude-code mcp serve");
  console.log("  ./mcp-proxy-cli.ts --port 3000 -- npm exec -- @anthropic-ai/claude-code mcp serve");
  console.log("  ./mcp-proxy-cli.ts -- node your-mcp-server.js");
  console.log("");
  console.log("注意:");
  console.log("  MCPサーバーコマンドは '--' の後に指定してください。");
}

// コマンドライン引数の解析
function parseArgs(rawArgs: string[]) {
  const options = {
    address: "0.0.0.0",
    port: 8080,
    verbose: false,
    serverCommand: "",
    serverArgs: [] as string[],
  };

  let i = 0;
  let foundSeparator = false;

  // オプションの解析
  while (i < rawArgs.length) {
    const arg = rawArgs[i];
    
    // コマンド区切り
    if (arg === "--") {
      foundSeparator = true;
      i++;
      break;
    }
    
    // オプション解析
    if (arg === "--address" || arg === "-a") {
      if (i + 1 >= rawArgs.length || rawArgs[i + 1].startsWith("-")) {
        console.error(`エラー: ${arg} オプションに値が必要です`);
        return null;
      }
      options.address = rawArgs[++i];
    } else if (arg === "--port" || arg === "-p") {
      if (i + 1 >= rawArgs.length || rawArgs[i + 1].startsWith("-")) {
        console.error(`エラー: ${arg} オプションに値が必要です`);
        return null;
      }
      
      const port = parseInt(rawArgs[++i], 10);
      if (isNaN(port) || port < 1 || port > 65535) {
        console.error("エラー: ポートは1から65535の間の数値である必要があります");
        return null;
      }
      
      options.port = port;
    } else if (arg === "--verbose" || arg === "-v") {
      options.verbose = true;
    } else if (arg === "--help" || arg === "-h") {
      showHelp();
      Deno.exit(0);
    } else {
      console.error(`エラー: 不明なオプション: ${arg}`);
      return null;
    }
    
    i++;
  }
  
  // サーバーコマンドと引数の解析
  if (foundSeparator && i < rawArgs.length) {
    options.serverCommand = rawArgs[i];
    options.serverArgs = rawArgs.slice(i + 1);
  }
  
  // コマンドの検証
  if (!options.serverCommand) {
    console.error("エラー: MCPサーバーコマンドが指定されていません");
    return null;
  }
  
  return options;
}

// メイン処理
async function main() {
  // 引数の解析
  const options = parseArgs(Deno.args);
  
  if (!options) {
    showHelp();
    Deno.exit(1);
  }
  
  console.log(`MCPサーバープロキシの起動 (HTTP/SSEプロキシ: ${options.address}:${options.port})`);
  console.log(`MCPサーバーコマンド: ${options.serverCommand} ${options.serverArgs.join(" ")}`);
  
  // プロキシの設定
  const proxy = createProxy({
    address: options.address,
    port: options.port,
    command: options.serverCommand,
    args: options.serverArgs,
    verbose: options.verbose,
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
    
    console.log(`MCPサーバーが起動しました`);
    console.log(`プロキシは ${options.address}:${options.port} でリッスン中です`);
    console.log("Ctrl+Cで停止できます");
    
    // プロセスを実行し続ける
    await new Promise(() => {});
  } catch (error) {
    console.error("予期しないエラーが発生しました:", error);
    Deno.exit(1);
  }
}

// エントリーポイント
if (import.meta.main) {
  main();
}
