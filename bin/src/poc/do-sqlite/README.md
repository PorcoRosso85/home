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
├── flake.nix           # Nix Flake設定（waku_node継承）
├── README.md           # プロジェクトドキュメント
├── src/                # ソースコード
│   ├── index.ts        # Worker エントリポイント
│   └── do-sqlite.ts    # Durable Object実装
├── wrangler.toml       # Cloudflare設定
├── tsconfig.json       # TypeScript設定
└── package.json        # 依存関係定義
```

## 責務と設計判断

### このFlakeの責務
- **実装責務**: Durable Objects SQLite POCの具体的な実装
- **継承関係**: `waku_node`から開発環境を継承（Node.js、Wrangler等）
- **独立性**: ビジネスロジックは完全に独立

### 関連プロジェクトとの責務分離
```
bin/src/
├── poc/vite_rsc/
│   ├── waku_node/      # 開発ツール提供（npm, wrangler, turbo等）
│   └── waku-init/      # POCテンプレート
└── publish/
    └── poc/
        └── do-sqlite/  # ← このプロジェクト（実装のみ）
```

### Turborepoとの統合（将来）
- **ツール提供**: `waku_node`がTurborepoコマンドを提供
- **設定配置**: `bin/turbo.json`で全体統括
- **このプロジェクト**: 必要に応じて`turbo.json`で固有タスク定義

## 実装済み機能

- ✅ Durable Object内でのSQLiteインスタンス管理
- ✅ KVストア API (GET/SET/DELETE/LIST)
- ✅ SQLiteインデックスによる高速クエリ
- ✅ REST APIエンドポイント
- ✅ トランザクション処理（UPSERT対応）

## API エンドポイント

```
GET    /do/sqlite/{id}/get?key={key}      # 値の取得
POST   /do/sqlite/{id}/set                # 値の設定（JSON body）
GET    /do/sqlite/{id}/list?limit={n}     # 最新エントリ一覧
DELETE /do/sqlite/{id}/delete?key={key}   # 値の削除
```

## 検証項目

- SQLiteのWASM版のパフォーマンス特性
- Durable Objectsのストレージ制限との整合性
- 同時接続処理の挙動
- データ整合性の保証