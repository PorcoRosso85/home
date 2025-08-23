# kuzu_sqlite

## 責務

このディレクトリは以下の責務を持つPOC（Proof of Concept）です：

1. **SQLite永続化**: データをSQLiteデータベースに永続化する
2. **KuzuDB連携**: SQLiteをKuzuDBにアタッチすることでCypherクエリを実行可能にする
3. **グラフクエリ実証**: リレーショナルデータをグラフ構造として探索・分析

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

### 5. グラフクエリデモ

ソーシャルネットワークデータでグラフ探索を実演：

```bash
./graph_query_demo.sh
```

このデモでは以下を確認できます：
- リレーショナルデータからグラフ構造への変換
- 複雑なパターンマッチング（相互フォロー、共通フォロワーなど）
- グラフ探索（最短パス、nホップ接続）
- グラフ分析（インフルエンサー検出、コミュニティ検出）

## ファイル構成

```
kuzu_sqlite/
├── README.md                      # このファイル
├── example_attach.sh              # 完全な実行例（CLI版）
├── simple_query.sh                # インタラクティブクエリツール
├── batch_query.sh                 # バッチクエリ実行ツール
├── graph_query_demo.sh            # グラフクエリデモ
├── test_integration.sh            # 統合テスト
├── simple_test_cli.sh             # 簡易CLIテスト
├── simple_attach_bun.ts           # Bun版の簡易実行例
├── minimal_attach_bun.sh          # Bun版の最小テスト
├── queries/
│   ├── sample_analysis.cypher    # サンプル分析クエリ
│   └── graph_patterns.cypher     # グラフパターンマッチング例
├── flake.nix                      # Nix環境設定
├── .gitignore                     # Git除外設定
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