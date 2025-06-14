// Denoによるプロセス管理実装

import type { StreamMessage } from "../command/types.ts";
import type { 
  ProcessId, 
  ProcessInfo, 
  ProcessStartParams, 
  ProcessStore,
  ProcessManagerConfig,
  ProcessKillResult
} from "./types.ts";
import * as logger from "../../../kuzu/common/infrastructure/logger.ts";

// プロセスマネージャーを作成する高階関数
export function createProcessManager(config: ProcessManagerConfig) {
  const processes: ProcessStore = new Map();
  const queue: Array<() => Promise<void>> = [];
  let runningCount = 0;

  // プロセスを生成してストリーミング
  async function* spawn(params: ProcessStartParams): AsyncGenerator<StreamMessage> {
    const { id, command, args } = params;
    
    logger.info('[processManager] Starting process', {
      id,
      command,
      args,
      runningCount,
      maxConcurrent: config.maxConcurrent
    });
    
    // 並列数チェック
    if (runningCount >= config.maxConcurrent) {
      // キューに追加して待機
      yield {
        type: "chunk",
        data: `Process queued. ${queue.length + 1} processes waiting.`
      };
      
      await new Promise<void>((resolve) => {
        queue.push(resolve);
      });
    }
    
    runningCount++;
    
    try {
      // プロセスを生成
      const cmd = new Deno.Command(command, {
        args,
        stdout: "piped",
        stderr: "piped",
      });
      
      const process = cmd.spawn();
      const decoder = new TextDecoder();
      
      // プロセス情報を保存
      const info: ProcessInfo = {
        id,
        command,
        args,
        startTime: new Date().toISOString(),
        status: "running",
      };
      
      processes.set(id, {
        info,
        process,
        output: [],
      });
      
      // 標準出力をストリーミング
      const reader = process.stdout.getReader();
      
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const processData = processes.get(id);
          if (processData) {
            processData.output.push(chunk);
          }
          
          logger.debug(`[processManager] Output from ${id}`, {
            chunkLength: chunk.length,
            chunkPreview: chunk.substring(0, 200)
          });
          
          yield {
            type: "chunk",
            data: chunk,
          };
        }
        
        // プロセスの終了を待つ
        const { code, success } = await process.status;
        
        logger.info(`[processManager] Process ${id} completed`, {
          code,
          success,
          outputCount: processes.get(id)?.output.length || 0
        });
        
        // ステータスを更新
        const processData = processes.get(id);
        if (processData) {
          processData.info.status = success ? "completed" : "error";
        }
        
        yield {
          type: "complete",
          code,
        };
        
      } catch (error) {
        // エラー時の処理
        const processData = processes.get(id);
        if (processData) {
          processData.info.status = "error";
        }
        
        yield {
          type: "error",
          errorCode: "EXECUTION_ERROR",
          message: error instanceof Error ? error.message : "Unknown error",
        };
      }
      
    } finally {
      // クリーンアップ
      processes.delete(id);
      runningCount--;
      
      // 待機中のタスクを開始
      if (queue.length > 0) {
        const next = queue.shift();
        if (next) next();
      }
    }
  }
  
  // アクティブなプロセス一覧を取得
  function list(): ProcessInfo[] {
    return Array.from(processes.values()).map(p => p.info);
  }
  
  // プロセスを終了
  async function kill(id: ProcessId): Promise<ProcessKillResult> {
    const processData = processes.get(id);
    if (!processData) {
      return {
        status: "error",
        errorCode: "NOT_FOUND",
        message: `Process ${id} not found`,
      };
    }
    
    try {
      processData.process.kill();
      processes.delete(id);
      runningCount--;
      
      // 待機中のタスクを開始
      if (queue.length > 0) {
        const next = queue.shift();
        if (next) next();
      }
      
      return { status: "success" };
    } catch (error) {
      return {
        status: "error",
        errorCode: "KILL_FAILED",
        message: error instanceof Error ? error.message : "Failed to kill process",
      };
    }
  }
  
  // プロセスの出力を取得
  function getOutput(id: ProcessId): string[] | undefined {
    const processData = processes.get(id);
    return processData?.output;
  }
  
  return {
    spawn,
    list,
    kill,
    getOutput,
  };
}
