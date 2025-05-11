import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';
import './main'; // KuzuDBの初期化処理を読み込む
import * as logger from '../../common/infrastructure/logger';

// DOMContentLoadedイベントでReactアプリをマウント
document.addEventListener('DOMContentLoaded', () => {
  logger.debug('DOMContentLoaded: Reactアプリをマウントします');
  const rootElement = document.getElementById('root');
  
  if (rootElement) {
    // React 18のcreateRootメソッドを使用してレンダリング
    const root = createRoot(rootElement);
    root.render(<App />);
    logger.debug('Reactアプリがマウントされました');
  } else {
    logger.error('エラー: rootエレメントが見つかりません。');
  }
});
