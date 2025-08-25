# Vite RSC → Cloudflare Workers デプロイ分析

## 問題の本質

Vite RSCビルドとCloudflare Workersの根本的な非互換性：

### 1. ランタイムAPI差異
| Vite RSC (Node.js) | Cloudflare Workers |
|--------------------|-------------------|
| `fs.readFile()` | 利用不可 |
| `path.join()` | 利用不可 |
| `process.env` | `env`バインディング |
| `http.createServer()` | `fetch`ハンドラ |
| `stream.Readable` | `ReadableStream` |

### 2. React SSRの違い
```javascript
// Node.js版（Vite RSCが生成）
import { renderToPipeableStream } from 'react-dom/server';

// Workers版（必要なもの）
import { renderToReadableStream } from 'react-dom/server.edge';
```

### 3. モジュール解決
- **Vite RSC**: ファイルシステムベースの動的import
- **Workers**: バンドル時に全て解決済み必要

## 解決策の選択肢

### Option 1: アダプター層の実装（推奨）
```javascript
// cloudflare-adapter.js
import { handler as rscHandler } from './dist/rsc/index.js';
import { renderToReadableStream } from 'react-dom/server.edge';

export default {
  async fetch(request, env) {
    // Node.js APIをWorkers APIにブリッジ
    const rscStream = await rscHandler(request);
    const htmlStream = await renderToReadableStream(rscStream);
    return new Response(htmlStream);
  }
}
```

### Option 2: @cloudflare/vite-plugin使用
```javascript
// vite.config.ts
import { cloudflare } from '@cloudflare/vite-plugin';
import { rsc } from '@vitejs/plugin-rsc';

export default {
  plugins: [
    rsc(),
    cloudflare() // Workers環境を提供
  ],
  environments: {
    ssr: {
      target: 'webworker' // Node.jsではなくWorkers向け
    }
  }
}
```

### Option 3: ビルド後変換
```bash
# 1. Viteでビルド
npm run build

# 2. Workers用に変換
npx @cloudflare/workers-build dist/ssr/index.js \
  --outfile=worker.js \
  --target=es2022 \
  --platform=browser
```

## 現実的な次のステップ

1. **最小限のWorkerラッパー作成**（現在実装済み）
   - `worker-entry.js`で静的レスポンス
   - デプロイパイプライン確立

2. **段階的な統合**
   - 静的アセット配信から開始
   - SSRを徐々に追加
   - 最後にRSC統合

3. **または別アプローチ**
   - Vite RSCをNode.jsサーバーで実行
   - CloudflareをCDN/プロキシとして使用

## 結論

**Vite RSCビルドを直接Workersにデプロイは不可能**。理由：
- ランタイムAPI非互換
- モジュール形式の違い
- サイズ制限

**解決には変換層が必須**。