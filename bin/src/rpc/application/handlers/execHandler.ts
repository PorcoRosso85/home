// execコマンドのハンドラー

import type {
  JsonRpcRequest,
  JsonRpcResponse,
  ExecParams,
  ExecStreamResult,
  HandlerDependencies,
} from "../types.ts";
import type { StreamMessage } from "../../domain/command/types.ts";

// パラメータのバリデーションと型変換
function parseExecParams(params: unknown): ExecParams | null {
  if (!params || typeof params !== "object") {
    return null;
  }
  
  const p = params as Record<string, unknown>;
  
  if (typeof p.command !== "string") {
    return null;
  }
  
  return {
    command: p.command,
    args: Array.isArray(p.args) ? p.args.filter((arg): arg is string => typeof arg === "string") : undefined,
    cwd: typeof p.cwd === "string" ? p.cwd : undefined,
  };
}

// 高階関数によるexecハンドラーの作成
export function createExecHandler(deps: HandlerDependencies) {
  return async function handleExec(request: JsonRpcRequest): Promise<void> {
    // パラメータのパース
    const params = parseExecParams(request.params);
    
    if (!params) {
      deps.messageSender({
        jsonrpc: "2.0",
        error: {
          code: -32602,
          message: "Invalid params",
          data: "Expected object with 'command' property",
        },
        id: request.id,
      });
      return;
    }
    
    // ストリーミング実行
    const messageGenerator = deps.commandExecutor(params) as AsyncGenerator<StreamMessage>;
    
    for await (const message of messageGenerator) {
      switch (message.type) {
        case "chunk": {
          const response: JsonRpcResponse = {
            jsonrpc: "2.0",
            result: {
              stdout: message.data,
              stream: true,
            } as ExecStreamResult,
            id: request.id,
          };
          deps.messageSender(response);
          break;
        }
        
        case "complete": {
          const response: JsonRpcResponse = {
            jsonrpc: "2.0",
            result: {
              code: message.code,
              stream: false,
              complete: true,
            } as ExecStreamResult,
            id: request.id,
          };
          deps.messageSender(response);
          break;
        }
        
        case "error": {
          const response: JsonRpcResponse = {
            jsonrpc: "2.0",
            error: {
              code: -32603,
              message: "Internal error",
              data: {
                errorCode: message.errorCode,
                message: message.message,
              },
            },
            id: request.id,
          };
          deps.messageSender(response);
          break;
        }
      }
    }
  };
}

// メソッドに対応するハンドラーを返す高階関数
export function createMethodHandler(deps: HandlerDependencies) {
  const execHandler = createExecHandler(deps);
  
  return async function handleMethod(request: JsonRpcRequest): Promise<void> {
    switch (request.method) {
      case "exec":
        await execHandler(request);
        break;
        
      default:
        deps.messageSender({
          jsonrpc: "2.0",
          error: {
            code: -32601,
            message: "Method not found",
          },
          id: request.id,
        });
    }
  };
}
