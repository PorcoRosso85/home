import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';
import './main'; // KuzuDBの初期化処理を読み込む

// DOMContentLoadedイベントでReactアプリをマウント
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOMContentLoaded: Reactアプリをマウントします');
  const rootElement = document.getElementById('root');
  
  if (rootElement) {
    // React 18のcreateRootメソッドを使用してレンダリング
    const root = createRoot(rootElement);
    root.render(<App />);
    console.log('Reactアプリがマウントされました');
  } else {
    console.error('エラー: rootエレメントが見つかりません。');
  }
});
