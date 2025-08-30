# Non-CDN WASM Loading Guide

## 概要
CDNで提供されていないWASMファイル（SQLite WASM等）をWaku/Cloudflare Workersで使用する方法

## 方法1: Public Directory (推奨)

### セットアップ
```bash
# WASMファイルをpublicディレクトリに配置
public/
  wasm/
    sqlite3.wasm
    sqlite3.js
```

### package.jsonの設定
```json
{
  "scripts": {
    "build": "waku build --with-cloudflare && cp -r public/wasm dist/assets/wasm 2>/dev/null || true"
  }
}
```

### コンポーネントでの使用
```tsx
const wasmUrl = '/wasm/sqlite3.wasm';
const response = await fetch(wasmUrl);
const wasmBuffer = await response.arrayBuffer();
```

## 方法2: NPMパッケージからコピー

### インストール
```bash
npm install @sqlite/wasm-esm
```

### ビルドスクリプト
```json
{
  "scripts": {
    "build": "waku build --with-cloudflare && npm run copy-wasm",
    "copy-wasm": "cp -r node_modules/@sqlite/wasm-esm/dist/* dist/assets/wasm/"
  }
}
```

## 方法3: Cloudflare R2からロード

### R2へのアップロード
```bash
# R2バケットにWASMファイルをアップロード
wrangler r2 object put waku-data/sqlite3.wasm --file=./sqlite3.wasm

# CORSポリシーを設定
```

### コンポーネントでの使用
```tsx
const wasmUrl = 'https://your-r2-domain.com/sqlite3.wasm';
```

## 方法4: Base64エンコード（小さなWASMファイル用）

### ビルド時にBase64化
```javascript
// build-wasm.js
const fs = require('fs');
const wasmBuffer = fs.readFileSync('./sqlite3.wasm');
const base64 = wasmBuffer.toString('base64');
fs.writeFileSync('./src/wasm-data.js', 
  `export const WASM_BASE64 = "${base64}";`
);
```

### 使用時
```tsx
import { WASM_BASE64 } from './wasm-data';
const wasmBuffer = Buffer.from(WASM_BASE64, 'base64');
```

## 実装例: SQLiteLoader

```tsx
// sqlite-loader.tsx
const SQLiteLoader = ({ wasmUrl = '/wasm/sqlite3.wasm' }) => {
  const [shouldLoad, setShouldLoad] = useState(false);
  
  // 遅延ロード実装
  if (!shouldLoad) {
    return <button onClick={() => setShouldLoad(true)}>Load SQLite</button>;
  }
  
  return (
    <Suspense fallback={<div>Loading SQLite WASM...</div>}>
      <SQLiteDemo wasmUrl={wasmUrl} />
    </Suspense>
  );
};
```

## Cloudflare Workers制限事項

### メモリ制限
- Workers: 128MB
- Workers Paid: 512MB
- WASMファイルサイズに注意

### 実行時間制限
- 無料: 10ms CPU時間
- 有料: 30秒

### ワークアラウンド
- 大きなWASMは分割ロード
- Service Bindingsで別Workerへ処理委譲
- Durable Objectsで永続的な処理

## トラブルシューティング

### CORS エラー
```json
// R2 CORS設定
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000
  }
]
```

### MIME Type エラー
```javascript
// Workerでヘッダー設定
return new Response(wasmBuffer, {
  headers: {
    'Content-Type': 'application/wasm',
    'Cache-Control': 'public, max-age=31536000'
  }
});
```

### Module Instantiation エラー
```javascript
// 正しい初期化方法
const module = await WebAssembly.instantiate(wasmBuffer, imports);
```

## パフォーマンス最適化

1. **キャッシング**: ブラウザキャッシュを活用
2. **圧縮**: Brotli/Gzip圧縮を有効化
3. **遅延ロード**: 必要時のみロード
4. **CDN化**: 可能ならR2 + Custom Domainで配信

## 推奨構成

小規模WASM（< 1MB）: Public Directory
中規模WASM（1-10MB）: R2 + 遅延ロード
大規模WASM（> 10MB）: R2 + 分割ロード + Worker Cache