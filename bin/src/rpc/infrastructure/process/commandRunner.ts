// プロセス実行の実装

import type {
  ProcessSpawnResult,
  StreamReadResult,
  ProcessWaitResult,
} from "./types.ts";

// プロセスをスポーンする関数
export function spawnProcess(
  command: string,
  args: string[],
  cwd: string
): ProcessSpawnResult {
  const cmd = new Deno.Command(command, {
    args,
    cwd,
    stdout: "piped",
    stderr: "piped",
  });

  const process = cmd.spawn();
  
  if (!process.stdout) {
    return {
      status: "error",
      errorCode: "SPAWN_ERROR",
      message: "Failed to create process stdout stream",
    };
  }

  const reader = process.stdout.getReader();
  
  return {
    status: "success",
    process,
    reader,
  };
}

// ストリームから読み取る関数
export async function readFromStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  decoder: TextDecoder
): Promise<StreamReadResult> {
  const { done, value } = await reader.read();
  
  if (done) {
    return {
      status: "success",
      chunk: "",
      done: true,
    };
  }

  if (!value) {
    return {
      status: "error",
      errorCode: "READ_ERROR",
      message: "No data received from stream",
    };
  }

  const chunk = decoder.decode(value, { stream: true });
  
  return {
    status: "success",
    chunk,
    done: false,
  };
}

// プロセスの終了を待つ関数
export async function waitForProcess(
  process: Deno.ChildProcess
): Promise<ProcessWaitResult> {
  const { code } = await process.status;
  
  return {
    status: "success",
    code,
  };
}

// デコーダーを作成する関数
export function createTextDecoder(): TextDecoder {
  return new TextDecoder();
}
