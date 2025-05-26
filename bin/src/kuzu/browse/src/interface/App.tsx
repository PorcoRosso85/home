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
  const handleLsClick = () => {
    const ws = new WebSocket("ws://localhost:8080");
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        jsonrpc: "2.0",
        method: "ls",
        params: { args: ["-la"] },
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

  return (
    <Layout>
      <Page />
      <button onClick={handleLsClick} style={{position: 'fixed', bottom: 20, right: 20}}>
        LS実行
      </button>
    </Layout>
  );
};

export default App;
