// インフラ層の型定義

export type ProcessSpawnSuccess = {
  status: "success";
  process: Deno.ChildProcess;
  reader: ReadableStreamDefaultReader<Uint8Array>;
};

export type ProcessSpawnError = {
  status: "error";
  errorCode: "SPAWN_ERROR" | "PERMISSION_ERROR" | "COMMAND_NOT_FOUND";
  message: string;
};

export type ProcessSpawnResult = ProcessSpawnSuccess | ProcessSpawnError;

export type StreamReadSuccess = {
  status: "success";
  chunk: string;
  done: boolean;
};

export type StreamReadError = {
  status: "error";
  errorCode: "READ_ERROR" | "DECODE_ERROR";
  message: string;
};

export type StreamReadResult = StreamReadSuccess | StreamReadError;

export type ProcessWaitSuccess = {
  status: "success";
  code: number;
};

export type ProcessWaitError = {
  status: "error";
  errorCode: "WAIT_ERROR";
  message: string;
};

export type ProcessWaitResult = ProcessWaitSuccess | ProcessWaitError;
