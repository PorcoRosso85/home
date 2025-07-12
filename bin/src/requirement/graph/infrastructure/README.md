# インフラストラクチャ層

[ドメイン](../domain/README.md)と[アプリケーション](../application/README.md)を技術的に実現。

## 技術選択

### KuzuDB
グラフ構造の永続化。高性能なグラフクエリエンジン。

### 主要コンポーネント

現在の主要ファイル：
- **kuzu_repository.py**: KuzuDBとの統合インターフェース
- **database_factory.py**: データベース接続管理
- **logger.py**: ロギング基盤
- **variables/**: 環境変数と設定管理

削除したコンポーネント：
- Cypher実行系（3ファイル）
- クエリ検証系

## 今後の統合予定

### Phase 2: テンプレートローダー
操作定義の読み込み。ファイルシステムからのテンプレート管理。

### Phase 3: POC Search統合
- **VSSAdapter**: POC searchとの統合インターフェース
- **EmbeddingGenerator**: 256次元ベクトル生成
- VSS/FTSによる類似検索の実現

## 環境設定

主要な環境変数：
- `RGL_DATABASE_PATH`: データベースファイルパス
- `RGL_SKIP_SCHEMA_CHECK`: スキーマチェックのスキップ
- `RGL_LOG_LEVEL`: ログレベル

## 上位層への責任

アプリケーション層のユースケースを技術的に支える基盤を提供。