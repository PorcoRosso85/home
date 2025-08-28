# Durable Objects SQLite POC

## ディレクトリ責務

- **SQLite in Durable Object**: Cloudflare Durable Objects内でSQLiteを使用する実装
- **概念実証**: Durable ObjectsとSQLiteの統合による永続性とパフォーマンスの検証

## 概要

このプロジェクトは、Cloudflare Durable Objects内でSQLiteデータベースを活用する概念実証（POC）です。
Durable Objectsの永続性とSQLiteの軽量データベース機能を組み合わせることで、エッジコンピューティング環境での効率的なデータ管理を実現します。

## 技術スタック

- Cloudflare Durable Objects
- SQLite (WASM版)
- Waku Framework (RSC対応)
- TypeScript
- Nix (開発環境管理)

## セットアップ

```bash
# 開発環境の起動
nix develop

# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev
```

## ビルド・デプロイ

```bash
# ビルド
nix run .#build

# デプロイ
nix run .#deploy
```

## プロジェクト構造

```
.
├── flake.nix           # Nix Flake設定
├── README.md           # プロジェクトドキュメント
└── (実装予定)
    ├── src/            # ソースコード
    ├── tests/          # テストコード
    └── wrangler.toml   # Cloudflare設定
```

## 主要機能（実装予定）

- Durable Object内でのSQLiteインスタンス管理
- トランザクション処理
- データ永続化とレプリケーション
- パフォーマンスメトリクスの収集

## 検証項目

- SQLiteのWASM版のパフォーマンス特性
- Durable Objectsのストレージ制限との整合性
- 同時接続処理の挙動
- データ整合性の保証