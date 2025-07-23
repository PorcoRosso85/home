# 統一APIパターン提案書

## 目的
FTSとVSSを並列で使用する際、呼び出し側が一貫したメンタルモデルで両方を扱えるようにする。

## 現状の問題点
呼び出し側から見た場合、FTSとVSSで異なるパターンを学習する必要がある：

```python
# 現在の不統一な状態
# FTS: シンプルな関数群
fts_conn = create_fts_connection()
fts_result = index_fts_documents(docs, fts_conn)

# VSS: 複雑な組み立て
embedding_func = create_embedding_service()
vss_service = create_vss_service(多数の関数...)
vss_result = vss_service["index_documents"](docs, config)
```

## 理想的な統一パターン

### パターン1: 作成・操作・破棄の3段階
```python
# 検索システムの作成
fts = create_fts()
vss = create_vss()

# ドキュメントの操作
fts.index(documents)
vss.index(documents)

# 検索の実行
fts_results = fts.search("クエリ")
vss_results = vss.search("クエリ")

# リソースの解放
fts.close()
vss.close()
```

### パターン2: 関数型の統一インターフェース
```python
# 同じ構造の設定
fts_config = create_fts_config(db_path="./fts_db")
vss_config = create_vss_config(db_path="./vss_db")

# 同じ構造の初期化
fts = initialize_fts(fts_config)
vss = initialize_vss(vss_config)

# 同じ構造の操作
index_documents(fts, documents)
index_documents(vss, documents)

# 同じ構造の検索
fts_results = search_documents(fts, query="テキスト")
vss_results = search_documents(vss, query="テキスト")
```

## 推奨実装アプローチ

### 1. 統一された作成関数
```python
def create_fts(**kwargs) -> SearchSystem:
    """FTS検索システムを作成"""
    return FTSSearchSystem(**kwargs)

def create_vss(**kwargs) -> SearchSystem:
    """VSS検索システムを作成"""
    return VSSSearchSystem(**kwargs)
```

### 2. 共通インターフェース
```python
class SearchSystem(Protocol):
    """検索システムの共通インターフェース"""
    
    def index(self, documents: List[Document]) -> IndexResult:
        """ドキュメントをインデックス"""
        ...
    
    def search(self, query: str, **options) -> SearchResults:
        """検索を実行"""
        ...
    
    def delete(self, document_ids: List[str]) -> DeleteResult:
        """ドキュメントを削除"""
        ...
    
    def close(self) -> None:
        """リソースを解放"""
        ...
```

### 3. 統一された結果型
```python
@dataclass
class IndexResult:
    success: bool
    indexed_count: int
    failed_count: int
    duration_ms: float
    errors: List[Error]

@dataclass
class SearchResults:
    success: bool
    items: List[SearchResultItem]
    total_count: int
    duration_ms: float
    metadata: Dict[str, Any]
```

## 利点

### 呼び出し側の視点
1. **学習コスト削減**: 一つのパターンを学べば両方使える
2. **コードの一貫性**: 同じ思考フローで実装可能
3. **エラー処理の統一**: 同じ方法でエラーをハンドリング
4. **テストの簡素化**: 同じテストパターンを適用可能

### 実装例
```python
# 統一されたパターンで両方を使用
def process_documents(documents: List[Document]):
    # 両方の検索システムを同じパターンで作成
    fts = create_fts(db_path="./fts_db")
    vss = create_vss(db_path="./vss_db", model="ruri-v3")
    
    try:
        # 同じパターンでインデックス
        fts_result = fts.index(documents)
        vss_result = vss.index(documents)
        
        # 同じパターンで検索
        query = "ユーザー認証"
        fts_matches = fts.search(query, limit=10)
        vss_matches = vss.search(query, limit=10)
        
        # 結果の統合
        return combine_results(fts_matches, vss_matches)
        
    finally:
        # 同じパターンでクリーンアップ
        fts.close()
        vss.close()
```

## 実装の段階

### Phase 1: インターフェース定義
- `SearchSystem` プロトコルの定義
- 共通の結果型の定義

### Phase 2: FTSのラッパー実装
- 既存のFTS関数を`SearchSystem`インターフェースでラップ

### Phase 3: VSSの簡素化
- 複雑な高階関数を内部に隠蔽
- `SearchSystem`インターフェースの実装

### Phase 4: ドキュメント整備
- 統一APIの使用例
- マイグレーションガイド