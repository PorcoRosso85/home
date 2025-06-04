// コマンド実行のビジネスロジック

import type {
  CommandParams,
  CommandExecutionResult,
  StreamMessage,
  ProcessRunner,
} from "./types.ts";
import { executeTmuxCommand } from "../../infrastructure/process/tmuxCommandRunner.ts";
import type { TmuxSessionParams } from "./tmuxTypes.ts";

// パラメータのバリデーション
function validateParams(params: CommandParams): {
  isValid: boolean;
  error?: string;
} {
  if (!params.command || params.command.trim() === "") {
    return {
      isValid: false,
      error: "Command is required",
    };
  }

  return { isValid: true };
}

// 高階関数によるコマンド実行器の作成
export function createCommandExecutor(deps: { processRunner: ProcessRunner }) {
  return async function executeCommand(
    params: CommandParams
  ): Promise<CommandExecutionResult> {
    // パラメータのバリデーション
    const validation = validateParams(params);
    if (!validation.isValid) {
      return {
        status: "error",
        errorCode: "INVALID_PARAMS",
        message: validation.error || "Invalid parameters",
      };
    }

    // デフォルト値の設定
    const args = params.args || [];
    const cwd = params.cwd || ".";

    // プロセスのスポーン
    const spawnResult = deps.processRunner.spawn(params.command, args, cwd);
    
    switch (spawnResult.status) {
      case "error":
        return {
          status: "error",
          errorCode: "EXECUTION_FAILED",
          message: spawnResult.message,
          details: { code: spawnResult.errorCode },
        };
      case "success": {
        const decoder = deps.processRunner.createDecoder();
        const stdout: string[] = [];
        
        // ストリームの読み取り
        while (true) {
          const readResult = await deps.processRunner.readStream(
            spawnResult.reader,
            decoder
          );
          
          switch (readResult.status) {
            case "error":
              return {
                status: "error",
                errorCode: "STREAM_ERROR",
                message: readResult.message,
                details: { code: readResult.errorCode },
              };
            case "success":
              if (readResult.chunk) {
                stdout.push(readResult.chunk);
              }
              if (readResult.done) {
                // プロセスの終了を待つ
                const waitResult = await deps.processRunner.waitProcess(
                  spawnResult.process
                );
                
                switch (waitResult.status) {
                  case "error":
                    return {
                      status: "error",
                      errorCode: "EXECUTION_FAILED",
                      message: waitResult.message,
                    };
                  case "success":
                    return {
                      status: "success",
                      code: waitResult.code,
                      stdout,
                    };
                }
              }
          }
        }
      }
    }
  };
}

// ストリーミング対応のコマンド実行器
export function createStreamingCommandExecutor(deps: { processRunner: ProcessRunner }) {
  return async function* executeCommandStreaming(
    params: CommandParams
  ): AsyncGenerator<StreamMessage> {
    // tmuxコマンドの特別処理
    if (params.command === "tmux" && params.args?.[0] === "new-session") {
      // tmuxセッション作成の場合
      const sessionIndex = params.args.indexOf("-s");
      if (sessionIndex !== -1 && params.args[sessionIndex + 1]) {
        const sessionName = params.args[sessionIndex + 1];
        
        // claude-codeコマンドを抽出
        const commandStartIndex = params.args.indexOf("pnpm");
        if (commandStartIndex !== -1) {
          const tmuxParams: TmuxSessionParams = {
            sessionName,
            command: params.args[commandStartIndex],
            args: params.args.slice(commandStartIndex + 1),
          };
          
          yield* executeTmuxCommand(tmuxParams);
          return;
        }
      }
    }
    
    // パラメータのバリデーション
    const validation = validateParams(params);
    if (!validation.isValid) {
      yield {
        type: "error",
        errorCode: "INVALID_PARAMS",
        message: validation.error || "Invalid parameters",
      };
      return;
    }

    // デフォルト値の設定
    const args = params.args || [];
    const cwd = params.cwd || ".";

    // プロセスのスポーン
    const spawnResult = deps.processRunner.spawn(params.command, args, cwd);
    
    switch (spawnResult.status) {
      case "error":
        yield {
          type: "error",
          errorCode: spawnResult.errorCode,
          message: spawnResult.message,
        };
        return;
      case "success": {
        const decoder = deps.processRunner.createDecoder();
        
        // ストリームの読み取り
        while (true) {
          const readResult = await deps.processRunner.readStream(
            spawnResult.reader,
            decoder
          );
          
          switch (readResult.status) {
            case "error":
              yield {
                type: "error",
                errorCode: readResult.errorCode,
                message: readResult.message,
              };
              return;
            case "success":
              if (readResult.chunk) {
                yield {
                  type: "chunk",
                  data: readResult.chunk,
                };
              }
              if (readResult.done) {
                // プロセスの終了を待つ
                const waitResult = await deps.processRunner.waitProcess(
                  spawnResult.process
                );
                
                switch (waitResult.status) {
                  case "error":
                    yield {
                      type: "error",
                      errorCode: waitResult.errorCode,
                      message: waitResult.message,
                    };
                    return;
                  case "success":
                    yield {
                      type: "complete",
                      code: waitResult.code,
                    };
                    return;
                }
              }
          }
        }
      }
    }
  };
}
