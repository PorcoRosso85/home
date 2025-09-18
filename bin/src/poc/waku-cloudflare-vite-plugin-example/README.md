# Waku + @cloudflare/vite-plugin 統合例

このプロジェクトは、Waku（PR#1619）と@cloudflare/vite-pluginの統合を実証するPOCです。

## 主要な実装ポイント

### @cloudflare/vite-pluginの統合
- **vite-pluginがCloudflare Workersのために使用可能**
  - waku.config.tsでrsc環境に@cloudflare/vite-pluginを適用
  - WASMバンドルのサポートが可能（Issue #1245で要望された機能）

### 設定ファイル構成

#### waku.config.ts
```typescript
vite: {
  plugins: [
    cloudflare({
      viteEnvironment: { name: "rsc" }
    }),
  ],
}
```

#### wrangler.jsonc
- エントリーポイント: `./src/server.ts`
- nodejs_compatフラグ有効（Wakuのサーバーサイドコンテキストに必要）
- ASSETSバインディングで静的アセット配信

### 解決された課題
1. **Issue #1596**: @cloudflare/vite-pluginの統合が可能に
   - エントリーポイント問題を解決（src/server.ts）
   - rsc環境での動作を実現

2. **Issue #1245**: WASMファイルのサポート
   - @cloudflare/vite-pluginがWASMバンドルを正しく処理可能
   - Shikiなどのパッケージで必要なWASMファイルのインポートに対応

## アーキテクチャ

```
Waku (3環境)
├── client環境
├── ssr環境（オプション）
└── rsc環境 ← @cloudflare/vite-plugin適用
    └── Cloudflare Workers実行環境
```

## 依存関係

- waku: PR#1619版（@vitejs/plugin-rsc対応）
- @cloudflare/vite-plugin: 1.11.2
- wrangler: 4.27.0
- vite: 7.0.5

## ビルド・デプロイ

```bash
# 開発
npm run dev

# ビルド（Cloudflare用）
npm run build

# ローカル実行（Wrangler）
npm run start
```

## 注意事項

- nodejs_compatフラグが必要（Wakuのrequest contextのため）
- 静的ページのみの場合はnodejs_compatフラグは不要
- dist/assetsディレクトリが正しく生成されることを確認