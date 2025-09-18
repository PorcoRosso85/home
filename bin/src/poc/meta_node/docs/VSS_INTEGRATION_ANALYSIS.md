# VSS統合分析 - Meta Node POC

## 背景
ユーザーから提案された将来機能：
1. MATCHクエリでVSSランク上位が取得できるか
2. メタノード（クエリを含むノード）をMATCHすることで、VSSランク上位を連鎖させることができるか

## KuzuDBのVSS機能調査

### 現在のKuzuDB（v0.6.0時点）
- **制限事項**: KuzuDBは現時点でネイティブなベクトル検索機能を持たない
- **代替案**: 
  - 外部ベクトルDBとの連携
  - アプリケーション層でのベクトル計算
  - カスタムUDF（User Defined Function）の実装

### VSS実装パターン

#### パターン1: 外部ベクトルDB連携
```python
# Faissやhnswlibなどと連携
def vss_search(query_vector, top_k=10):
    # 外部ベクトルDBで検索
    similar_ids = vector_db.search(query_vector, k=top_k)
    
    # KuzuDBでメタデータ取得
    cypher = """
    MATCH (n:Node)
    WHERE n.id IN $similar_ids
    RETURN n
    """
    return execute_query(cypher, {"similar_ids": similar_ids})
```

#### パターン2: メタノードチェーン実行
```python
# メタノードA: VSS検索クエリ
meta_node_a = {
    "name": "vss_search_products",
    "cypher_query": """
    // 外部関数呼び出しを想定
    CALL vss.search($query_vector, 10) YIELD nodeId, score
    MATCH (p:Product {id: nodeId})
    RETURN p, score
    """
}

# メタノードB: 結果の集約
meta_node_b = {
    "name": "aggregate_by_category",
    "cypher_query": """
    MATCH (p:Product)-[:IN_CATEGORY]->(c:Category)
    WHERE p.id IN $product_ids
    RETURN c.name, COUNT(p) as count
    ORDER BY count DESC
    """
}
```

## 実装提案

### フェーズ1: VSS基盤構築
1. ベクトル計算ライブラリの統合（numpy, scikit-learn）
2. シンプルなコサイン類似度関数の実装
3. メタノードへのembeddingプロパティ追加

### フェーズ2: メタノード連鎖
1. QueryExecutorの拡張（結果を次のクエリに渡す）
2. ワークフローエンジンの実装
3. 非同期実行サポート

### フェーズ3: 最適化
1. ベクトルインデックスのキャッシング
2. バッチ処理による高速化
3. 分散実行対応

## 技術的課題

### 1. KuzuDBの制約
- トランザクション管理の制限
- カスタム関数の登録方法
- 大規模ベクトルデータの格納

### 2. パフォーマンス
- ベクトル計算のオーバーヘッド
- メモリ使用量の最適化
- クエリ実行の並列化

### 3. インターフェース設計
- VSS関数のAPI設計
- エラーハンドリング
- 結果のランキング表現

## 次のステップ

1. **概念実証（POC）**
   - 小規模データセットでのVSS実装
   - メタノード連鎖の基本実装

2. **プロトタイプ開発**
   - 実用的なVSS統合
   - パフォーマンステスト

3. **本番実装**
   - スケーラブルなアーキテクチャ
   - 運用監視機能

## 参考実装

### シンプルなVSS関数
```python
import numpy as np

def cosine_similarity(vec1, vec2):
    """コサイン類似度計算"""
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    return dot_product / (norm_a * norm_b)

def find_similar_nodes(query_vector, node_embeddings, top_k=10):
    """類似ノードの検索"""
    similarities = []
    for node_id, embedding in node_embeddings.items():
        sim = cosine_similarity(query_vector, embedding)
        similarities.append((node_id, sim))
    
    # 上位k件を返す
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]
```

### メタノード実行チェーン
```python
class ChainExecutor:
    """メタノードの連鎖実行"""
    
    def execute_chain(self, meta_nodes, initial_params):
        result = initial_params
        
        for meta_node in meta_nodes:
            # 前の結果を次の入力に
            result = self.execute_meta_node(
                meta_node, 
                params=result
            )
        
        return result
```

## まとめ
KuzuDBネイティブのVSS機能は現在存在しないが、外部ライブラリとの連携により実現可能。メタノードアーキテクチャを活用することで、VSS結果の連鎖的な処理も実装できる。