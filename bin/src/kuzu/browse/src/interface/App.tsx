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
    for (let i = 1; i <= 16; i++) {
      const ws = new WebSocket("ws://localhost:8080");
      
      let question;
      if (i === 16) {
        question = "show me fibonacci function by rust, in short with only code";
      } else {
        question = i % 2 === 1 ? "just say hi" : "what's your name? in short";
      }
      
      ws.onopen = () => {
        ws.send(JSON.stringify({
          jsonrpc: "2.0",
          method: "exec",
          params: { 
            command: "pnpm",
            args: ["dlx", "@anthropic-ai/claude-code", "-p", question]
          },
          id: i
        }));
      };
      
      ws.onmessage = (e) => {
        const res = JSON.parse(e.data);
        console.log(`Session ${i}:`, res.result?.stdout || res.error);
        ws.close();
      };
    }
  };

  return (
    <Layout>
      <Page />
      <button onClick={handleDualClaude} style={{position: 'fixed', bottom: 20, right: 20}}>
        16x Claude
      </button>
    </Layout>
  );
};

export default App;
