// index.tsx - エントリーポイント
import React from "https://esm.sh/react@18.2.0";
import { createRoot } from "https://esm.sh/react-dom@18.2.0/client";
import App from "./App";

// アプリケーションのルートコンポーネント
export function AppRoot() {
  return (
    <App />
  );
}

// クライアントサイドでのレンダリング
if (typeof document !== 'undefined') {
  const rootElement = document.getElementById("root");
  if (rootElement) {
    const root = createRoot(rootElement);
    root.render(<AppRoot />);
  }
}
