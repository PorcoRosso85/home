# ロールバック手順書：001_unify_naming_rollback

## 概要
このドキュメントは、`000_initial.cypher`で実施したネーミング統一（LocationURI → ImplementationURI）を安全にロールバックする手順を記載します。

## ロールバック対象
- **ノードテーブル名の変更**
  - ImplementationURI → LocationURI
  - ImplementationEntity → RequirementEntity
- **エッジテーブルの参照更新**
  - 各リレーションテーブルの参照を新しいノード名に合わせて更新

## 前提条件
1. KuzuDBが稼働中であること
2. 現在のデータベースバックアップが存在すること
3. `001_unify_naming_rollback.cypher`ファイルが利用可能であること

## ロールバック手順

### 1. 事前確認
```bash
# 現在のスキーマ状態を確認
cd /home/nixos/bin/src/architecture
python infrastructure/query_runner.py "SHOW TABLES;"

# データ件数を記録
python infrastructure/query_runner.py "MATCH (n:ImplementationURI) RETURN COUNT(n);"
python infrastructure/query_runner.py "MATCH (n:ImplementationEntity) RETURN COUNT(n);"
```

### 2. データベースバックアップ
```bash
# KuzuDBのデータディレクトリをバックアップ
cp -r /path/to/kuzu/data /path/to/backup/kuzu_data_$(date +%Y%m%d_%H%M%S)
```

### 3. ロールバックスクリプトの実行
```bash
# スキーママネージャーを使用してロールバック実行
cd /home/nixos/bin/src/architecture
python infrastructure/schema_manager.py apply ddl/migrations/001_unify_naming_rollback.cypher
```

### 4. 実行後の検証

#### 4.1 スキーマ確認
```bash
# テーブル一覧の確認
python infrastructure/query_runner.py "SHOW TABLES;"
```

期待される結果：
- LocationURI（ノードテーブル）
- RequirementEntity（ノードテーブル）
- VersionState（ノードテーブル）
- Responsibility（ノードテーブル）
- 各種リレーションテーブル

#### 4.2 データ整合性確認
```bash
# ノード数の確認
python infrastructure/query_runner.py "MATCH (l:LocationURI) RETURN COUNT(l) AS location_count;"
python infrastructure/query_runner.py "MATCH (r:RequirementEntity) RETURN COUNT(r) AS entity_count;"

# リレーション数の確認
python infrastructure/query_runner.py "MATCH (:LocationURI)-[l:LOCATES]->(:RequirementEntity) RETURN COUNT(l) AS locates_count;"
python infrastructure/query_runner.py "MATCH (:LocationURI)-[c:CONTAINS_LOCATION]->(:LocationURI) RETURN COUNT(c) AS contains_count;"
```

### 5. バックアップテーブルのクリーンアップ（オプション）
検証が完了し、ロールバックが成功したことを確認後：

```bash
# バックアップテーブルの削除
python infrastructure/query_runner.py "DROP TABLE _backup_ImplementationURI;"
python infrastructure/query_runner.py "DROP TABLE _backup_ImplementationEntity;"
python infrastructure/query_runner.py "DROP TABLE _backup_LOCATES;"
python infrastructure/query_runner.py "DROP TABLE _backup_CONTAINS_LOCATION;"
python infrastructure/query_runner.py "DROP TABLE _backup_HAS_RESPONSIBILITY;"
```

## トラブルシューティング

### ロールバック失敗時
1. エラーメッセージを記録
2. バックアップからデータベースを復元：
   ```bash
   rm -rf /path/to/kuzu/data
   cp -r /path/to/backup/kuzu_data_[timestamp] /path/to/kuzu/data
   ```

### データ不整合が発生した場合
1. バックアップテーブルからデータを確認
2. 手動でデータを修正するか、バックアップから復元

## 注意事項
- ロールバック実行前に必ずフルバックアップを取得すること
- 本番環境では営業時間外に実施すること
- アプリケーションコードも同時に旧バージョンに戻す必要がある

## ロールバック後の対応
1. アプリケーションコードの更新（ImplementationURI → LocationURIへの参照変更）
2. 関連するDQLクエリの更新
3. システム全体のテスト実施