# ハイブリッド検索システム設計書

## 概要
search/vss（モック実装）とsearch/embeddings（実装済み）を統合し、ハイブリッド検索を実現する。

## 現状分析

### search/vss
- **実装方式**: モック実装（実際の埋め込みモデルなし）
- **ベクトル次元**: 384次元（ハードコード）
- **主な用途**: 要件管理システムの類似検索
- **特徴**: 軽量、テスト向け

### search/embeddings
- **実装方式**: 実際のモデル使用（Ruri v3）
- **ベクトル次元**: 256次元
- **主な用途**: 日本語文書の意味検索
- **特徴**: 本格的、プロダクション向け

## 統合アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    Hybrid Search API                     │
├─────────────────────────┬───────────────────────────────┤
│    Keyword Search       │      Vector Search            │
│   (Traditional BM25)    │    (Semantic Search)          │
├─────────────────────────┼───────────────────────────────┤
│                         │                               │
│   KuzuDB Cypher Query   │   Embedding Service           │
│                         │   ┌─────────────────┐         │
│                         │   │ Model Selector  │         │
│                         │   ├─────────────────┤         │
│                         │   │ • Ruri v3       │         │
│                         │   │ • Mock (test)   │         │
│                         │   └─────────────────┘         │
│                         │             ↓                 │
│                         │   KuzuDB VECTOR Extension     │
└─────────────────────────┴───────────────────────────────┘
                          ↓
              ┌────────────────────┐
              │   Result Fusion    │
              │  (Score Combiner)  │
              └────────────────────┘
```

## インターフェース設計

```python
class HybridSearchService:
    """ハイブリッド検索サービス"""
    
    def __init__(self, 
                 db_path: str,
                 embedding_model: str = "ruri-v3",
                 enable_keyword: bool = True,
                 enable_vector: bool = True):
        """
        Args:
            db_path: KuzuDBパス
            embedding_model: 使用する埋め込みモデル
            enable_keyword: キーワード検索を有効化
            enable_vector: ベクトル検索を有効化
        """
        pass
    
    def search(self,
               query: str,
               k: int = 10,
               keyword_weight: float = 0.3,
               vector_weight: float = 0.7) -> List[SearchResult]:
        """
        ハイブリッド検索を実行
        
        Args:
            query: 検索クエリ
            k: 返却件数
            keyword_weight: キーワード検索の重み
            vector_weight: ベクトル検索の重み
        
        Returns:
            統合された検索結果
        """
        pass
```

## データモデル

```python
@dataclass
class SearchResult:
    id: str
    content: str
    keyword_score: Optional[float]  # BM25スコア
    vector_score: Optional[float]   # コサイン類似度
    combined_score: float           # 統合スコア
    metadata: Dict[str, Any]
```

## 実装方針

1. **段階的統合**
   - Phase 1: 共通インターフェースの定義
   - Phase 2: embeddings側をプライマリ実装として使用
   - Phase 3: キーワード検索の追加
   - Phase 4: スコア統合アルゴリズムの実装

2. **互換性維持**
   - 既存のvss/embeddingsモジュールは独立して動作可能
   - 新しいhybridモジュールが両者を統合

3. **テスト戦略**
   - 単体テスト: 各検索方式を個別にテスト
   - 統合テスト: ハイブリッド検索全体をテスト
   - パフォーマンステスト: 大規模データでの性能確認

## ディレクトリ構造

```
search/
├── vss/           # 既存（モック実装）
├── embeddings/    # 既存（本実装）
├── hybrid/        # 新規（統合層）
│   ├── __init__.py
│   ├── service.py
│   ├── models.py
│   ├── keyword_search.py
│   ├── vector_search.py
│   └── score_fusion.py
└── tests/         # 統合テスト
    └── test_hybrid_search.py
```