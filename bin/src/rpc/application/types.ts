// アプリケーション層の型定義

export type JsonRpcRequest = {
  jsonrpc: "2.0";
  method: string;
  params?: unknown;
  id: number | string;
};

export type JsonRpcSuccess = {
  jsonrpc: "2.0";
  result: unknown;
  id: number | string;
};

export type JsonRpcError = {
  jsonrpc: "2.0";
  error: {
    code: number;
    message: string;
    data?: unknown;
  };
  id: number | string;
};

export type JsonRpcResponse = JsonRpcSuccess | JsonRpcError;

export type ExecParams = {
  command: string;
  args?: string[];
  cwd?: string;
};

export type ExecStreamResult = {
  stdout?: string;
  stream: boolean;
  complete?: boolean;
  code?: number;
};

export type HandlerSuccess = {
  status: "success";
  response: JsonRpcResponse;
};

export type HandlerError = {
  status: "error";
  errorCode: "INVALID_METHOD" | "INVALID_PARAMS" | "INTERNAL_ERROR";
  response: JsonRpcError;
};

export type HandlerResult = HandlerSuccess | HandlerError;

// メッセージ送信関数の型
export type MessageSender = (message: JsonRpcResponse) => void;

// ハンドラーの依存性
export type HandlerDependencies = {
  commandExecutor: (params: unknown) => AsyncGenerator<unknown>;
  messageSender: MessageSender;
};
