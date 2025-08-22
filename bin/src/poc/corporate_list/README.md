# Corporate List - 国内法人データベース

## 概要
法人番号公表サイトAPIを使用して、国内の全法人リストをDuckDBに格納・管理するシステムです。

## 技術スタック
- **Nix Flakes**: 再現可能な開発環境
- **Node.js 22**: APIクライアント実装
- **DuckDB**: 高速な分析用データベース

## 主な機能
- 法人番号公表サイトAPIからの法人データ取得
- DuckDBへの効率的なデータ格納
- 法人情報の検索・分析機能

## セットアップ

### 前提条件
- Nix with Flakes enabled
- 法人番号公表サイトAPIアクセス権限

### インストール
```bash
# 開発環境の起動
nix develop

# 依存関係のインストール
npm install
```

## 使用方法

### スクレイピング実行
```bash
# デフォルト（TypeScript実装）
npm run scrape

# レガシー実装を使用
USE_LEGACY=true npm run scrape

# Nix環境での実行
nix run .#scrape

# シェルスクリプト経由での実行
./run-scraper.sh
USE_LEGACY=true ./run-scraper.sh
```

### 実装の切り替え（Production Migration）

本プロジェクトは安全な本番移行のために、2つの実装を並行実行できる切り替え機能を提供しています：

1. **TypeScript実装**（推奨・デフォルト）: `src/main.ts`
   - モジュール化された設計
   - 型安全性
   - テスト可能な構造

2. **レガシー実装**: `scrape.mjs`
   - 元の単一ファイル実装
   - 既存の動作を保持

#### 切り替え方法

**環境変数による切り替え:**
```bash
# TypeScript実装（デフォルト）
npm run scrape

# レガシー実装
USE_LEGACY=true npm run scrape
```

**直接実行:**
```bash
# TypeScript実装
npm run scrape:ts

# レガシー実装
npm run scrape:legacy
```

#### 移行テスト

両実装の互換性を確認するテストを実行：
```bash
# 移行テストのみ
npm run test:migration

# 全テスト実行
npm run test:all
```

#### ロールバック手順

問題が発生した場合、即座にレガシー実装に戻せます：
```bash
USE_LEGACY=true npm run scrape
```

### データの取得（将来実装予定）
```bash
# 全法人データの初期取得
npm run fetch:initial

# 差分更新
npm run fetch:update
```

### データベース操作
```bash
# DuckDBコンソールの起動
npm run db:console

# クエリ実行例
npm run query -- "SELECT * FROM corporations WHERE name LIKE '%株式会社%' LIMIT 10"
```

## データ構造

### corporations テーブル
| カラム名 | 型 | 説明 |
|---------|-----|------|
| corporate_number | VARCHAR | 法人番号（13桁） |
| name | VARCHAR | 法人名 |
| address | VARCHAR | 本店所在地 |
| prefecture | VARCHAR | 都道府県 |
| city | VARCHAR | 市区町村 |
| kind | INTEGER | 法人種別 |
| update_date | DATE | 更新年月日 |
| change_date | DATE | 変更年月日 |
| process | INTEGER | 処理区分 |

## API仕様
法人番号公表サイトAPI（国税庁）の仕様に準拠しています。
- エンドポイント: https://api.houjin-bangou.nta.go.jp/
- レート制限: 適切な間隔での実行を推奨

## 開発

### ディレクトリ構造
```
corporate_list/
├── flake.nix              # Nix開発環境定義
├── package.json           # Node.js依存関係
├── scrape.mjs             # レガシー実装（単一ファイル）
├── scripts/
│   └── switchover.mjs     # 実装切り替えスクリプト
├── src/                   # TypeScript実装
│   ├── domain/
│   │   ├── scraper.ts     # スクレイピングロジック
│   │   ├── extractor.ts   # データ抽出ロジック
│   │   └── types.ts       # 型定義
│   ├── infrastructure/
│   │   └── browser.ts     # ブラウザ管理
│   ├── main.ts            # メインエントリーポイント
│   └── variables.ts       # 設定管理
├── test/                  # テストファイル
│   ├── migration.test.ts  # 移行テスト
│   └── ...               # その他のテスト
└── README.md              # このファイル
```

### 技術的詳細

#### 切り替え機能の仕組み

1. **switchover.mjs**: 環境変数 `USE_LEGACY` を検査して適切な実装を起動
2. **同一の出力形式**: 両実装とも同じJSON形式で結果を出力
3. **環境変数の継承**: 全ての環境変数が子プロセスに継承される
4. **シグナル処理**: SIGINT/SIGTERMを適切に子プロセスに転送

#### 出力形式の互換性

両実装は以下の形式でデータを出力します：
```json
[
  {
    "source": "PR_TIMES",
    "company_name": "株式会社Example",
    "title": "記事タイトル",
    "url": "https://example.com/article",
    "scraped_at": "2025-08-22T12:34:56.789Z"
  }
]
```

### テスト
```bash
npm test
```

### ビルド
```bash
npm run build
```

## ライセンス
MIT

## 注意事項
- 法人番号公表サイトの利用規約を遵守してください
- 大量データ取得時は適切な間隔を設けてください
- 個人情報の取り扱いには十分注意してください