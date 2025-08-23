# kuzu_sqlite

## 責務

このディレクトリは以下の責務を持つPOC（Proof of Concept）です：

1. **SQLite永続化**: データをSQLiteデータベースに永続化する
2. **KuzuDB連携**: SQLiteをKuzuDBにアタッチすることでCypherクエリを実行可能にする

## 目的

SQLiteの安定した永続化機能とKuzuDBのグラフクエリ機能を組み合わせることで、以下を実現します：

- リレーショナルデータのグラフDB表現
- Cypherクエリによる柔軟なデータ探索
- SQLiteの信頼性とKuzuDBの表現力の両立

## 技術スタック

- **SQLite**: 永続化層
- **KuzuDB**: グラフクエリエンジン
  - CLIツール版: `nixpkgs#kuzu`
  - TypeScript版: `bin/src/persistence/kuzu_ts/bun`
- **Cypher**: クエリ言語
- **Bun**: TypeScript実行環境（最小動作確認用）

## 使用方法

### 1. 完全な例の実行

SQLiteデータベースの作成からKuzuDBでのクエリ実行まで：

```bash
./example_attach.sh
```

このスクリプトは以下を実行します：
- SQLiteデータベースの作成（学生、コース、履修データ）
- KuzuDBへのアタッチ
- データのクエリとグラフ構造への変換

### 2. 既存SQLiteデータベースへのクエリ

インタラクティブモード：

```bash
./simple_query.sh ./data/university.db
```

### 3. バッチクエリの実行

Cypherファイルを使用したバッチ実行：

```bash
./batch_query.sh ./data/university.db ./queries/sample_analysis.cypher
```

### 4. Bun版の最小動作確認

TypeScriptとBunを使用した軽量版：

```bash
# 直接実行
bun run simple_attach_bun.ts

# またはシェルスクリプト経由
./minimal_attach_bun.sh
```

## ファイル構成

```
kuzu_sqlite/
├── README.md                      # このファイル
├── example_attach.sh              # 完全な実行例（CLI版）
├── simple_query.sh                # インタラクティブクエリツール
├── batch_query.sh                 # バッチクエリ実行ツール
├── test_integration.sh            # 統合テスト
├── simple_attach_bun.ts           # Bun版の簡易実行例
├── minimal_attach_bun.sh          # Bun版の最小テスト
├── queries/
│   └── sample_analysis.cypher    # サンプル分析クエリ
├── data/                          # データディレクトリ（実行時に作成）
│   ├── university.db              # SQLiteデータベース
│   └── kuzu_db/                   # KuzuDBデータベース
├── data_bun/                      # Bun版データディレクトリ
└── docs/                          # ドキュメント
    └── *_sqlite-extension.md      # KuzuDB SQLite拡張のドキュメント
```

## 必要なツール

すべてのスクリプトは`nix shell`を使用して必要なツールを自動的に提供します：

- `sqlite3`: SQLiteのCLI
- `kuzu`: KuzuDBのCLI

手動で環境を構築する場合：

```bash
nix shell nixpkgs#sqlite nixpkgs#kuzu
```