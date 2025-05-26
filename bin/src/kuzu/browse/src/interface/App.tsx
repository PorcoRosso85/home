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
  const [sessionIds, setSessionIds] = React.useState<Record<number, string>>({});
  
  const handleDualClaude = () => {
    for (let i = 1; i <= 16; i++) {
      const ws = new WebSocket("ws://localhost:8080");
      
      let question;
      if (i === 16) {
        question = "show me fibonacci function by rust, in short with only code";
      } else {
        question = i % 2 === 1 ? "just say hi" : "what's your name? in short";
      }
      
      // セッションIDがある場合は--resumeを使用
      const args = sessionIds[i] 
        ? ["dlx", "@anthropic-ai/claude-code", "-p", "--resume", sessionIds[i], question]
        : ["dlx", "@anthropic-ai/claude-code", "-p", "--output-format", "json", question];
      
      ws.onopen = () => {
        ws.send(JSON.stringify({
          jsonrpc: "2.0",
          method: "exec",
          params: { 
            command: "pnpm",
            args: args
          },
          id: i
        }));
      };
      
      ws.onmessage = (e) => {
        const res = JSON.parse(e.data);
        const output = res.result?.stdout || res.error;
        console.log(`Session ${i}:`, output);
        
        // セッションIDを抽出して保存
        if (!sessionIds[i] && res.result?.stdout) {
          const jsonMatch = res.result.stdout.match(/\{[\s\S]*"session_id"[\s\S]*\}/);
          if (jsonMatch) {
            try {
              const data = JSON.parse(jsonMatch[0]);
              setSessionIds(prev => ({ ...prev, [i]: data.session_id }));
            } catch (err) {
              console.error(`Failed to parse session ${i}:`, err);
            }
          }
        }
        
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