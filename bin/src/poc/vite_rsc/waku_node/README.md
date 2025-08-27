# Waku Base Environment

このディレクトリは、Waku + Cloudflare Workers アプリケーションの基底環境を提供します。

## 責務
- **環境提供**: Node.js 22 + Wrangler + Waku
- **ビルド設定**: waku.config.ts
- **依存関係**: package.json (Waku, React, Hono)

## 使用方法

派生プロジェクトのflake.nixで参照:

```nix
inputs.waku-base.url = "github:user/repo?dir=bin/src/poc/vite_rsc/waku_node";
```

## 構成

```
waku_node/
├── flake.nix         # Nix環境定義
├── package.json      # 基底依存関係
├── waku.config.ts    # Waku設定
└── waku.*.ts        # Cloudflare統合設定
```

アプリケーション実装は派生側で行います。