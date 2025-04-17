// src/App.tsx - メインアプリケーションコンポーネント
import React from 'react';

// SSRでも利用できるようにエクスポート
export function App() {
  return (
    <div className="app-container">
      <h1>Hello from Bun + Vite + React + SSR!</h1>
      <p>Bunを使用したViteベースのSSR/SSGフレームワーク</p>
    </div>
  );
}

export default App;
