// ドメイン層の型定義

export type CommandParams = {
  command: string;
  args?: string[];
  cwd?: string;
};

export type CommandExecutionSuccess = {
  status: "success";
  code: number;
  stdout: string[];
};

export type CommandExecutionError = {
  status: "error";
  errorCode: "INVALID_PARAMS" | "EXECUTION_FAILED" | "STREAM_ERROR";
  message: string;
  details?: unknown;
};

export type CommandExecutionResult = CommandExecutionSuccess | CommandExecutionError;

export type StreamChunk = {
  type: "chunk";
  data: string;
};

export type StreamComplete = {
  type: "complete";
  code: number;
};

export type StreamError = {
  type: "error";
  errorCode: string;
  message: string;
};

export type StreamMessage = StreamChunk | StreamComplete | StreamError;

// 依存性の型定義
export type ProcessRunner = {
  spawn: (command: string, args: string[], cwd: string) => {
    status: "success";
    process: unknown;
    reader: unknown;
  } | {
    status: "error";
    errorCode: string;
    message: string;
  };
  readStream: (reader: unknown, decoder: unknown) => Promise<{
    status: "success";
    chunk: string;
    done: boolean;
  } | {
    status: "error";
    errorCode: string;
    message: string;
  }>;
  waitProcess: (process: unknown) => Promise<{
    status: "success";
    code: number;
  } | {
    status: "error";
    errorCode: string;
    message: string;
  }>;
  createDecoder: () => unknown;
};
