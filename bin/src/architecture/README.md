# Architecture Graph Database

このflakeの責務は、アーキテクチャをgraph dbで管理するためのスキーマ定義とusecaseとしてのdql充実徹底である

## 目的

- **DDL分離**: `requirement/graph`から独立したDDL管理
- **スキーマ統合**: 複数プロジェクトのスキーマを統一管理
- **DQLユースケース**: アーキテクチャ分析のためのクエリ充実

## 責務の境界

- **requirement/graph (DML側)**: データの格納・生成・URI生成まで
- **architecture (DQL側)**: 格納後のデータ利用・分析・洞察の導出

## ディレクトリ構造

```
architecture/
├── README.md                   # このファイル
├── ddl/                       # DDL定義（requirement/graphから移行予定）
│   ├── core/                  # コアスキーマ定義
│   │   ├── nodes/            # ノードテーブル定義
│   │   └── edges/            # エッジテーブル定義
│   ├── migrations/           # スキーママイグレーション
│   └── schema.cypher         # 統合スキーマ（自動生成）
├── dql/                      # DQLクエリ集
│   ├── analysis/             # 分析クエリ
│   ├── validation/           # 検証クエリ
│   └── reporting/            # レポート生成クエリ
└── infrastructure/           # インフラストラクチャコード
    ├── schema_manager.py     # スキーマ管理ツール
    └── query_runner.py       # クエリ実行ツール
```

## 移行戦略

1. **DDL完全分離**: requirement/graphのDDLを独立管理
2. **段階的移行**: 既存システムを稼働させたまま移行準備
3. **検証可能性**: 移行前後のスキーマ整合性を保証

## 使用方法

```bash
# スキーマ適用
python infrastructure/schema_manager.py apply

# DQL実行
python infrastructure/query_runner.py execute <query_name>
```