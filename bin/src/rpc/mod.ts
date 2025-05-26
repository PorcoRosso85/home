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

async function handleJsonRpc(request: JsonRpcRequest): Promise<JsonRpcResponse> {
  if (request.method === "ls") {
    try {
      const cmd = new Deno.Command("ls", {
        args: request.params?.args || [],
        cwd: request.params?.cwd || ".",
      });
      
      const { stdout, stderr } = await cmd.output();
      const output = new TextDecoder().decode(stdout);
      const error = new TextDecoder().decode(stderr);
      
      return {
        jsonrpc: "2.0",
        result: {
          stdout: output,
          stderr: error,
        },
        id: request.id,
      };
    } catch (error) {
      return {
        jsonrpc: "2.0",
        error: {
          code: -32603,
          message: "Internal error",
          data: error.message,
        },
        id: request.id,
      };
    }
  }
  
  return {
    jsonrpc: "2.0",
    error: {
      code: -32601,
      message: "Method not found",
    },
    id: request.id,
  };
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
      const response = await handleJsonRpc(request);
      socket.send(JSON.stringify(response));
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
