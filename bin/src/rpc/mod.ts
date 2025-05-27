import { serve } from "https://deno.land/std@0.220.0/http/server.ts";

interface JsonRpcRequest {
  jsonrpc: "2.0";
  method: string;
  params?: any;
  id: number | string;
}

interface JsonRpcResponse {
  jsonrpc: "2.0";
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
  id: number | string;
}

async function handleJsonRpc(socket: WebSocket, request: JsonRpcRequest): Promise<void> {
  if (request.method === "exec") {
    try {
      const { command, args = [], cwd = "." } = request.params || {};
      
      const cmd = new Deno.Command(command, {
        args,
        cwd,
        stdout: "piped",
        stderr: "piped",
      });
      
      const process = cmd.spawn();
      
      // stdoutのストリーミング
      const reader = process.stdout.getReader();
      const decoder = new TextDecoder();
      
      (async () => {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            socket.send(JSON.stringify({
              jsonrpc: "2.0",
              result: {
                stdout: chunk,
                stream: true,
              },
              id: request.id,
            }));
          }
        } catch (error) {
          console.error("Error reading stdout:", error);
        }
      })();
      
      // プロセス終了を待つ
      const { code } = await process.status;
      
      // 最終的な完了通知
      socket.send(JSON.stringify({
        jsonrpc: "2.0",
        result: {
          code,
          stream: false,
          complete: true,
        },
        id: request.id,
      }));
      
    } catch (error) {
      socket.send(JSON.stringify({
        jsonrpc: "2.0",
        error: {
          code: -32603,
          message: "Internal error",
          data: error.message,
        },
        id: request.id,
      }));
    }
  } else {
    socket.send(JSON.stringify({
      jsonrpc: "2.0",
      error: {
        code: -32601,
        message: "Method not found",
      },
      id: request.id,
    }));
  }
}

serve((req) => {
  if (req.headers.get("upgrade") !== "websocket") {
    return new Response("WebSocket endpoint", { status: 400 });
  }

  const { socket, response } = Deno.upgradeWebSocket(req);
  
  socket.onopen = () => {
    console.log("WebSocket connection opened");
  };
  
  socket.onmessage = async (event) => {
    try {
      const request: JsonRpcRequest = JSON.parse(event.data);
      await handleJsonRpc(socket, request);
    } catch (error) {
      socket.send(JSON.stringify({
        jsonrpc: "2.0",
        error: {
          code: -32700,
          message: "Parse error",
        },
        id: null,
      }));
    }
  };
  
  socket.onclose = () => {
    console.log("WebSocket connection closed");
  };
  
  return response;
}, { port: 8080 });

console.log("JSON-RPC WebSocket server running on ws://localhost:8080");
