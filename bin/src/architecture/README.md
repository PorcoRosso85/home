# Architecture Graph Database

すべてのGraphDB関連機能（DDL/DML/DQL）を統合管理するアーキテクチャセンター

## 目的

- **統合管理**: DDL（スキーマ定義）、DML（データ操作）、DQL（データ照会）の一元化
- **責務分離**: 各機能を明確に分離し、単一責務の原則を徹底
- **再利用性**: 共通機能の集約により、コードの重複を排除

## 正規化後の完全構造

### ディレクトリ構造（移行後）

```
architecture/
├── README.md                          # このファイル
├── ddl/                              # スキーマ定義層
│   ├── migrations/                   # マイグレーション管理
│   └── schemas/                      # スキーマ定義
├── dml/                              # データ操作層
│   ├── requirement/                  # 要件データ入力（人間から）
│   │   ├── application/              # ※requirement/graphから移行
│   │   │   └── template_processor.py
│   │   ├── domain/
│   │   │   └── requirement_entity.py
│   │   └── infrastructure/
│   │       └── kuzu_repository.py
│   └── implementation/               # 実装データ収集（ファイルから）
│       ├── scanner.py                # ※docs/graph/flake_graphから移行
│       └── infrastructure/
│           └── kuzu_writer.py
└── dql/                              # データ照会層（フラット構造）
    ├── find_duplicates.cypher        # 重複検出
    ├── check_circular_deps.cypher    # 循環依存検証
    ├── search_requirements.cypher    # 要件検索
    ├── search_implementations.cypher # 実装検索
    ├── analyze_dependencies.cypher   # 依存関係分析
    ├── project_stats.cypher          # プロジェクト統計
    ├── export_graph.cypher           # グラフエクスポート
    ├── validate_boundaries.cypher    # 境界検証
    └── generate_reports.cypher       # レポート生成
```

### 移行前後の対応関係

```
【移行前】                           【移行後】
requirement/graph/                → architecture/dml/requirement/
  - DQL機能を除去                    - 純粋なDML機能のみ

docs/graph/flake_graph/          → architecture/dml/implementation/
  - DQL機能を除去                    - 純粋なDML機能のみ
  - 名称変更で役割明確化

両プロジェクトのDQL機能         → architecture/dql/*.cypher
  - Pythonコードから抽出            - Cypherテンプレートとして再実装
  - 階層構造を撤廃                  - フラット構造で管理
```

## 外部依存関係

```nix
inputs = {
  # 基本依存
  nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  flake-utils.url = "github:numtide/flake-utils";

  # Python開発環境
  python-flake.url = "path:../flakes/python";

  # データベース層
  kuzu-py.url = "path:../persistence/kuzu_py";  # KuzuDB Pythonバインディング

  # ロギング層
  log-py.url = "path:../telemetry/log_py";      # 構造化ロギング

  # 検索層
  vss-kuzu.url = "path:../search/vss_kuzu";     # ベクトル類似検索
  fts-kuzu.url = "path:../search/fts_kuzu";     # 全文検索

  # 分析層（オプション）
  similarity.url = "path:../poc/similarity";     # AST分析・コード構造類似性
};
```

### 依存関係の使用箇所

- **kuzu-py**: すべてのDML/DQLで使用（DB接続・操作）
- **log-py**: 全モジュールでロギングに使用
- **vss-kuzu**: requirement検索、implementation類似性分析で使用
- **fts-kuzu**: requirement検索で使用
- **similarity**: implementationのAST分析で使用（将来統合予定）

## 責務の明確化

### DML（Data Manipulation Language）
- **requirement/**: 人間からの要件データ入力
  - JSON APIによるテンプレート入力
  - 要件エンティティの管理
- **implementation/**: ファイルシステムからの実装データ収集
  - flake.nixスキャン
  - README抽出
  - 自動インデックス生成

### DQL（Data Query Language）
- すべてのクエリをCypherファイルとして管理
- 複雑なロジックはquery_runner.pyで処理
- 純粋な宣言的クエリのみを保持

### DDL（Data Definition Language）
- スキーマの一元管理
- マイグレーション戦略の統一
- kuzu-migrationツールでの管理

## 使用方法

```bash
# スキーマ適用
python infrastructure/schema_manager.py apply

# DQL実行
python infrastructure/query_runner.py execute <query_name>
```