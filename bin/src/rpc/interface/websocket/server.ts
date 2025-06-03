// WebSocketサーバーの実装

import { serve } from "https://deno.land/std@0.220.0/http/server.ts";
import type {
  WebSocketConnection,
  ConnectionResult,
  MessageParseResult,
  ServerConfig,
} from "./types.ts";
import type { JsonRpcRequest, JsonRpcResponse } from "../../application/types.ts";

// WebSocket接続のアップグレード
export function upgradeConnection(request: Request): ConnectionResult & { response?: Response } {
  if (request.headers.get("upgrade") !== "websocket") {
    return {
      status: "error",
      errorCode: "UPGRADE_FAILED",
      message: "Not a WebSocket request",
    };
  }

  const { socket, response } = Deno.upgradeWebSocket(request);
  
  return {
    status: "success",
    connection: {
      socket,
      send: (message: unknown) => {
        socket.send(JSON.stringify(message));
      },
      close: () => {
        socket.close();
      },
    },
    response, // upgradeWebSocketから返されたresponseを含める
  };
}

// メッセージのパース
export function parseMessage(data: string): MessageParseResult {
  let parsed: unknown;
  
  // JSON パース
  const jsonResult = parseJson(data);
  if (jsonResult.status === "error") {
    return {
      status: "error",
      errorCode: "PARSE_ERROR",
      message: "Invalid JSON",
    };
  }
  
  parsed = jsonResult.data;
  
  // JSON-RPC リクエストの検証
  if (!isValidJsonRpcRequest(parsed)) {
    return {
      status: "error",
      errorCode: "INVALID_FORMAT",
      message: "Invalid JSON-RPC request format",
    };
  }
  
  return {
    status: "success",
    request: parsed,
  };
}

// JSON パース関数
function parseJson(data: string): { status: "success"; data: unknown } | { status: "error" } {
  let parsed: unknown;
  parsed = JSON.parse(data);
  return { status: "success", data: parsed };
}

// JSON-RPC リクエストの検証
function isValidJsonRpcRequest(obj: unknown): obj is JsonRpcRequest {
  if (!obj || typeof obj !== "object") {
    return false;
  }
  
  const req = obj as Record<string, unknown>;
  
  return (
    req.jsonrpc === "2.0" &&
    typeof req.method === "string" &&
    (typeof req.id === "number" || typeof req.id === "string")
  );
}

// 高階関数によるWebSocketハンドラーの作成
export function createWebSocketHandler(deps: {
  methodHandler: (request: JsonRpcRequest) => Promise<void>;
}) {
  return function handleWebSocket(connection: WebSocketConnection): void {
    connection.socket.onopen = () => {
      console.log("WebSocket connection opened");
    };
    
    connection.socket.onmessage = async (event) => {
      const parseResult = parseMessage(event.data);
      
      switch (parseResult.status) {
        case "error":
          connection.send({
            jsonrpc: "2.0",
            error: {
              code: -32700,
              message: "Parse error",
            },
            id: null,
          } as JsonRpcResponse);
          break;
          
        case "success":
          await deps.methodHandler(parseResult.request as JsonRpcRequest);
          break;
      }
    };
    
    connection.socket.onclose = () => {
      console.log("WebSocket connection closed");
    };
    
    connection.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  };
}

// 高階関数によるHTTPハンドラーの作成
export function createHttpHandler(deps: {
  websocketHandler: (connection: WebSocketConnection) => void;
}) {
  return function handleHttp(request: Request): Response {
    const upgradeResult = upgradeConnection(request);
    
    switch (upgradeResult.status) {
      case "error":
        return new Response(upgradeResult.message, { status: 400 });
        
      case "success":
        deps.websocketHandler(upgradeResult.connection);
        return upgradeResult.response!; // upgradeWebSocketから返されたresponseを返す
    }
  };
}

// サーバーの起動
export async function startServer(
  config: ServerConfig,
  handler: (request: Request) => Response
): Promise<void> {
  const hostname = config.hostname || "localhost";
  const url = `ws://${hostname}:${config.port}`;
  
  console.log(`JSON-RPC WebSocket server running on ${url}`);
  
  await serve(handler, {
    port: config.port,
    hostname: config.hostname,
  });
}
