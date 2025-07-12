# KuzuDB統合

グラフデータベースとしてのKuzuDBの役割と責務。

## 役割

### グラフ永続化
[ドメイン層](../../domain/README.md)で定義された要件グラフ構造の保存。

### 高速クエリ実行
グラフトラバーサルとパターンマッチングの効率的な処理。

### 拡張機能
- **vector**: 256次元embeddingのインデックス化
- **fts**: 全文検索インデックス

## 主要コンポーネント

### Connection
データベース接続の確立と管理。

### IndexManager
VSS/FTSインデックスの作成と維持。

### QueryExecutor
[アプリケーション層](../../application/README.md)からのクエリ実行。

## スキーマ管理

[DDL定義](../../domain/ddl/README.md)に基づくテーブル構造の実現。

## 上位概念

[インフラ層](../README.md)の中核として、データ永続化と検索基盤を提供。