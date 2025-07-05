# DQLテンプレート仕様書（TDD Red）

## 1. get_requirement_history.cypher

### 目的
要件の全変更履歴を時系列で取得する

### パラメータ
- `$req_id`: 要件ID

### 期待される出力
```cypher
RETURN 
    r.id as entity_id,
    r.title as title,
    r.description as description,
    r.status as status,
    r.priority as priority,
    v.id as version_id,
    v.operation as operation,
    v.author as author,
    v.change_reason as change_reason,
    v.timestamp as timestamp
ORDER BY v.timestamp
```

### 必要な要素
- LocationURI経由でのアクセス
- HAS_VERSIONリレーションの追跡
- 時系列順でのソート

## 2. get_version_diff.cypher

### 目的
2つのバージョン間の差分情報を取得する

### パラメータ
- `$req_id`: 要件ID
- `$from_version`: 比較元バージョン番号
- `$to_version`: 比較先バージョン番号

### 期待される出力
両バージョンの完全な情報を返し、アプリケーション層で差分を計算

### 実装の課題
- KuzuDBではバージョン番号が直接保存されていない
- タイムスタンプ順での番号付けが必要

## 3. list_all_versions.cypher

### 目的
要件の全バージョンIDと基本情報を一覧取得

### パラメータ
- `$req_id`: 要件ID

### 期待される出力
```cypher
RETURN
    v.id as version_id,
    v.operation as operation,
    v.timestamp as timestamp,
    v.author as author
ORDER BY v.timestamp
```

## 実装時の注意点

1. **パフォーマンス**
   - 大量のバージョンがある場合を考慮
   - 適切なインデックス使用

2. **一貫性**
   - 既存のDMLテンプレートとの整合性
   - LocationURIパターンの統一

3. **エラーハンドリング**
   - 存在しない要件IDの処理
   - 不正なバージョン番号の処理