# Search POC アーキテクチャ

## 概要

このPOCは、KuzuDBのネイティブVSS（Vector Similarity Search）とFTS（Full-Text Search）機能を使用した、要件管理システムの検索機能を実証します。

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    Search POC                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐ │
│  │     VSS     │  │     FTS     │  │    Graph      │ │
│  │  (Vector)   │  │   (Text)    │  │  (Relations)  │ │
│  └──────┬──────┘  └──────┬──────┘  └───────┬───────┘ │
│         │                 │                  │         │
│         └─────────────────┴──────────────────┘         │
│                           │                             │
│                    ┌──────┴──────┐                    │
│                    │   KuzuDB    │                    │
│                    │  Database   │                    │
│                    └─────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## コンポーネント

### 1. Vector Similarity Search (VSS)
- **目的**: 意味的に類似した要件を検索
- **技術**: KuzuDB VECTOR拡張機能
- **機能**:
  - 384次元の埋め込みベクトル
  - HNSWアルゴリズムによる高速検索
  - コサイン類似度による順位付け

### 2. Full-Text Search (FTS)
- **目的**: キーワードベースの高速検索
- **技術**: KuzuDB FTS拡張機能
- **機能**:
  - 日本語トークナイズ対応
  - 部分一致検索
  - TF-IDFスコアリング

### 3. Graph Traversal
- **目的**: 要件間の依存関係分析
- **技術**: KuzuDB Cypher
- **機能**:
  - 依存関係の探索
  - 影響範囲の特定
  - 循環参照の検出

## ユースケース

### 1. 重複要件検出
```python
# 新規要件追加時の重複チェック
def detect_duplicates(new_requirement):
    # 1. VSSで類似要件を検索
    similar = vss_search(new_requirement, threshold=0.8)
    
    # 2. 重複の可能性を警告
    if similar:
        alert_teams(similar)
```

### 2. 変更影響分析
```python
# 要件変更時の影響範囲特定
def analyze_impact(changed_requirement):
    # 1. グラフで直接依存を探索
    direct = graph_traverse(changed_requirement)
    
    # 2. VSSで意味的関連を発見
    semantic = vss_search(changed_requirement)
    
    return merge_results(direct, semantic)
```

### 3. 用語統一性チェック
```python
# プロジェクト全体の用語統一
def check_terminology():
    # 1. FTSで表記揺れを検出
    variations = fts_find_variations()
    
    # 2. VSSで同義語を発見
    synonyms = vss_find_synonyms()
    
    return suggest_unification(variations, synonyms)
```

## テスト戦略

### 仕様テスト（Specification Tests）
- **ファイル**: `test_search_poc_spec.py`
- **内容**: 実行可能な仕様書として機能
- **特徴**: ビジネス価値を明確化

### 統合テスト（Integration Tests）
- **ファイル**: `test_kuzu_vss_fts_integration.py`
- **内容**: KuzuDB機能の実装例
- **特徴**: 最小限の動作確認

### E2Eテスト（End-to-End Tests）
- **ファイル**: `test_hybrid_search_e2e.py`
- **内容**: 実際のシナリオ検証
- **特徴**: ユーザー視点での価値確認

## 実装ガイドライン

### 規約遵守
1. **関数型設計**: クラスの使用禁止
2. **エラーハンドリング**: Result型パターン
3. **複雑度管理**: 各関数は10行以内
4. **モック最小化**: KuzuDBネイティブ機能を使用

### パフォーマンス目標
- 検索レスポンス: < 100ms
- インデックス作成: < 1秒/1000件
- メモリ使用量: < 1GB

### 成功基準
- 重複検出率: > 90%
- 検索精度: > 85%
- ユーザー満足度: > 4.0/5.0

## 今後の展開

1. **実装フェーズ**
   - KuzuDB拡張機能の実装
   - 日本語埋め込みモデルの統合
   - UIの構築

2. **評価フェーズ**
   - 実データでの性能測定
   - ユーザビリティテスト
   - フィードバック収集

3. **本番展開**
   - スケーラビリティ対策
   - 監視・運用体制
   - 継続的改善