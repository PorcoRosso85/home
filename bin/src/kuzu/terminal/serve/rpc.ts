// kuzu/terminal/serve/rpc.ts

import { RPCRequest } from "./types.ts";
import { 
  createSuccessResponse, 
  createErrorResponse,
  createStreamEvent 
} from "./response.ts";
import { executeCommand } from "./executor.ts";
import { 
  RPC_ERRORS, 
  SSE_HEADERS,
  SUPPORTED_METHODS 
} from "./constants.ts";

/**
 * JSON-RPC 2.0リクエストを処理する
 * @param request JSON-RPC 2.0リクエスト
 * @returns HTTPレスポンス
 */
export async function executeRpc(request: RPCRequest): Promise<Response> {
  // JSON-RPC 2.0形式のバリデーション
  if (request.jsonrpc !== "2.0") {
    return new Response(
      JSON.stringify(createErrorResponse(request.id, RPC_ERRORS.INVALID_REQUEST, "Invalid JSON-RPC 2.0 request")),
      { headers: { "content-type": "application/json" }, status: 400 }
    );
  }

  // メソッドのバリデーション
  if (!request.method || !SUPPORTED_METHODS.includes(request.method)) {
    return new Response(
      JSON.stringify(createErrorResponse(request.id, RPC_ERRORS.METHOD_NOT_FOUND, "Method not found")),
      { headers: { "content-type": "application/json" }, status: 400 }
    );
  }

  // executeメソッドの処理
  if (request.method === "execute") {
    return await handleExecute(request);
  }

  // この行に到達することはないはずだが、念のため
  return new Response(
    JSON.stringify(createErrorResponse(request.id, RPC_ERRORS.INTERNAL_ERROR, "Internal server error")),
    { headers: { "content-type": "application/json" }, status: 500 }
  );
}

/**
 * executeメソッドを処理する
 * @param request JSON-RPC 2.0リクエスト
 * @returns ストリーミングHTTPレスポンス
 */
async function handleExecute(request: RPCRequest): Promise<Response> {
  const params = request.params;
  
  // パラメータのバリデーション
  if (!params || !params.command) {
    return new Response(
      JSON.stringify(createErrorResponse(request.id, RPC_ERRORS.INVALID_PARAMS, "Invalid params: command is required")),
      { headers: { "content-type": "application/json" }, status: 400 }
    );
  }

  const { command, args = [], stdin = "" } = params;
  
  try {
    // コマンドを実行
    const { stdout, stderr, process } = await executeCommand(command, args, stdin);
    
    // Server-Sent Eventsのストリームを作成
    const stream = new TransformStream();
    const writer = stream.writable.getWriter();
    
    // プロセスの終了を監視するためのPromise
    const processExit = new Promise<number>((resolve) => {
      process.status().then(status => resolve(status.code));
    });
    
    // stdout処理
    processStreamData(stdout, "stdout", request.id as string | number, writer);
    
    // stderr処理
    processStreamData(stderr, "stderr", request.id as string | number, writer);

    // プロセスが終了したら完了メッセージを送信してストリームを閉じる
    processExit.then(async (exitCode) => {
      const completionMessage = createSuccessResponse(request.id, {
        status: "completed",
        exitCode,
      });
      
      await writer.write(new TextEncoder().encode(`data: ${JSON.stringify(completionMessage)}\n\n`));
      await writer.close();
    });
    
    return new Response(stream.readable, { headers: SSE_HEADERS });
  } catch (error) {
    return new Response(
      JSON.stringify(createErrorResponse(
        request.id, 
        RPC_ERRORS.EXECUTION_ERROR, 
        "Execution error", 
        error.message
      )),
      { headers: { "content-type": "application/json" }, status: 500 }
    );
  }
}

/**
 * ストリームデータを処理して書き込む
 * @param stream データのReadableStream
 * @param type ストリームタイプ（"stdout" or "stderr"）
 * @param id リクエストID
 * @param writer ターゲットのWritableStreamWriter
 */
async function processStreamData(
  stream: ReadableStream<Uint8Array>,
  type: "stdout" | "stderr",
  id: string | number,
  writer: WritableStreamDefaultWriter<Uint8Array>
) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      if (value) {
        const data = decoder.decode(value);
        const event = createStreamEvent(id, type, data);
        await writer.write(new TextEncoder().encode(event));
      }
    }
  } catch (error) {
    console.error(`Error processing ${type} stream:`, error);
  } finally {
    reader.releaseLock();
  }
}
