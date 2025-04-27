// Kuzu-WASM初期化と実行
// Reactアプリケーションのエントリーポイント
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';

console.log("Kuzu-WASM ESMモジュールを読み込みました");

// DOMが読み込まれたらReactアプリケーションをマウント
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById('root');
  if (container) {
    const root = createRoot(container);
    root.render(React.createElement(App));
    console.log("Reactアプリケーションをマウントしました");
  } else {
    console.error("ルート要素が見つかりません");
  }
});
