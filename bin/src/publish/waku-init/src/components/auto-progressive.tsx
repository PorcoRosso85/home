// 自動プログレッシブエンハンスメント実験
// use clientを動的に切り替える

import type { ComponentType } from 'react';
import { getEnableClient } from '../infrastructure/mod.js';

// 条件付きuse clientのラッパー
export function withAutoProgressive<P extends object>(
  ServerComponent: ComponentType<P>,
  clientPath: string // クライアントコンポーネントのパス
) {
  return async function AutoProgressive(props: P) {
    // 実行時条件チェック
    const enableClient = getEnableClient();
    const userAgent = globalThis.headers?.get('user-agent') || '';
    const isBot = /bot|crawler|spider/i.test(userAgent);
    const acceptsJS = !globalThis.headers?.get('save-data'); // データセーブモード
    
    // 条件判定
    const shouldUseClient = enableClient && !isBot && acceptsJS;
    
    if (!shouldUseClient) {
      // サーバーコンポーネントを使用
      return <ServerComponent {...props} />;
    }
    
    // クライアントコンポーネントを動的インポート
    try {
      const { default: ClientComponent } = await import(clientPath);
      return <ClientComponent {...props} />;
    } catch (error) {
      console.warn('Failed to load client component, falling back to server:', error);
      return <ServerComponent {...props} />;
    }
  };
}

// 使用例
export const SmartForm = withAutoProgressive(
  // サーバー版
  function ServerForm({ onSubmit }: { onSubmit?: string }) {
    return (
      <form method="POST" action={onSubmit || '/api/submit'}>
        <input name="email" type="email" required />
        <button type="submit">Submit (Server)</button>
      </form>
    );
  },
  // クライアント版のパス
  './client-form'
);