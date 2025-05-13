/**
 * MCP Transport Proxy
 * 
 * stdio TransportのみをサポートするMCPサーバーをHTTP/SSE Transport経由でアクセス可能にするプロキシ。
 * 
 * 使用例:
 * ```typescript
 * // 直接実行
 * // deno run --allow-net --allow-run mod.ts github-mcp-server stdio
 * 
 * // モジュールとして使用
 * import { createProxy, startProxy } from "./mod.ts";
 * 
 * const proxy = createProxy({
 *   address: "127.0.0.1",
 *   port: 8080,
 *   command: "github-mcp-server",
 *   args: ["stdio"],
 *   verbose: true
 * });
 * 
 * await startProxy(proxy);
 * ```
 */

// 型定義
export type { 
  MCPMessage, 
  MCPMethod, 
  TransportOptions,
  ProxyStartResult,
  CreateServerResult
} from "./domain/types.ts";

// コア機能
export { 
  createProxy, 
  startProxy 
} from "./infrastructure/proxy.ts";

// CLI
export { main } from "./cli.ts";

// スクリプトが直接実行された場合は、mainを実行する
if (import.meta.main) {
  const { main } = await import("./cli.ts");
  main();
}
