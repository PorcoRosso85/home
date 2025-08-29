// Progressive Enhancement実験
// use clientを条件付きで無効化できるか検証

import { useState } from 'react';

// サーバー版（フォールバック）
export function ServerCounter({ initial = 0 }: { initial?: number }) {
  return (
    <form method="POST" action="/api/increment">
      <input type="hidden" name="current" value={initial} />
      <div>Count: {initial}</div>
      <button type="submit" name="action" value="increment">
        + (Server)
      </button>
      <button type="submit" name="action" value="decrement">
        - (Server)
      </button>
    </form>
  );
}

// クライアント版
function ClientCounterInternal({ initial = 0 }: { initial?: number }) {
  'use client';
  const [count, setCount] = useState(initial);
  
  return (
    <div>
      <div>Count: {count}</div>
      <button onClick={() => setCount(count + 1)}>+ (Client)</button>
      <button onClick={() => setCount(count - 1)}>- (Client)</button>
    </div>
  );
}

// プログレッシブラッパー
export function ProgressiveCounter({ initial = 0 }: { initial?: number }) {
  // NoJSモードを検出する環境変数やヘッダーをチェック
  const noJsMode = process.env.DISABLE_CLIENT_JS === 'true';
  
  if (noJsMode) {
    return <ServerCounter initial={initial} />;
  }
  
  // 通常モード：クライアントコンポーネントを動的インポート
  return (
    <div suppressHydrationWarning>
      <noscript>
        <ServerCounter initial={initial} />
      </noscript>
      <div className="js-only">
        <ClientCounterInternal initial={initial} />
      </div>
    </div>
  );
}