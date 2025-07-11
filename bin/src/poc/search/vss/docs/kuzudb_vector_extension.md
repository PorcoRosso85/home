# KuzuDB Vector Extension

## 概要
KuzuDBのベクター拡張機能は、グラフデータベース内でネイティブなベクター検索を可能にする機能です。ディスクベースのHNSW（Hierarchical Navigable Small World）インデックスを実装しています。

## 主な特徴
- **ネイティブ実装**: ディスクベースのHNSWベクターインデックス
- **サポートされるデータ型**: 32ビットおよび64ビットの浮動小数点配列
- **統合性**: グラフトラバーサルとベクター検索の組み合わせが可能

## 主要な関数

### 1. CREATE_VECTOR_INDEX
ベクターインデックスを作成します。

```cypher
CALL CREATE_VECTOR_INDEX(
    'TableName',           -- テーブル名
    'index_name',         -- インデックス名
    'embedding_column'    -- 埋め込みベクトルを含むカラム名
);
```

### 2. QUERY_VECTOR_INDEX
類似度検索を実行します。

```cypher
CALL QUERY_VECTOR_INDEX(
    'TableName',
    'index_name',
    query_vector,         -- クエリベクトル
    k                     -- 返す結果の数
);
```

### 3. DROP_VECTOR_INDEX
既存のインデックスを削除します。

```cypher
CALL DROP_VECTOR_INDEX('TableName', 'index_name');
```

## インデックス設定オプション

| パラメータ | 説明 | デフォルト値 |
|-----------|------|-------------|
| `mu` | 上位グラフのノードの最大次数 | 30 |
| `ml` | 下位グラフのノードの最大次数 | 60 |
| `pu` | 上位グラフにサンプリングされるノードの割合 | 0.05 |
| `metric` | 距離計算方法（cosine, l2, l2sq, dotproduct） | cosine |
| `efc` | インデックス構築時の候補頂点数 | - |

## 高度な機能

### フィルタリング付きベクター検索
プロジェクトされたグラフを使用してフィルタリング条件を適用した検索が可能です。

### グラフトラバーサルとの組み合わせ
ベクター検索の結果を起点として、グラフのトラバーサルを実行できます。

## 使用例

### Pythonでの実装例
```python
import kuzu

# データベースに接続
conn = kuzu.Connection("./my_db")

# ベクターインデックスを作成
conn.execute("""
CALL CREATE_VECTOR_INDEX(
    'Book', 
    'title_vec_index', 
    'title_embedding'
);
""")

# 類似度検索を実行
query_vector = [0.1, 0.2, 0.3, ...]  # 実際の埋め込みベクトル
results = conn.execute("""
CALL QUERY_VECTOR_INDEX(
    'Book',
    'title_vec_index',
    $1,
    10  -- 上位10件を取得
);
""", [query_vector])
```

## 距離メトリクス

- **cosine**: コサイン類似度
- **l2**: ユークリッド距離
- **l2sq**: ユークリッド距離の二乗
- **dotproduct**: ドット積

## 参考リンク
- [KuzuDB Vector Extension Documentation](https://docs.kuzudb.com/extensions/vector/)