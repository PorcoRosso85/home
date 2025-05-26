/**
 * KuzuDB Graph Browser のメインアプリケーションコンポーネント
 */
import React from 'react';
import { Layout } from './Layout';
import { Page } from './Page';

/**
 * アプリケーションのメインコンポーネント
 */
const App: React.FC = () => {
  const handleDualClaude = () => {
    // 1つ目のWebSocket接続
    const ws1 = new WebSocket("ws://localhost:8080");
    ws1.onopen = () => {
      ws1.send(JSON.stringify({
        jsonrpc: "2.0",
        method: "exec",
        params: { 
          command: "pnpm",
          args: ["dlx", "@anthropic-ai/claude-code", "-p", "just say hi"]
        },
        id: 1
      }));
    };
    ws1.onmessage = (e) => {
      const res = JSON.parse(e.data);
      console.log("Session 1:", res.result?.stdout || res.error);
      ws1.close();
    };

    // 2つ目のWebSocket接続（同時実行）
    const ws2 = new WebSocket("ws://localhost:8080");
    ws2.onopen = () => {
      ws2.send(JSON.stringify({
        jsonrpc: "2.0",
        method: "exec",
        params: { 
          command: "pnpm",
          args: ["dlx", "@anthropic-ai/claude-code", "-p", "what's your name? in short"]
        },
        id: 2
      }));
    };
    ws2.onmessage = (e) => {
      const res = JSON.parse(e.data);
      console.log("Session 2:", res.result?.stdout || res.error);
      ws2.close();
    };
  };

  return (
    <Layout>
      <Page />
      <button onClick={handleDualClaude} style={{position: 'fixed', bottom: 20, right: 20}}>
        Dual Claude
      </button>
    </Layout>
  );
};

export default App;
