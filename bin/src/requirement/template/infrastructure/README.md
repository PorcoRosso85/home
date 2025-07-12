# インフラストラクチャ層

[ドメイン](../domain/README.md)と[アプリケーション](../application/README.md)を技術的に実現。

## 技術選択

### KuzuDB
グラフ構造の永続化。高性能なグラフクエリエンジン。詳細は[`kuzu/`](./kuzu/README.md)。

### VSS/FTS
類似検索の実現。POC searchモジュール統合による知的検索。

### テンプレートローダー
操作定義の読み込み。ファイルシステムからのテンプレート管理。

## 主要コンポーネント

- **VSSAdapter**: POC searchとの統合インターフェース
- **TemplateLoader**: クエリテンプレートの動的読み込み
- **EmbeddingGenerator**: 256次元ベクトル生成

## 環境設定

設定管理の詳細は[`variables/`](./variables/README.md)を参照。

## 統合ポイント

- `poc.search.hybrid.requirement_search_engine`: ハイブリッド検索エンジン
- KuzuDB拡張機能: vector/ftsによる高度な検索

## 上位層への責任

アプリケーション層のユースケースを技術的に支える基盤を提供。