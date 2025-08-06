# KuzuDBネイティブなマイグレーションワークフロー

## 概要
KuzuDBの`EXPORT DATABASE`/`IMPORT DATABASE`機能を活用した、より実践的なマイグレーションワークフローを定義します。

## ワークフロー

### 1. 開発フェーズ（現在の構造を活用）

```
architecture/
├── ddl/
│   ├── core/                 # 開発時のスキーマ定義
│   │   ├── nodes/           # モジュラーな管理
│   │   └── edges/           
│   └── schema.cypher        # 自動生成された統合スキーマ
```

**利点**:
- モジュラーな開発が可能
- Gitでの差分管理が容易
- レビューしやすい構造

### 2. エクスポートフェーズ（KuzuDBネイティブ）

```bash
# 開発環境からエクスポート
EXPORT DATABASE '/home/nixos/bin/src/architecture/migrations/v4.1.0' (format="parquet");
```

生成されるファイル:
```
migrations/
└── v4.1.0/
    ├── schema.cypher    # KuzuDBが生成する完全スキーマ
    ├── macro.cypher     # マクロ定義
    ├── copy.cypher      # データインポート文
    └── *.parquet        # データファイル
```

### 3. バージョン管理フェーズ

```
migrations/
├── v4.0.0/              # 初期バージョン
│   └── schema.cypher    
├── v4.1.0/              # 機能追加
│   ├── schema.cypher
│   └── CHANGELOG.md     # 変更内容の記録
└── current -> v4.1.0/   # シンボリックリンク
```

### 4. デプロイフェーズ

```bash
# 新環境へのインポート
IMPORT DATABASE '/home/nixos/bin/src/architecture/migrations/v4.1.0';
```

## 改訂されたディレクトリ構造

```
architecture/
├── ddl/                      # 開発用スキーマ定義
│   ├── core/
│   │   ├── nodes/
│   │   └── edges/
│   └── schema.cypher         # 開発用統合スキーマ
├── migrations/               # KuzuDBエクスポート
│   ├── v4.0.0/
│   │   ├── schema.cypher    # KuzuDB生成
│   │   ├── macro.cypher
│   │   └── copy.cypher
│   ├── v4.1.0/
│   │   └── ...
│   └── current -> v4.1.0/
├── dql/                      # クエリ集
└── infrastructure/
    ├── schema_manager.py     # 開発用ツール
    ├── migration_tool.py     # 新規：マイグレーション支援
    └── query_runner.py

```

## migration_tool.pyの機能

```python
# 使用例
python infrastructure/migration_tool.py export --version v4.1.0
python infrastructure/migration_tool.py import --version v4.1.0
python infrastructure/migration_tool.py diff v4.0.0 v4.1.0
python infrastructure/migration_tool.py rollback v4.0.0
```

## ワークフローの利点

1. **開発効率**: `ddl/core/`でモジュラー開発
2. **KuzuDB準拠**: ネイティブ機能で確実な移行
3. **バージョン管理**: エクスポートごとに完全な状態を保存
4. **ロールバック**: 任意のバージョンに戻せる
5. **差分確認**: バージョン間の変更を追跡可能

## 移行シナリオ

### A. 通常のスキーマ更新
1. `ddl/core/`でスキーマを修正
2. `schema_manager.py`で統合スキーマ生成
3. テスト環境で検証
4. `EXPORT DATABASE`で新バージョン作成
5. 本番環境で`IMPORT DATABASE`

### B. 緊急ロールバック
1. 問題のあるバージョンを特定
2. 前バージョンのディレクトリを指定
3. `IMPORT DATABASE`で即座に復元

### C. 環境間の同期
1. 本番環境から`EXPORT DATABASE`
2. 開発環境で`IMPORT DATABASE`
3. 完全に同じ状態で検証可能

## requirement/graphとの互換性

requirement/graphの移行も同じワークフローで実施可能:

```bash
# requirement/graphからエクスポート
cd /home/nixos/bin/src/requirement/graph
EXPORT DATABASE '../architecture/migrations/from_requirement_graph';

# architectureへインポート
cd /home/nixos/bin/src/architecture
IMPORT DATABASE './migrations/from_requirement_graph';
```

これにより、実データを含めた完全な移行が可能です。