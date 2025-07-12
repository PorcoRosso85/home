# データ定義言語（DDL）

要件グラフの構造を定義するスキーマ群。

## スキーマバージョン管理

[`migrations/`](./migrations/)ディレクトリで段階的な進化を管理。

## 主要テーブル

### RequirementEntity
要件の中核情報を保持。256次元のembeddingフィールドを含む。

### LocationURI  
要件の一意な識別子を管理。URIスキームによる名前空間分離。

### VersionState
要件の変更履歴を追跡。作成・更新・削除の状態遷移。

## リレーション

- **DEPENDS_ON**: 要件間の依存関係
- **LOCATES**: URIと要件の関連付け  
- **TRACKS_STATE_OF**: バージョン状態の追跡

## 上位概念

[ドメイン層](../README.md)で定義されたルールを具体的なスキーマとして表現。