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
  const handleHiClaude = () => {
    const ws = new WebSocket("ws://localhost:8080");
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        jsonrpc: "2.0",
        method: "exec",
        params: { 
          command: "pnpm",
          args: ["dlx", "@anthropic-ai/claude-code", "-p", "just say hi"]
        },
        id: 1
      }));
    };
    
    ws.onmessage = (e) => {
      const res = JSON.parse(e.data);
      console.log(res.result?.stdout || res.error);
      alert(res.result?.stdout || JSON.stringify(res.error));
      ws.close();
    };
  };

  const handleNameClaude = () => {
    const ws = new WebSocket("ws://localhost:8080");
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        jsonrpc: "2.0",
        method: "exec",
        params: { 
          command: "pnpm",
          args: ["dlx", "@anthropic-ai/claude-code", "-p", "what's your name? in short"]
        },
        id: 2
      }));
    };
    
    ws.onmessage = (e) => {
      const res = JSON.parse(e.data);
      console.log(res.result?.stdout || res.error);
      alert(res.result?.stdout || JSON.stringify(res.error));
      ws.close();
    };
  };

  return (
    <Layout>
      <Page />
      <button onClick={handleHiClaude} style={{position: 'fixed', bottom: 20, right: 20}}>
        Say Hi
      </button>
      <button onClick={handleNameClaude} style={{position: 'fixed', bottom: 60, right: 20}}>
        Name?
      </button>
    </Layout>
  );
};

export default App;
