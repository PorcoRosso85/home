# R2 WASM Architecture

## なぜR2を使うべきか

### Cloudflare Workers サイズ制限
- **無料プラン**: 1MB（圧縮後）
- **有料プラン**: 10MB（圧縮後）  
- **問題**: DuckDB (45MB)、SQLite (1.8MB)などのWASMファイルは制限超過

### R2の利点
- **ストレージ**: 無制限
- **エグレス料金**: 無料
- **グローバル配信**: Cloudflareネットワーク経由
- **Workers統合**: 同じアカウントでシームレス連携

## アーキテクチャ

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│   Worker    │────▶│     R2      │
│             │     │  (< 1MB)    │     │             │
│  - UI Code  │     │  - HTML/JS  │     │ - WASM files│
│  - Lazy Load│     │  - Router   │     │ - Data files│
└─────────────┘     └─────────────┘     └─────────────┘
       │                                        │
       └────────────────────────────────────────┘
         Direct fetch via Custom Domain (CORS)
```

## 実装方針

### 1. Worker（軽量）
- HTMLとJavaScriptのみ
- ルーティング処理
- 環境変数でR2 URLを管理

### 2. R2バケット
- すべてのWASMファイルを格納
- パブリックアクセス用Custom Domain設定
- CORS設定で直接アクセス可能

### 3. ブラウザ
- 必要時のみR2からWASMをfetch
- ローカルキャッシュ活用
- Progressive Enhancement

## セットアップ手順

### 1. R2バケット作成
```bash
# バケット作成
wrangler r2 bucket create waku-wasm

# カスタムドメイン設定（Cloudflare Dashboard）
# wasm.your-domain.com → waku-wasm
```

### 2. CORS設定
```bash
# cors.json
cat > cors.json << 'EOF'
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["Content-Length", "Content-Type"],
    "MaxAgeSeconds": 86400
  }
]
EOF

# CORS適用
wrangler r2 bucket cors put waku-wasm --rules cors.json
```

### 3. WASMファイルアップロード
```bash
# DuckDB WASM
wrangler r2 object put waku-wasm/duckdb/duckdb.wasm --file=./duckdb.wasm
wrangler r2 object put waku-wasm/duckdb/duckdb.js --file=./duckdb.js

# SQLite WASM  
wrangler r2 object put waku-wasm/sqlite/sqlite3.wasm --file=./sqlite3.wasm
wrangler r2 object put waku-wasm/sqlite/sqlite3.js --file=./sqlite3.js
```

### 4. 環境変数設定
```toml
# wrangler.toml
[vars]
R2_WASM_URL = "https://wasm.your-domain.com"

# または.env
R2_WASM_URL=https://wasm.your-domain.com
```

## コンポーネント実装

```tsx
// Generic WASM Loader
const WASMLoader = ({ 
  name, 
  wasmPath,
  displayName,
  estimatedSize 
}) => {
  const r2BaseUrl = process.env.R2_WASM_URL;
  const wasmUrl = `${r2BaseUrl}/${wasmPath}`;
  
  return (
    <LazyLoader
      loadUrl={wasmUrl}
      displayName={displayName}
      estimatedSize={estimatedSize}
    />
  );
};

// 使用例
<WASMLoader 
  name="sqlite"
  wasmPath="sqlite/sqlite3.wasm"
  displayName="SQLite"
  estimatedSize="1.8MB"
/>
```

## メリット

1. **Workerサイズ削減**: 1MB以下に収まる
2. **スケーラビリティ**: WASMファイル数/サイズ無制限
3. **パフォーマンス**: CDNキャッシュ活用
4. **コスト**: エグレス無料
5. **メンテナンス**: WASMファイルの独立更新可能

## 注意点

1. **初回ロード**: ネットワーク遅延考慮
2. **CORS設定**: 必須
3. **キャッシュ戦略**: Cache-Control設定推奨
4. **バージョニング**: URLにバージョン含める

```
waku-wasm/sqlite/v1.0.0/sqlite3.wasm
waku-wasm/duckdb/v0.9.2/duckdb.wasm
```