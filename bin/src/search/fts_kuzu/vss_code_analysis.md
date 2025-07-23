# VSS関連コード分析

## 1. application.py のVSS関連要素

### クラス・関数
- `class VSSService` (行309-363): ベクトル検索サービスクラス
- `create_vss_service()` (行29-262): VSS用の高階関数
- `create_embedding_service()` (行265-306): 埋め込み生成サービス

### 使用箇所
- ApplicationConfig.embedding_dimension
- check_vector_func パラメータ
- generate_embedding_func パラメータ
- vector_available チェック
- documents_with_embeddings 処理
- query_vector オプション

## 2. infrastructure.py のVSS関連要素

### 定数
- EMBEDDING_DIMENSION = 256
- DOCUMENT_EMBEDDING_INDEX_NAME = "doc_embedding_index"

### 関数
- `check_vector_extension()` (行138-181): VECTOR拡張チェック
- `initialize_vector_schema()` (行183-231): ベクトル検索スキーマ初期化
- `insert_documents_with_embeddings()` (行233-306): 埋め込み付きドキュメント挿入
- `search_similar_vectors()` (行309-393): 類似ベクトル検索

### データ構造
- DatabaseConfig.embedding_dimension フィールド
- embedding DOUBLE[{dimension}] カラム定義

## 3. domain.py のVSS関連要素

### データクラス
- `SearchResult` (行26-43): embedding フィールドを含む
- embedding 関連の型定義

### 関数
- `calculate_cosine_similarity()` (行157-172): コサイン類似度計算
- `cosine_distance_to_similarity()` (行175-181): 距離からスコアへの変換
- `find_semantically_similar_documents()` (行195-224): 意味的類似文書検索
- `validate_embedding_dimension()` (行234-249): 埋め込み次元検証
- `group_documents_by_topic_similarity()` (行311-332): トピック類似度でグルーピング

## 4. mod.py のVSS関連要素

### インポート
- VSSService クラス
- create_vss_service 関数
- create_embedding_service 関数
- ベクトル関連の関数群

### エクスポート (__all__)
- "VSSService"
- "create_vss_service"
- "create_embedding_service"
- vector関連の関数名

## 5. テストファイル

### test_domain.py
- TestDomain クラス: ベクトル検索関連テスト
- test_vector_search_* で始まるテスト

### test_infrastructure.py
- test_*_vector_* のテスト
- test_*_embedding_* のテスト

## 削除対象まとめ

1. **完全削除**
   - VSSService クラス全体
   - create_vss_service() 関数
   - create_embedding_service() 関数
   - vector/embedding 関連の全関数

2. **部分削除**
   - ApplicationConfig から embedding_dimension フィールド
   - DatabaseConfig から embedding_dimension フィールド
   - SearchResult から embedding フィールド

3. **保持検討**
   - FTS関連のみのコード
   - 共通のユーティリティ関数（もしあれば）