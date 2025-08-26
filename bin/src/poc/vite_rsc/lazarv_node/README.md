# @lazarv/react-server × Node 22

React Server Components実装の`@lazarv/react-server`を Node.js 22 環境で動作検証するプロジェクト。

## 環境構築

### Nix Shell
```bash
nix develop
```

Node.js 22およびpnpm環境が自動的にセットアップされます。

## セットアップ

```bash
# 依存関係のインストール
pnpm install

# 開発サーバー起動
pnpm dev
```

## プロジェクト構造

```
├── app/           # アプリケーションコード
│   ├── page.tsx   # ページコンポーネント
│   └── layout.tsx # レイアウトコンポーネント
├── docs/          # ドキュメントキャッシュ
└── flake.nix      # Nix環境定義
```

## デプロイ

### Cloudflare Workers
```bash
# ビルド
pnpm build

# Cloudflareへデプロイ
wrangler deploy
```

## 技術スタック

- **Framework**: @lazarv/react-server
- **Runtime**: Node.js 22
- **Package Manager**: pnpm
- **Environment**: Nix Shell
- **Deployment**: Cloudflare Workers

## 関連ドキュメント

- [React Server Guide](docs/2025-08-26_17-18-18_react-server.dev_guide.md)
- [@lazarv/react-server 公式](https://react-server.dev)

## 開発メモ

- React Server Components (RSC) のフレームワーク非依存実装
- Vite互換のビルドシステム
- ストリーミングSSRサポート
- Server Functionsによるサーバー・クライアント間通信