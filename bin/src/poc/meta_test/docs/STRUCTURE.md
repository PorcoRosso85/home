# メタテストシステム完成形の構造

## 概要
テストの品質を7つの独立指標で評価し、継続的に学習・改善するシステム

## 7つの独立指標
1. **existence** - テスト存在率（要件に対するテストの存在割合）
2. **reachability** - 到達可能性（循環参照なく実行可能か）
3. **boundary_coverage** - 境界値網羅度（閾値の前後をテストしているか）
4. **change_sensitivity** - 変更感度（要件変更時に失敗するか）
5. **semantic_alignment** - 意味的一致度（要件とテストの説明の類似度）
6. **runtime_correlation** - 実行時相関（テスト成功率と運用指標の相関）
7. **value_probability** - 価値貢献確率（ビジネス目標達成への寄与確率）

## ディレクトリ構造

```
meta_test/
├── docs/
│   ├── EXAMPLE.md                    # 議論の記録
│   ├── STRUCTURE.md                  # 本ファイル
│   └── METRICS.md                    # 7指標の詳細定義
│
├── domain/
│   ├── metrics/                      # 7つの独立指標
│   │   ├── existence.py              # 1. テスト存在率
│   │   ├── test_existence.py
│   │   ├── reachability.py           # 2. 到達可能性
│   │   ├── test_reachability.py
│   │   ├── boundary_coverage.py      # 3. 境界値網羅度
│   │   ├── test_boundary_coverage.py
│   │   ├── change_sensitivity.py     # 4. 変更感度
│   │   ├── test_change_sensitivity.py
│   │   ├── semantic_alignment.py     # 5. 意味的一致度
│   │   ├── test_semantic_alignment.py
│   │   ├── runtime_correlation.py    # 6. 実行時相関
│   │   ├── test_runtime_correlation.py
│   │   ├── value_probability.py      # 7. 価値貢献確率
│   │   └── test_value_probability.py
│   │
│   └── learning/
│       ├── correlation_updater.py    # ベイズ更新（指標6,7用）
│       └── test_correlation_updater.py
│
├── application/
│   ├── calculate_metrics.py          # 全指標の計算
│   ├── test_calculate_metrics.py
│   ├── improve_suggestions.py        # 改善提案生成
│   ├── test_improve_suggestions.py
│   └── learn_from_runtime.py         # 実行時学習
│
├── infrastructure/
│   ├── graph_adapter.py              # KuzuDB接続
│   ├── test_graph_adapter.py
│   ├── embedding_service.py          # 意味的一致度用
│   ├── test_embedding_service.py
│   ├── metrics_collector.py          # 実行時データ収集
│   └── cypher_writer.py              # 学習結果永続化
│
├── data/
│   ├── schema/
│   │   └── meta_test_schema.cypher   # 7指標のスキーマ
│   │
│   ├── initial/
│   │   └── 001_baseline_values.cypher # 初期ベースライン
│   │
│   └── learning/
│       └── daily/                    # 日次学習結果
│           └── 2024-01-20.cypher
│
├── examples/
│   └── payment_duplicate/
│       └── all_metrics.cypher        # 7指標すべての例
│
├── e2e/
│   ├── internal/
│   │   ├── test_e2e_existence_reachability.py
│   │   ├── test_e2e_boundary_sensitivity.py
│   │   ├── test_e2e_semantic_runtime.py
│   │   └── test_e2e_value_learning.py
│   │
│   └── external/
│       └── test_e2e_full_metrics_cycle.py
│
├── scripts/
│   ├── init_metrics.py               # 初期化
│   ├── calculate_all.py              # 全指標計算
│   └── daily_learning.py             # 学習実行
│
├── pyproject.toml
├── __main__.py                       # CLIエントリーポイント
└── README.md
```

## データフロー

```
requirement/graph（既存の要件グラフ）
         ↓
    7指標の並列計算
         ↓
    改善提案の生成
         ↓
実行時データ収集（指標6,7のみ）
         ↓
    学習による更新
         ↓
  Cypherファイルで永続化
         ↓
    GraphDBに反映
```

## 設計原則

1. **カテゴライズなし** - 7つの指標は独立して存在し、グループ化しない
2. **責務の独立性** - 各指標は他の指標では測れない固有の責務を持つ
3. **学習の限定** - 実行時データが必要な指標6,7のみ学習対象
4. **Cypher永続化** - すべてのデータ変更はCypherファイルとして記録
5. **既存資産の活用** - requirement/graphのスキーマとデータを再利用

## 使用方法

```bash
# 初期化
python -m meta_test init

# 全指標の計算
python -m meta_test calculate --requirement-id req_001

# 特定指標のみ
python -m meta_test check existence
python -m meta_test check boundary_coverage

# 改善提案
python -m meta_test suggest --threshold 0.7

# 学習実行（日次）
python -m meta_test learn
```

## 拡張性

新しい評価観点が必要になった場合：
1. 既存7指標で表現できないことを証明
2. 8つ目の指標として domain/metrics/ に追加
3. 既存指標の再定義やカテゴライズは不要