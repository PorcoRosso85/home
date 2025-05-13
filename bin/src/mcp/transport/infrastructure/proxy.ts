/**
 * プロキシのコア技術実装
 */

import { RunCommandResult, ProxyStartResult, TransportOptions } from "../domain/types.ts";
import { createServer } from "./server.ts";

/**
 * デフォルトのトランスポート設定
 */
export const DEFAULT_OPTIONS: TransportOptions = {
  address: "0.0.0.0",
  port: 8080,
  command: "",
  args: [],
  verbose: false,
};

/**
 * プロキシインスタンスの型定義
 */
type Proxy = {
  options: TransportOptions;
  sessions: Map<string, Deno.Process>;
  log: (message: string) => void;
};

/**
 * オプションに基づくプロキシインスタンスを生成する
 */
export function createProxy(options?: Partial<TransportOptions>): Proxy {
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options } as TransportOptions;
  
  // コマンドが指定されていない場合はエラーとする
  if (!mergedOptions.command) {
    throw new Error("Command must be specified");
  }
  
  return {
    options: mergedOptions,
    sessions: new Map(),
    log: (message: string) => {
      if (mergedOptions.verbose) {
        console.log(`[MCP Proxy] ${message}`);
      }
    },
  };
}

/**
 * 子プロセスを実行する
 */
export function runCommand(command: string, args: string[]): RunCommandResult {
  try {
    const process = Deno.run({
      cmd: [command, ...args],
      stdin: "piped",
      stdout: "piped",
      stderr: "piped",
    });
    
    return { ok: true, process };
  } catch (error) {
    return {
      ok: false,
      error: {
        code: "COMMAND_EXECUTION_ERROR",
        message: error instanceof Error ? error.message : String(error),
      },
    };
  }
}

/**
 * プロキシを開始する
 */
export async function startProxy(proxy: ReturnType<typeof createProxy>): Promise<ProxyStartResult> {
  proxy.log(`Starting proxy for command: ${proxy.options.command} ${proxy.options.args.join(" ")}`);
  proxy.log(`Listening on ${proxy.options.address}:${proxy.options.port}`);
  
  // HTTPサーバーの起動
  const serverResult = await createServer(proxy.options);
  
  if (!serverResult.ok) {
    return serverResult;
  }
  
  proxy.log("Server started successfully");
  return serverResult;
}

/**
 * 標準入出力を処理する
 */
export function handleSTDIO(process: Deno.Process, onMessage: (data: string) => void) {
  const decoder = new TextDecoder();
  
  // 標準出力の読み取り
  (async () => {
    const stdout = process.stdout;
    if (!stdout) return;
    
    const buffer = new Uint8Array(1024);
    
    while (true) {
      try {
        const bytesRead = await stdout.read(buffer);
        if (bytesRead === null) break;
        
        const text = decoder.decode(buffer.subarray(0, bytesRead));
        onMessage(text);
      } catch (error) {
        console.error("Error reading from stdout:", error);
        break;
      }
    }
  })();
  
  // 標準エラー出力の読み取り（ログ用）
  (async () => {
    const stderr = process.stderr;
    if (!stderr) return;
    
    const buffer = new Uint8Array(1024);
    
    while (true) {
      try {
        const bytesRead = await stderr.read(buffer);
        if (bytesRead === null) break;
        
        const text = decoder.decode(buffer.subarray(0, bytesRead));
        console.error(`[MCP Server stderr] ${text}`);
      } catch (error) {
        console.error("Error reading from stderr:", error);
        break;
      }
    }
  })();
  
  return {
    write: async (data: string) => {
      const encoder = new TextEncoder();
      const stdin = process.stdin;
      if (!stdin) return;
      
      try {
        await stdin.write(encoder.encode(data + "\n"));
      } catch (error) {
        console.error("Error writing to stdin:", error);
      }
    },
    close: () => {
      try {
        process.stdin?.close();
        process.kill("SIGTERM");
        process.close();
      } catch (error) {
        console.error("Error closing process:", error);
      }
    },
  };
}
