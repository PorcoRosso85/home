// テスト用ヘルパー関数
function createWebSocketClient(endpoint: string = "ws://localhost:8080") {
  return new Promise<{send: (data: any) => Promise<any>, close: () => Promise<void>}>((resolve, reject) => {
    const ws = new WebSocket(endpoint);
    
    ws.onopen = () => {
      resolve({
        send: (data: any) => new Promise((resolve, reject) => {
          const messageId = Date.now();
          const message = { ...data, id: messageId };
          
          const handler = (e: MessageEvent) => {
            const res = JSON.parse(e.data);
            if (res.id === messageId) {
              ws.removeEventListener('message', handler);
              resolve(res);
            }
          };
          
          const errorHandler = () => {
            ws.removeEventListener('message', handler);
            ws.removeEventListener('error', errorHandler);
            reject(new Error("WebSocket send failed"));
          };
          
          ws.addEventListener('message', handler);
          ws.addEventListener('error', errorHandler);
          ws.send(JSON.stringify(message));
        }),
        close: () => {
          return new Promise<void>((resolve) => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.onclose = () => resolve();
              ws.close();
            } else {
              resolve();
            }
          });
        }
      });
    };
    
    ws.onerror = (error) => {
      console.log("WebSocket error:", error);
      reject(new Error("WebSocket connection failed"));
    };
  });
}

// WebSocket接続疎通テスト
Deno.test("WebSocket接続疎通", async () => {
  let client;
  try {
    client = await createWebSocketClient();
    const response = await client.send({
      jsonrpc: "2.0",
      method: "exec",
      params: { command: "echo", args: ["test"] }
    });
    
    console.log("接続テスト結果:", response.result?.stdout || response.error);
    
    if (!response.result?.stdout?.includes("test")) {
      throw new Error("接続失敗");
    }
    console.log("✅ WebSocket接続成功");
  } catch (error) {
    console.error("❌ WebSocket接続エラー:", error.message);
    throw error;
  } finally {
    if (client) {
      await client.close();
    }
  }
});

// Rust hello関数作成テスト
Deno.test("Rust hello関数作成", async () => {
  let client;
  try {
    client = await createWebSocketClient();
    const prompt = "/home/nixos/bin/src/tmp/hello.rs\nここにhelloを返す関数とそれをコンソール出力するためのテストをインソーステストとして記述して";
    
    const response = await client.send({
      jsonrpc: "2.0",
      method: "exec",
      params: { 
        command: "pnpm",
        args: ["dlx", "@anthropic-ai/claude-code", "--dangerously-skip-permissions", "-p", "--output-format", "json", prompt]
      }
    });
    
    console.log("Rust作成結果:", response.result?.stdout || response.error);
    
    const fileContent = await Deno.readTextFile("/home/nixos/bin/src/tmp/hello.rs");
    if (!fileContent.includes("hello") && !fileContent.includes("fn")) {
      throw new Error("ファイル作成失敗");
    }
    
    console.log("✅ Rust hello関数作成成功");
    console.log("ファイル内容プレビュー:", fileContent.substring(0, 100) + "...");
  } catch (error) {
    console.error("❌ Rust作成エラー:", error.message);
    throw error;
  } finally {
    if (client) {
      await client.close();
    }
  }
});
