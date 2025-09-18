# ESM/モックなし実装のハードル

## 現在のハードル

### 1. KuzuDB WASM の Worker 要件
- **問題**: KuzuDB WASMの非同期版はWeb Workerが必須
- **Denoの制限**: Classic Worker非サポート (`NotSupported: Classic workers are not supported`)
- **影響**: テスト環境でKuzuDB WASMが動作しない

### 2. ESM/CommonJS 相互運用
- **問題**: KuzuDB WASM Node.js版はCommonJSのみ
- **エラー**: `Dynamic require of "fs" is not supported`
- **影響**: ESM環境でNode.js版が使用できない

### 3. WebSocket サーバー要件
- **問題**: 実際のWebSocket接続にはサーバーが必要
- **影響**: 統合テストで実サーバーの起動が必要

## 解決策

### 案1: ブラウザ環境でのE2Eテスト（推奨）
```typescript
// playwright.config.ts
export default {
  use: {
    // 実際のブラウザでKuzuDB WASMを実行
    launchOptions: {
      args: ['--enable-features=SharedArrayBuffer']
    }
  }
};
```

### 案2: KuzuDB同期版をESMラッパーで包む
```typescript
// kuzu-esm-wrapper.mjs
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

// CommonJSモジュールをESMでラップ
export default function createKuzuDB() {
  const kuzu = require('kuzu-wasm/nodejs/sync');
  return kuzu;
}
```

### 案3: Deno KVをストレージとして使用
```typescript
// deno-kv-storage.ts
// KuzuDBの代わりにDeno KVを使用（テスト専用）
export class DenoKVStorage {
  private kv: Deno.Kv;
  
  async executeTemplate(template: string, params: any) {
    // Deno KVでグラフ操作をシミュレート
  }
}
```

### 案4: WebContainerでNode.js環境を仮想化
```typescript
// WebContainer APIを使用してNode.js環境を作成
import { WebContainer } from '@webcontainer/api';

const container = await WebContainer.boot();
await container.mount({
  'index.js': {
    file: {
      contents: `
        const kuzu = require('kuzu-wasm/nodejs');
        // 実際のKuzuDB実行
      `
    }
  }
});
```

## 実装優先順位

1. **短期**: Playwright E2Eテストで実ブラウザ環境を使用
2. **中期**: ESMラッパーでKuzuDB同期版を包む
3. **長期**: KuzuDB側にESMサポートを要請

## 技術的制約

- Worker仕様の違い（Classic Worker vs Module Worker）
- WASM初期化の非同期性
- SharedArrayBufferのCross-Origin Isolation要件
- Node.jsファイルシステムAPIの依存