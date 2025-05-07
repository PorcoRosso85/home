// kuzu/terminal/serve/types.ts

// JSON-RPCリクエスト
export interface RPCRequest {
  jsonrpc: string;
  id: string | number | null;
  method: string;
  params?: {
    command: string;
    args?: string[];
    stdin?: string;
  };
}

// JSON-RPCレスポンス
export interface RPCResponse {
  jsonrpc: string;
  id: string | number | null;
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

// ストリームイベント
export interface StreamEvent {
  jsonrpc: string;
  method: string;
  params: {
    id: string | number;
    data: string;
  };
}
