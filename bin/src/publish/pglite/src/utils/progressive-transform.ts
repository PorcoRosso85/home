// Waku ビルドプラグイン: use client自動フォールバック
// vite.config.tsで使用

export function progressiveEnhancementPlugin() {
  return {
    name: 'progressive-enhancement',
    
    transform(code: string, id: string) {
      // .tsxファイルのみ処理
      if (!id.endsWith('.tsx')) return null;
      
      // use clientディレクティブを検出
      if (!code.includes("'use client'")) return null;
      
      // NoJSモードチェックを挿入
      const transformed = code.replace(
        /^'use client';?\n/m,
        `
// Progressive Enhancement自動挿入
if (typeof window === 'undefined' && process.env.PROGRESSIVE_MODE === 'true') {
  // use clientを無効化してサーバーコンポーネントとして扱う
  module.exports = require('./server-fallback');
  return;
}
'use client';
`
      );
      
      return {
        code: transformed,
        map: null
      };
    }
  };
}

// ランタイムヘルパー
export function useProgressive() {
  // SSR中かどうかを判定
  const isServer = typeof window === 'undefined';
  
  // ハイドレーション完了を検出
  const [isHydrated, setIsHydrated] = useState(false);
  
  useEffect(() => {
    setIsHydrated(true);
  }, []);
  
  return {
    isServer,
    isHydrated,
    isProgressive: isServer || !isHydrated
  };
}