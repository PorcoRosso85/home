// プロセス管理ハンドラー

import type {
  JsonRpcRequest,
  JsonRpcResponse,
  ExecParams,
  ExecStreamResult,
} from "../types.ts";
import type { StreamMessage } from "../../domain/command/types.ts";
import type { ProcessStartParams } from "../../domain/process/types.ts";
import * as logger from "../../../kuzu/common/infrastructure/logger.ts";

// claude-codeコマンドかどうかを判定
function isClaudeCodeCommand(params: ExecParams): boolean {
  return params.command === "pnpm" && 
         params.args?.includes("dlx") && 
         params.args?.includes("@anthropic-ai/claude-code");
}

// セッションIDを生成
function generateSessionId(): string {
  return `claude-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

// プロセス管理ハンドラーを作成する高階関数
export function createProcessHandler(deps: {
  processManager: {
    spawn: (params: ProcessStartParams) => AsyncGenerator<StreamMessage>;
    list: () => any[];
    kill: (id: string) => Promise<any>;
  };
  commandExecutor: (params: ExecParams) => AsyncGenerator<StreamMessage>;
  messageSender: (message: JsonRpcResponse) => void;
}) {
  return async function handleProcess(request: JsonRpcRequest): Promise<void> {
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
    
    // 実行するジェネレーターを選択
    let messageGenerator: AsyncGenerator<StreamMessage>;
    let accumulatedData = "";
    const isClaude = isClaudeCodeCommand(params);
    
    if (isClaude) {
      // claude-codeの場合はプロセスマネージャーを使用
      const sessionId = generateSessionId();
      const processParams: ProcessStartParams = {
        id: sessionId,
        command: params.command,
        args: params.args || [],
      };
      
      logger.info('[processHandler] Detected claude-code command', {
        sessionId,
        command: params.command,
        args: params.args,
        prompt: params.args?.slice(params.args.indexOf("-p") + 1).join(" ")
      });
      
      messageGenerator = deps.processManager.spawn(processParams);
    } else {
      // その他のコマンドは通常実行
      logger.info('[processHandler] Regular command execution', {
        command: params.command,
        args: params.args
      });
      
      messageGenerator = deps.commandExecutor(params);
    }
    
    // ストリーミング処理
    for await (const message of messageGenerator) {
      switch (message.type) {
        case "chunk": {
          // サーバー側ログ: ストリーミングデータ
          logger.debug('[processHandler] Streaming chunk', {
            dataLength: message.data.length,
            dataPreview: message.data.substring(0, 100),
            isClaude: isClaude
          });
          
          // claude-codeの場合はデータを蓄積
          if (isClaude) {
            accumulatedData += message.data;
          }
          
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
          // サーバー側ログ: 完了
          logger.info('[processHandler] Process completed', {
            code: message.code,
            isClaude: isClaude
          });
          
          // claude-codeの場合は実行結果を解析してログ出力
          if (isClaude && accumulatedData) {
            try {
              const parsedData = JSON.parse(accumulatedData);
              logger.info('[processHandler] Claude-code実行結果', {
                type: parsedData.type,
                subtype: parsedData.subtype,
                isError: parsedData.is_error,
                resultPreview: parsedData.result?.substring(0, 200) + '...',
                cost: parsedData.cost_usd,
                duration: parsedData.duration_ms,
                outputLength: accumulatedData.length
              });
            } catch {
              logger.info('[processHandler] Claude-code出力（非JSON）', {
                dataPreview: accumulatedData.substring(0, 200) + '...',
                outputLength: accumulatedData.length
              });
            }
          }
          
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
          logger.error('[processHandler] Process error', {
            errorCode: message.errorCode,
            message: message.message,
            isClaude: isClaude
          });
          
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

// パラメータのパース（既存の関数を再利用）
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
