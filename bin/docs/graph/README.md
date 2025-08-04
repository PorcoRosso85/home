# Flake Responsibility Graph

## 目的
bin/src配下の各flakeの責務を探索可能にし、プロジェクト全体の構造を可視化する。

## ビジネス価値

### 解決する課題
1. **重複実装の見逃し**
   - 説明文は異なるが同じ機能を実装している場合の発見困難性
   - 例: "Vector Search"と"ベクトル検索"のような表記揺れ

2. **責務の重複と分散**
   - 似た名前だが異なる実装の識別困難性
   - 例: kuzu_py vs kuzu_ts（同じDB、異なる言語バインディング）

### 期待される効果とROI

#### 開発効率の向上
- **重複コード削減**: 15-30%のコード量削減
- **調査時間短縮**: 新規実装時の既存コード調査時間を50%削減
- **メンテナンス効率化**: バグ修正箇所の一元化による保守工数削減

#### アーキテクチャ品質の向上
- **検出可能な問題**:
  - 意味的に同じだがコードが異なる実装（標準化の機会）
  - コードは似ているが目的が異なる実装（責務分離の必要性）
  - 両方が類似している実装（統合候補）

### 具体的なユースケース

**新規flake作成時の重複防止**:
```bash
$ flake-graph check-before-create "新しいログ機能"
警告: 類似flakeが存在:
- telemetry/log_py (説明: 85%, コード: 該当なし)
- monitoring/logger (説明: 70%, コード: 該当なし)
推奨: 既存flakeの拡張を検討
```

**リファクタリング機会の発見**:
```bash
$ flake-graph analyze . --architecture
アーキテクチャ健全性: 0.75/1.0
重複グループ発見:
1. DB接続系 (3 flakes)
   - 意味的類似度: 85% (VSS)
   - 構造的類似度: 90% (AST - 未実装)
   - 推奨: 共通ライブラリ化で500行削減可能
```

## 価値
- **構造理解**: 開発者が大規模なコードベースの全体像を把握できる
- **依存関係の可視化**: flake間の依存関係を明確に理解できる
- **責務の明確化**: 各flakeが何を担当しているかを素早く検索・理解できる
- **アーキテクチャ分析**: カテゴリ別・言語別の統計でプロジェクトの傾向を把握できる

## 機能
- 各flakeのflake.nixから責務情報を自動抽出
- KuzuDBを使用したグラフ構造での永続化
- 責務に基づいた検索・フィルタリング機能
- 依存関係の双方向探索（依存先・依存元）
- カテゴリ別・言語別の統計表示
- VSS（ベクトル類似検索）による意味的類似性分析
- AST分析によるコード構造類似性検出（開発中）

## 使用技術
- Nix Flakes
- KuzuDB (グラフデータベース)
- Python (データ処理・API)
- flakes/python環境の継承
- persistence/kuzu_py
- telemetry/log_py
- search/vss_kuzu (ベクトル類似検索)
- poc/similarity (コード構造分析・将来統合予定)

## 現在の実装状況

### 実装済み機能
1. **VSS（Vector Similarity Search）分析**
   - flakeの説明文とREADMEに基づく意味的類似性検出
   - 日本語/英語の表記揺れ対応（例: "ベクトル検索" ↔ "Vector Search"）
   - Complete-linkageクラスタリングによる重複グループ検出（閾値: 0.9）

2. **基本的なflake分析**
   - flake.nixからのメタデータ自動抽出
   - README.md欠落検出とアラート
   - 依存関係の双方向グラフ構築

### 未実装・開発中機能
1. **AST（Abstract Syntax Tree）分析**
   - similarityツールとの統合準備中
   - コードレベルの構造的類似性検出
   - 言語別（TypeScript/Python/Rust）の対応

2. **永続化機能**
   - 現状: 毎回メモリ内でVSSインデックス作成
   - 計画: KuzuDBへのembedding永続化

## VSS Persistence Implementation Progress

### What Has Been Implemented
1. **Embedding Extraction**: 
   - Automated extraction of text from flake descriptions and README files
   - Generation of embeddings using sentence-transformers
   - Support for Japanese/English mixed content

2. **Persistence Functions**:
   - Core persistence layer for storing embeddings in KuzuDB
   - Schema design for VSS data (embeddings, metadata)
   - Basic CRUD operations for embedding management

