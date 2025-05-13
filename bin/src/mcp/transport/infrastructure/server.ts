/**
 * HTTPサーバー実装
 */

import { crypto } from "https://deno.land/std@0.196.0/crypto/mod.ts";
import { CreateServerResult, MCPMessage, Session, TransportOptions } from "../domain/types.ts";
import { runCommand, handleSTDIO } from "./proxy.ts";

// セッション情報を保持するMap
const sessions = new Map<string, Session>();

// MCPサーバープロセスを保持するMap
const processes = new Map<string, {
  process: Deno.Process;
  stdio: ReturnType<typeof handleSTDIO>;
}>();

// SSE接続を保持するMap
const connections = new Map<string, {
  controller: ReadableStreamDefaultController;
  request: Request;
}>();

/**
 * HTTPサーバーを作成する
 */
export async function createServer(options: TransportOptions): Promise<CreateServerResult> {
  try {
    // HTTPサーバーの起動
    const server = Deno.listen({ hostname: options.address, port: options.port });
    
    // HTTPリクエストの処理
    (async () => {
      for await (const conn of server) {
        serveHttp(conn, options).catch((error) => {
          console.error("Error serving HTTP:", error);
        });
      }
    })();
    
    return { ok: true, server };
  } catch (error) {
    return {
      ok: false,
      error: {
        code: "SERVER_CREATION_ERROR",
        message: error instanceof Error ? error.message : String(error),
      },
    };
  }
}

/**
 * HTTP接続を処理する
 */
async function serveHttp(conn: Deno.Conn, options: TransportOptions) {
  const httpConn = Deno.serveHttp(conn);
  
  for await (const requestEvent of httpConn) {
    const request = requestEvent.request;
    const url = new URL(request.url);
    
    try {
      let response: Response;
      
      if (request.method === "GET" && url.pathname === "/sse") {
        response = await handleSSEConnection(request, options);
      } else if (request.method === "POST" && url.pathname === "/messages") {
        response = await handleMessageRequest(request, options);
      } else if (request.method === "GET" && url.pathname === "/healthz") {
        response = new Response("OK", { status: 200 });
      } else {
        response = new Response("Not Found", { status: 404 });
      }
      
      await requestEvent.respondWith(response);
    } catch (error) {
      console.error("Error processing request:", error);
      
      try {
        await requestEvent.respondWith(
          new Response("Internal Server Error", { status: 500 })
        );
      } catch (respondError) {
        console.error("Error sending error response:", respondError);
      }
    }
  }
}

/**
 * SSE接続を処理する
 */
export async function handleSSEConnection(request: Request, options: TransportOptions): Promise<Response> {
  // 簡易的なUUID代替生成（ランダムな文字列）
  const sessionId = crypto.randomUUID();
  
  if (options.verbose) {
    console.log(`[MCP Proxy] New SSE connection: ${sessionId}`);
  }
  
  // MCPサーバーの起動
  console.log(`Starting MCP server: ${options.command} ${options.args.join(" ")}`);
  const commandResult = runCommand(options.command, options.args);
  
  if (!commandResult.ok) {
    console.error(`Failed to start MCP server: ${JSON.stringify(commandResult.error)}`);
    return new Response(JSON.stringify({ error: commandResult.error }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
  
  console.log("MCP server process started successfully");
  const process = commandResult.process;
  
  // 新しいセッションの作成
  const session: Session = {
    id: sessionId,
    requestQueue: [],
    responseQueue: [],
    createdAt: new Date(),
  };
  
  sessions.set(sessionId, session);
  
  // SSEストリームの作成
  const stream = new ReadableStream({
    start(controller) {
      connections.set(sessionId, { controller, request });
      
      // SSEヘッダーの送信
      controller.enqueue(`event: endpoint\ndata: http://${request.headers.get("host")}/messages?sessionId=${sessionId}\n\n`);
      
      // 接続確立メッセージの送信（クライアントがSSEを処理し始めるのを助ける）
      controller.enqueue(`event: connected\ndata: {"sessionId":"${sessionId}"}\n\n`);
      
      // 定期的なキープアライブメッセージを送信
      const keepAliveInterval = setInterval(() => {
        try {
          controller.enqueue(`: keep-alive ${new Date().toISOString()}\n\n`);
        } catch (error) {
          console.error(`Error sending keep-alive: ${error}`);
          clearInterval(keepAliveInterval);
        }
      }, 30000); // 30秒ごと
      
      // 標準入出力の処理
      const stdio = handleSTDIO(process, (data) => {
        try {
          // JSONとして解析できない場合もあるので、行ごとに処理
          const lines = data.split("\n").filter(line => line.trim() !== "");
          
          for (const line of lines) {
            try {
              // JSONとして解析
              const message = JSON.parse(line) as MCPMessage;
              session.responseQueue.push(message);
              controller.enqueue(`event: message\ndata: ${line}\n\n`);
              
              if (options.verbose) {
                console.log(`[MCP Proxy] Server -> Client (${sessionId}): ${message.method || "response"}`);
              }
            } catch (jsonError) {
              // JSON以外のデータの場合はデバッグ情報として送信
              console.log(`[MCP Server non-JSON output]: ${line}`);
              controller.enqueue(`event: log\ndata: ${JSON.stringify({message: line})}\n\n`);
            }
          }
        } catch (error) {
          console.error("Error processing server message:", error, "Data:", data);
        }
      });
      
      processes.set(sessionId, { process, stdio });
      
      // リクエストが中断された時の処理
      request.signal.addEventListener("abort", () => {
        cleanup(sessionId);
      });
    },
    cancel() {
      cleanup(sessionId);
    },
  });
  
  // レスポンスの作成
  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  });
}

/**
 * メッセージリクエストを処理する
 */
export async function handleMessageRequest(request: Request, options: TransportOptions): Promise<Response> {
  const url = new URL(request.url);
  const sessionId = url.searchParams.get("sessionId");
  
  if (!sessionId) {
    return new Response(JSON.stringify({ error: "Session ID is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }
  
  const processInfo = processes.get(sessionId);
  
  if (!processInfo) {
    return new Response(JSON.stringify({ error: "Session not found" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  }
  
  try {
    const data = await request.json();
    const message = data as MCPMessage;
    
    if (options.verbose) {
      console.log(`[MCP Proxy] Client -> Server (${sessionId}): ${message.method}`);
    }
    
    // メッセージをサーバーに送信
    await processInfo.stdio.write(JSON.stringify(message));
    
    return new Response(JSON.stringify({ status: "accepted" }), {
      status: 202,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: {
          code: "MESSAGE_PROCESSING_ERROR",
          message: error instanceof Error ? error.message : String(error),
        },
      }),
      {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}

/**
 * セッションをクリーンアップする
 */
function cleanup(sessionId: string) {
  const processInfo = processes.get(sessionId);
  if (processInfo) {
    processInfo.stdio.close();
    processes.delete(sessionId);
  }
  
  connections.delete(sessionId);
  sessions.delete(sessionId);
}
