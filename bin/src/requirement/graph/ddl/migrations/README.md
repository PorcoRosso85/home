# DDLマイグレーション管理

## 概要
このディレクトリはDDLスキーマの変更履歴を管理します。
セマンティックバージョニングを採用し、各バージョンのスキーマを独立ファイルとして管理します。

## ファイル構成
- `3.1.0_initial.cypher`: 初期スキーマ
- `3.2.0_remove_has_version.cypher`: HAS_VERSION削除の差分
- `3.2.0_current.cypher`: 現在の完全スキーマ

## 命名規則
```
<major>.<minor>.<patch>_<説明>.cypher
```

- major.minor.patch: セマンティックバージョン
- 説明: 変更内容を表す短い説明（snake_case）

## スキーマ適用方法

### 新規環境（推奨）
```bash
# 最新の完全スキーマを適用
kuzu apply 3.2.0_current.cypher
```

### 既存環境（差分適用）
各差分ファイル内のマイグレーションクエリを順次実行。

## 将来的な運用
`../schema.cypher`は廃止予定。最新の完全スキーマは常に
`<最新バージョン>_current.cypher`として管理します。

## 変更履歴

### 3.1.0 → 3.2.0
- **変更内容**: HAS_VERSION関係を削除
- **理由**: kuzu/query/ddl準拠（VersionStateはLocationURIのみ管理）
- **影響**: RequirementEntity → VersionStateの直接関係が削除
- **新方式**: VersionState → LocationURI → RequirementEntity
- **破壊的変更**: あり（既存クエリの修正が必要）