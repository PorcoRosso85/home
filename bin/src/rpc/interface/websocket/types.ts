// WebSocket関連の型定義

export type WebSocketConnection = {
  socket: WebSocket;
  send: (message: unknown) => void;
  close: () => void;
};

export type ConnectionSuccess = {
  status: "success";
  connection: WebSocketConnection;
};

export type ConnectionError = {
  status: "error";
  errorCode: "UPGRADE_FAILED" | "WEBSOCKET_ERROR";
  message: string;
};

export type ConnectionResult = ConnectionSuccess | ConnectionError;

export type MessageParseSuccess = {
  status: "success";
  request: unknown;
};

export type MessageParseError = {
  status: "error";
  errorCode: "PARSE_ERROR" | "INVALID_FORMAT";
  message: string;
};

export type MessageParseResult = MessageParseSuccess | MessageParseError;

export type ServerConfig = {
  port: number;
  hostname?: string;
};

export type ServerStartSuccess = {
  status: "success";
  url: string;
};

export type ServerStartError = {
  status: "error";
  errorCode: "BIND_ERROR" | "PERMISSION_ERROR";
  message: string;
};

export type ServerStartResult = ServerStartSuccess | ServerStartError;
