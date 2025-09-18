# 環境変数設計

## 概要
すべての環境変数は`src/infrastructure/config/variables.ts`で一元管理されます。
build.tsはデフォルト値を持たず、環境変数をそのまま渡します。

## 必要な環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| LOG_LEVEL | 3 | ログレベル (0-5) |
| NODE_ENV | development | 実行環境 |
| API_HOST | localhost | APIホスト |
| API_PORT | 3000 | APIポート |
| DB_PATH | ./kuzu.db | データベースパス |

## 起動例

### 最小構成（デフォルト値を使用）
```bash
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH \
nix run nixpkgs#deno -- run -A build.ts
```

### フル設定
```bash
LOG_LEVEL=5 \
NODE_ENV=production \
API_HOST=api.example.com \
API_PORT=8080 \
DB_PATH=/var/lib/kuzu/prod.db \
LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH \
nix run nixpkgs#deno -- run -A build.ts \
--mount /home/nixos/bin/src/kuzu/query/ddl:/ddl:*.cypher
```

## アーキテクチャ

```
build.ts (外部入力)
  ↓ 環境変数をそのまま渡す
Vite define設定
  ↓ ビルド時に置換
variables.ts (インフラ層)
  ↓ 検証・デフォルト値設定
アプリケーション層
```
