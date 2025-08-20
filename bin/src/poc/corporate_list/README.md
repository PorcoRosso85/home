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

### データの取得
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
├── flake.nix          # Nix開発環境定義
├── package.json       # Node.js依存関係
├── src/              # ソースコード
│   ├── api/          # API クライアント
│   ├── db/           # DuckDB操作
│   └── utils/        # ユーティリティ
├── data/             # データ格納ディレクトリ
│   └── corporate.db  # DuckDBデータベース
└── README.md         # このファイル
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