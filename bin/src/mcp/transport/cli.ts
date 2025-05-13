/**
 * コマンドラインインターフェース
 */

import { ParseArgsResult, TransportOptions } from "../domain/types.ts";
import { createProxy, DEFAULT_OPTIONS, startProxy } from "../infrastructure/proxy.ts";

/**
 * コマンドライン引数を解析する
 */
export function parseArgs(args: string[]): ParseArgsResult {
  const options: Partial<TransportOptions> = { ...DEFAULT_OPTIONS };
  
  let i = 0;
  while (i < args.length) {
    const arg = args[i];
    
    if (arg === "--address" || arg === "-a") {
      if (i + 1 >= args.length) {
        return {
          ok: false,
          error: {
            code: "INVALID_ARGUMENTS",
            message: `Missing value for ${arg}`,
          },
        };
      }
      options.address = args[++i];
    } else if (arg === "--port" || arg === "-p") {
      if (i + 1 >= args.length) {
        return {
          ok: false,
          error: {
            code: "INVALID_ARGUMENTS",
            message: `Missing value for ${arg}`,
          },
        };
      }
      
      const port = parseInt(args[++i], 10);
      if (isNaN(port) || port < 1 || port > 65535) {
        return {
          ok: false,
          error: {
            code: "INVALID_ARGUMENTS",
            message: "Port must be a number between 1 and 65535",
          },
        };
      }
      
      options.port = port;
    } else if (arg === "--verbose" || arg === "-v") {
      options.verbose = true;
    } else if (arg === "--help" || arg === "-h") {
      showHelp();
      Deno.exit(0);
    } else if (arg.startsWith("-")) {
      return {
        ok: false,
        error: {
          code: "INVALID_ARGUMENTS",
          message: `Unknown option: ${arg}`,
        },
      };
    } else {
      // コマンドとその引数
      options.command = arg;
      options.args = args.slice(i + 1);
      break;
    }
    
    i++;
  }
  
  if (!options.command) {
    return {
      ok: false,
      error: {
        code: "INVALID_ARGUMENTS",
        message: "Command is required",
      },
    };
  }
  
  return {
    ok: true,
    options: options as TransportOptions,
  };
}

/**
 * ヘルプメッセージを表示する
 */
function showHelp() {
  console.log("MCP Transport Proxy");
  console.log("");
  console.log("Usage: mcp-transport-proxy [options] <command> [args...]");
  console.log("");
  console.log("Options:");
  console.log("  --address, -a <address>  The address to listen on (default: 0.0.0.0)");
  console.log("  --port, -p <port>        The port to listen on (default: 8080)");
  console.log("  --verbose, -v            Enable verbose logging");
  console.log("  --help, -h               Show this help message");
  console.log("");
  console.log("Examples:");
  console.log("  mcp-transport-proxy github-mcp-server stdio");
  console.log("  mcp-transport-proxy --port 3000 /path/to/mcp-server arg1 arg2");
}

/**
 * CLIのエントリーポイント
 */
export async function main() {
  // シグナルハンドリングの設定
  const cleanup = () => {
    console.log("\nShutting down...");
    Deno.exit(0);
  };
  
  Deno.addSignalListener("SIGINT", cleanup);
  Deno.addSignalListener("SIGTERM", cleanup);
  
  // 引数の解析
  const result = parseArgs(Deno.args);
  
  if (!result.ok) {
    console.error(`Error: ${result.error.message}`);
    showHelp();
    Deno.exit(1);
  }
  
  try {
    // プロキシの起動
    const proxy = createProxy(result.options);
    const startResult = await startProxy(proxy);
    
    if (!startResult.ok) {
      console.error(`Error starting proxy: ${startResult.error.message}`);
      Deno.exit(1);
    }
    
    console.log(`MCP Transport Proxy listening on ${result.options.address}:${result.options.port}`);
    console.log("Press Ctrl+C to stop");
    
    // プロセスを実行し続ける
    await new Promise(() => {});
  } catch (error) {
    console.error("Unexpected error:", error);
    Deno.exit(1);
  }
}

// スクリプトが直接実行された場合は、mainを実行する
if (import.meta.main) {
  main();
}
