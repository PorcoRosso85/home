/** @jsxImportSource react */
// index.tsx - シンプルなアプリケーションエントリポイント
import React from 'react';
import { createRoot } from 'react-dom/client';

// シンプルなアプリケーションコンポーネント
function App() {
  return (
    <div className="app-container">
      <h1>Hello from Bun + Vite + React!</h1>
      <p>シンプルなBun + Viteアプリケーション</p>
    </div>
  );
}

// クライアントサイドでのレンダリング
if (typeof document !== 'undefined') {
  const rootElement = document.getElementById('root');
  if (rootElement) {
    const root = createRoot(rootElement);
    root.render(<App />);
  }
}