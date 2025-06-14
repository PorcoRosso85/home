/**
 * MCP関連のドメインモデルと型定義
 */

/**
 * MCP関連メソッド名の型定義
 */
export type MCPMethod =
  | "notifications/cancelled"
  | "initialize"
  | "notifications/initialized"
  | "ping"
  | "notifications/progress"
  | "resources/list"
  | "resources/templates/list"
  | "resources/read"
  | "notifications/resource/list/changed"
  | "resources/subscribe"
  | "resources/unsubscribe"
  | "notifications/resource/updated"
  | "prompts/list"
  | "prompts/get"
  | "notifications/prompt/list/changed"
  | "tools/list"
  | "tools/call"
  | "notifications/tool/list/changed";

/**
 * MCPメッセージの型定義
 */
export type MCPMessage = {
  jsonrpc: string;
  method: MCPMethod;
  id?: string | number;
  params?: Record<string, unknown>;
  result?: unknown;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
};

/**
 * トランスポート設定オプションの型定義
 */
export type TransportOptions = {
  address: string;
  port: number;
  command: string;
  args: string[];
  verbose: boolean;
};

/**
 * コマンド実行結果の型定義
 */
export type RunCommandResult =
  | { ok: true; process: Deno.Process }
  | { ok: false; error: { code: string; message: string } };

/**
 * プロキシ起動結果の型定義
 */
export type ProxyStartResult =
  | { ok: true; server: Deno.Listener }
  | { ok: false; error: { code: string; message: string } };

/**
 * HTTPサーバー作成結果の型定義
 */
export type CreateServerResult =
  | { ok: true; server: Deno.Listener }
  | { ok: false; error: { code: string; message: string } };

/**
 * 引数解析結果の型定義
 */
export type ParseArgsResult =
  | { ok: true; options: TransportOptions }
  | { ok: false; error: { code: string; message: string } };

/**
 * セッション情報の型定義
 */
export type Session = {
  id: string;
  requestQueue: Array<MCPMessage>;
  responseQueue: Array<MCPMessage>;
  createdAt: Date;
};
