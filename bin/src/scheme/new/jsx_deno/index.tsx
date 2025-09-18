// index.tsx - アプリケーションコンポーネントと最適化されたハイドレーション処理
import React from "https://esm.sh/react@18.2.0";
import { hydrateRoot } from "https://esm.sh/react-dom@18.2.0/client";

// SSRでも利用できるようにエクスポート
export function App() {
  return <h1>Hello from Deno + Vite + SSR!</h1>;
}

// React Server Componentライクなハイドレーション最適化のためのヘルパー
function optimizeHydration(rootElement: Element) {
  // パフォーマンスマーカー追加
  if (typeof performance !== 'undefined' && performance.mark) {
    performance.mark('hydration-start');
  }
  
  // 最適化されたハイドレーション（React 18のhydrateRootを使用）
  const root = hydrateRoot(rootElement, <App />);
  
  // ハイドレーション完了後の処理
  window.setTimeout(() => {
    // ハイドレーション完了をマーク
    if (typeof performance !== 'undefined' && performance.mark) {
      performance.mark('hydration-end');
      performance.measure('hydration-duration', 'hydration-start', 'hydration-end');
    }
    
    // ドキュメントにハイドレーション完了のマーカーを設定
    document.documentElement.setAttribute('data-hydrated', 'true');
    
    // デバッグ情報（開発環境のみ）
    if (import.meta.env?.DEV) {
      console.log('[Hydration] Complete');
    }
  }, 0);
  
  return root;
}

// クライアントサイドでのハイドレーション
if (typeof document !== 'undefined') {
  const rootElement = document.getElementById("root");
  if (rootElement) {
    // より効率的なハイドレーションのためoptimizeHydration関数を使用
    optimizeHydration(rootElement);
  }
}
