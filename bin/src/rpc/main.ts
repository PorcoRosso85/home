// エントリーポイント

import {
  createWebSocketHandler,
  createHttpHandler,
  startServer,
} from "./interface/websocket/server.ts";
import { createMethodHandler } from "./application/handlers/execHandler.ts";
import { createStreamingCommandExecutor } from "./domain/command/executor.ts";
import {
  spawnProcess,
  readFromStream,
  waitForProcess,
  createTextDecoder,
} from "./infrastructure/process/commandRunner.ts";
import type { ProcessRunner } from "./domain/command/types.ts";
import type { JsonRpcResponse } from "./application/types.ts";
import type { WebSocketConnection } from "./interface/websocket/types.ts";

// 依存性の組み立て
function createProcessRunner(): ProcessRunner {
  return {
    spawn: spawnProcess,
    readStream: readFromStream,
    waitProcess: waitForProcess,
    createDecoder: createTextDecoder,
  };
}

// アプリケーションの組み立て
function createApplication() {
  // インフラ層の依存性
  const processRunner = createProcessRunner();
  
  // ドメイン層
  const commandExecutor = createStreamingCommandExecutor({ processRunner });
  
  // 現在の接続を保持するクロージャ
  let currentConnection: WebSocketConnection | null = null;
  
  // メッセージ送信関数
  const messageSender = (message: JsonRpcResponse) => {
    if (currentConnection) {
      currentConnection.send(message);
    }
  };
  
  // アプリケーション層
  const methodHandler = createMethodHandler({
    commandExecutor,
    messageSender,
  });
  
  // インターフェース層
  const websocketHandler = createWebSocketHandler({
    methodHandler,
  });
  
  // 接続を設定するハンドラーをラップ
  const connectionAwareHandler = (connection: WebSocketConnection) => {
    currentConnection = connection;
    websocketHandler(connection);
    
    // 接続が閉じられたらリセット
    connection.socket.addEventListener("close", () => {
      currentConnection = null;
    });
  };
  
  const httpHandler = createHttpHandler({
    websocketHandler: connectionAwareHandler,
  });
  
  return {
    httpHandler,
  };
}

// メイン関数
async function main() {
  const app = createApplication();
  
  const config = {
    port: 8080,
    hostname: "localhost",
  };
  
  await startServer(config, app.httpHandler);
}

// エントリーポイント
if (import.meta.main) {
  main();
}
