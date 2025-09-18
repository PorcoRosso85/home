# 環境変数管理

システム設定の一元管理と環境差分の吸収。

## 設定原則

### 12-Factor App準拠
環境固有の設定は環境変数で管理。コードから分離。

### 階層的管理
- デフォルト値
- 環境変数によるオーバーライド
- 実行時パラメータ

## 主要設定

### データベース
- `RTS_DB_PATH`: KuzuDBのデータパス
- `RTS_DB_TIMEOUT`: 接続タイムアウト

### ログ
- `RTS_LOG_LEVEL`: ログレベル設定
- `RTS_LOG_FORMAT`: 出力フォーマット

### 検索
- `RTS_SEARCH_K`: デフォルト検索件数
- `RTS_EMBEDDING_DIM`: ベクトル次元数（256）

## 設定の継承

[requirement/graph](../../../graph/infrastructure/variables/)から移植された設定体系を維持。

## 上位概念

[インフラ層](../README.md)の一部として、環境に依存しない実行を保証。