// kuzu/terminal/serve/constants.ts

// JSON-RPC 2.0エラーコード
export const RPC_ERRORS = {
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,
  EXECUTION_ERROR: -32000,
};

// HTTPヘッダー
export const JSON_HEADERS = {
  "content-type": "application/json",
  "cache-control": "no-cache",
  "Access-Control-Allow-Origin": "*",
};

export const SSE_HEADERS = {
  "content-type": "text/event-stream",
  "cache-control": "no-cache",
  "connection": "keep-alive",
  "Access-Control-Allow-Origin": "*",
};

// CLIツールのパス
export const CLI_PATH = "/home/nixos/bin/src/kuzu/terminal";

// サポートされているメソッド
export const SUPPORTED_METHODS = ["execute"];
