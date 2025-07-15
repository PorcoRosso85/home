# VSS統合リファクタリング計画

## 概要
search/embeddingsの実装をsearch/vssに統合し、統一されたベクトル検索システムを構築する。

## Phase 1: インターフェース統一（互換性維持）

### 1.1 共通インターフェース定義
```python
# search/vss/core/interfaces.py
from typing import Protocol, List, Dict, Any
from dataclasses import dataclass

@dataclass
class EmbeddingResult:
    """統一された埋め込み結果"""
    embeddings: List[float]
    dimension: int
    model_name: str

class EmbeddingModel(Protocol):
    """埋め込みモデルの統一インターフェース"""
    @property
    def dimension(self) -> int: ...
    
    def encode(self, text: str) -> EmbeddingResult: ...
    def encode_batch(self, texts: List[str]) -> List[EmbeddingResult]: ...

class VectorRepository(Protocol):
    """ベクトルDB操作の統一インターフェース"""
    def create_index(self, table: str, index: str, column: str, dim: int) -> Any: ...
    def query_index(self, index: str, vector: List[float], k: int) -> Any: ...
```

### 1.2 アダプターパターンで既存実装をラップ
```python
# search/vss/models/mock_adapter.py
class MockEmbeddingAdapter:
    """既存のモック実装をラップ"""
    def __init__(self):
        self._dimension = 384
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def encode(self, text: str) -> EmbeddingResult:
        # 既存のgenerate_requirement_embeddingを呼び出し
        from ..requirement_embedder import generate_requirement_embedding
        embedding = generate_requirement_embedding({"title": text})
        return EmbeddingResult(embedding, self._dimension, "mock")

# search/vss/models/ruri_adapter.py  
class RuriEmbeddingAdapter:
    """Ruriモデルをラップ"""
    def __init__(self):
        from ...embeddings.infrastructure import create_embedding_model
        self._model = create_embedding_model("ruri-v3-30m")
        self._dimension = 256
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def encode(self, text: str) -> EmbeddingResult:
        from ...embeddings.domain import EmbeddingRequest, EmbeddingType
        req = EmbeddingRequest(text=text, embedding_type=EmbeddingType.DOCUMENT)
        result = self._model.encode(req)
        return EmbeddingResult(result.embeddings, self._dimension, "ruri-v3")
```

## Phase 2: ディレクトリ構造の再編成

### 2.1 新しい構造
```
search/vss/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── interfaces.py      # 共通インターフェース
│   ├── types.py          # 共通型定義
│   └── utils.py          # ユーティリティ
├── models/
│   ├── __init__.py
│   ├── base.py           # 基底クラス
│   ├── mock.py           # モック実装（移動）
│   ├── ruri.py           # Ruri実装（移動）
│   └── factory.py        # モデルファクトリー
├── adapters/
│   ├── __init__.py
│   ├── kuzu_native.py    # 既存のKuzuDB VSS
│   ├── kuzu_vector.py    # VECTOR拡張（移動）
│   └── subprocess_wrapper.py  # セグフォルト対策（移動）
├── services/
│   ├── __init__.py
│   ├── similarity_search.py  # 類似検索サービス
│   └── hybrid_search.py      # ハイブリッド検索（新規）
└── tests/
    ├── test_models.py
    ├── test_adapters.py
    └── test_services.py
```

### 2.2 移行スクリプト
```bash
#!/bin/bash
# migrate.sh

# バックアップ作成
cp -r search/embeddings search/embeddings.backup
cp -r search/vss search/vss.backup

# コア機能の移動
mkdir -p search/vss/core
mkdir -p search/vss/models
mkdir -p search/vss/adapters
mkdir -p search/vss/services

# embeddingsからの移動
mv search/embeddings/infrastructure/ruri_model.py search/vss/models/ruri.py
mv search/embeddings/infrastructure/kuzu search/vss/adapters/
mv search/embeddings/domain/types.py search/vss/core/types.py

# 既存vssファイルの整理
mv search/vss/requirement_embedder.py search/vss/models/mock.py
mv search/vss/similarity_search.py search/vss/services/
```

## Phase 3: API互換性レイヤー

### 3.1 後方互換性の維持
```python
# search/vss/__init__.py
"""後方互換性のためのエクスポート"""

# 既存のインポートパスを維持
from .models.mock import generate_requirement_embedding
from .services.similarity_search import search_similar_requirements

# 新しい統一API
from .core.interfaces import EmbeddingModel, VectorRepository
from .models.factory import create_embedding_model
from .services.similarity_search import VectorSearchService

__all__ = [
    # 後方互換性
    'generate_requirement_embedding',
    'search_similar_requirements',
    # 新API
    'EmbeddingModel',
    'VectorRepository', 
    'create_embedding_model',
    'VectorSearchService',
]
```

### 3.2 移行ガイド
```python
# 旧コード
from search.vss import generate_requirement_embedding
embedding = generate_requirement_embedding({"title": "test"})

# 新コード（推奨）
from search.vss import create_embedding_model
model = create_embedding_model("mock")  # or "ruri-v3"
result = model.encode("test")
embedding = result.embeddings
```

## Phase 4: テストの統合

### 4.1 統合テスト戦略
```python
# search/vss/tests/test_integration.py
import pytest
from ..models.factory import create_embedding_model

class TestModelIntegration:
    @pytest.mark.parametrize("model_name,expected_dim", [
        ("mock", 384),
        ("ruri-v3", 256),
    ])
    def test_all_models(self, model_name, expected_dim):
        model = create_embedding_model(model_name)
        result = model.encode("テスト")
        assert len(result.embeddings) == expected_dim
```

## Phase 5: 段階的廃止

### 5.1 Deprecation warnings
```python
# search/embeddings/__init__.py
import warnings

def __getattr__(name):
    warnings.warn(
        f"search.embeddings is deprecated. Use search.vss.{name} instead",
        DeprecationWarning,
        stacklevel=2
    )
    # リダイレクト
    from search.vss import __dict__ as vss_exports
    return vss_exports.get(name)
```

## 実行順序とタイムライン

1. **Week 1**: Phase 1 - インターフェース定義とアダプター作成
2. **Week 2**: Phase 2 - ディレクトリ構造の再編成
3. **Week 3**: Phase 3 - API互換性レイヤーの実装
4. **Week 4**: Phase 4 - テストの統合と検証
5. **Week 5**: Phase 5 - 段階的廃止の開始

## リスクと対策

| リスク | 対策 |
|--------|------|
| 既存コードの破壊 | 完全なバックアップと段階的移行 |
| インポートエラー | 互換性レイヤーで既存パスを維持 |
| テストの失敗 | 各フェーズでテストを実行 |
| パフォーマンス劣化 | ベンチマークテストの実施 |

## 成功指標

- [ ] 既存のすべてのテストが通る
- [ ] 新しい統一APIが動作する
- [ ] ドキュメントが更新される
- [ ] パフォーマンスが維持される
- [ ] 移行ガイドが完成する