### Current Status
- **Tests Written**: Comprehensive test suite covering persistence layer
- **Partial Implementation**: Core functions implemented but not yet integrated with main application
- **Infrastructure Ready**: KuzuDB schema and data models in place

### Performance Goals
- **90% reduction in startup time** after initial embedding generation
- From ~30 seconds (current) to ~3 seconds for subsequent runs
- Incremental updates only for changed flakes

### Next Steps Needed
1. **Integration**: Connect persistence layer to main analysis workflow
2. **Cache Management**: Implement change detection for incremental updates
3. **Performance Testing**: Validate 90% improvement target with real data
4. **Error Handling**: Add resilience for partial persistence failures

## 今後の開発方針

### Phase 1: VSS永続化（現在）
**目的**: 大規模コードベースでの実用性確保
- VSSのembeddingをKuzuDBに永続化
- 初回実行後は90%以上の起動時間短縮
- 更新検知による差分インデックス

### Phase 2: GraphDBスキーマ拡張
**目的**: 分析結果の個別管理と柔軟な活用
```cypher
CREATE NODE Flake {
    path: STRING PRIMARY KEY,
    description: STRING,
    language: STRING,
    // 分析結果を個別属性として管理
    vss_score: FLOAT,
    vss_embedding: LIST[FLOAT],
    ast_score: FLOAT,
    ast_metrics: MAP
}
```

### Phase 3: 並行分析アーキテクチャ
**目的**: VSS/AST分析の独立実行と部分的失敗への耐性
- VSS分析とAST分析を並行実行
- 片方が失敗しても他方の結果は保存
- 分析タイプ別の実行タイミング制御

### Phase 4: 統合分析ビュー
**目的**: 複合的なアーキテクチャ健全性評価
- VSS（意味）とAST（構造）の統合スコア算出
- 時系列でのコード品質追跡
- CI/CDパイプラインへの組み込み

## 設計原則

1. **段階的な価値提供**
   - 各フェーズで独立した価値を提供
   - 後方互換性を維持しながら機能拡張

2. **疎結合アーキテクチャ**
   - VSS/AST/GraphDBは独立したコンポーネント
   - アダプターパターンによる統合

3. **実用性優先**
   - 完璧な分析より高速な応答
   - 部分的な分析結果でも価値を提供

## 使用方法

### 基本的な分析
```bash
# flake情報の分析と可視化
nix run . -- analyze /home/nixos/bin/src

# README欠落チェック
nix run . -- check-readme /home/nixos/bin/src

# 重複flake検出
nix run . -- detect-duplicates /home/nixos/bin/src
```

### アーキテクチャ分析（VSS実装済み、AST開発中）
```bash
# 統合分析の実行
nix run . -- analyze /home/nixos/bin/src --architecture

# JSON形式での出力
nix run . -- analyze /home/nixos/bin/src --json
```

### データエクスポート
```bash
# 基本的なエクスポート（全flake情報をJSON形式で出力）
nix run . -- export /home/nixos/bin/src

# 言語フィルタ付きエクスポート
nix run . -- export /home/nixos/bin/src --language python
nix run . -- export /home/nixos/bin/src --language typescript

# embedding含むエクスポート（VSS分析用）
nix run . -- export /home/nixos/bin/src --include-embeddings
```

### 出力JSONの構造
```json
{
  "flakes": [
    {
      "path": "/path/to/flake",
      "name": "flake_name",
      "description": "flakeの説明",
      "language": "python",
      "category": "persistence",
      "dependencies": ["dep1", "dep2"],
      "readme_content": "READMEの内容（存在する場合）",
      "embedding": [0.1, 0.2, ...] // --include-embeddingsオプション使用時のみ
    }
  ],
  "statistics": {
    "total_flakes": 42,
    "by_language": {
      "python": 20,
      "typescript": 15,
      "rust": 7
    },
    "by_category": {
      "persistence": 8,
      "search": 5,
      "telemetry": 4
    }
  },
  "metadata": {
    "generated_at": "2024-01-20T10:30:00Z",
    "base_path": "/home/nixos/bin/src",
    "version": "1.0.0"
  }
}

## 開発環境
```bash
# 開発シェルに入る
nix develop

# テストの実行
pytest -v

# 特定のテストのみ実行
pytest tests/e2e/internal/test_architecture_analysis.py -v
```