import React from 'react';
import ReactDOM from 'react-dom/client';
import { HomePage } from './pages/index.tsx'; // 拡張子を明示

// Vite-plugin-deno ではasset importがサポートされていないため、
// ランタイムにリソースパスを指定する方法を使用
const styleUrl = new URL('../public/styles.css', import.meta.url).href;
const themeUrl = new URL('../public/theme.css', import.meta.url).href;

// スタイルシートを動的に読み込む
document.addEventListener('DOMContentLoaded', () => {
  // スタイルシートが既に読み込まれていないか確認
  if (!document.querySelector(`link[href="${styleUrl}"]`)) {
    const styleLink = document.createElement('link');
    styleLink.rel = 'stylesheet';
    styleLink.href = styleUrl;
    document.head.appendChild(styleLink);
  }
  
  if (!document.querySelector(`link[href="${themeUrl}"]`)) {
    const themeLink = document.createElement('link');
    themeLink.rel = 'stylesheet';
    themeLink.href = themeUrl;
    document.head.appendChild(themeLink);
  }
});

// クラシックなJSX表記に合わせたレンダリング
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  React.createElement(React.StrictMode, null,
    React.createElement(HomePage, null)
  )
);
