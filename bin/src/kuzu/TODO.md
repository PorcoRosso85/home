# KuzuDB URIバージョン管理システム - TODO

## 実装優先順位

1. **append-only設計** 【最優先・基盤】 - 全体アーキテクチャの根本
2. **change_type機能** 【必須・前提条件】 - append-onlyを実現するために必須
3. **URIリネーム変更追跡** 【重要・履歴保持】 - ファイル履歴の連続性
4. **URIの関数パス化** 【拡張・独立】 - 細粒度追跡の拡張機能

---

## 1. append-only設計のための要件【最優先・基盤】

### 設計原則
- 各バージョンは変更差分のみを記録
- LocationURIノードは削除せず、関係性で状態を表現
- 完全な変更履歴を保持

### なぜ最優先か
- 全体のアーキテクチャを決定する根本的な設計判断
- 他のすべての機能がこの設計に依存
- 既存データの移行戦略も含めて最初に決定すべき

### 実装要件

1. **差分記録の徹底**
   - 各バージョンでCREATE/UPDATE/DELETEの変更のみ記録
   - 変更なしのファイルは関係性を作らない

2. **最新状態の効率的な取得**
   ```cypher
   // 各LocationURIの最新状態を取得するビューの作成
   CREATE VIEW current_location_state AS
   MATCH (v:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
   WHERE NOT EXISTS {
     MATCH (v2:VersionState)-[r2:TRACKS_STATE_OF_LOCATED_ENTITY]->(l)
     WHERE v2.timestamp > v.timestamp
   }
   AND r.change_type != 'DELETE'
   RETURN l.id, v.version_id, r.change_type;
   ```

3. **確認すべき実装ファイル**
   - `/home/nixos/bin/src/kuzu/browse/infrastructure/repository/queryExecutor.ts` - クエリ実行
   - `/home/nixos/bin/src/kuzu/browse/public/dql/list_uris_cumulative.cypher` - 累積クエリの修正

### パフォーマンス考慮事項
- インデックス戦略：`(version_id, change_type)`の複合インデックス
- キャッシュ：現在バージョンのLocationURI一覧をメモリキャッシュ

---

## 2. change_type機能【必須・前提条件】

### 現状の問題
- TRACKS_STATE_OF_LOCATED_ENTITYリレーションシップにchange_typeプロパティがない
- 削除されたファイルと変更なしファイルの区別が不可能

### なぜ必須か
- append-only設計を実現するために**必須**
- これがないと「削除」と「変更なし」を区別できない
- リネーム追跡もchange_type='RENAME'として実装可能

### 実装方針
1. **スキーマ変更**
   ```cypher
   CREATE REL TABLE TRACKS_STATE_OF_LOCATED_ENTITY (
       FROM VersionState TO LocationURI,
       change_type STRING,  // CREATE, UPDATE, DELETE, RENAME
       MANY_MANY
   );
   ```

2. **CSVファイル構造の変更**
   ```csv
   # version_location_changes.csv
   version_id,id,change_type
   v1.1.0,file:///src/new.ts,CREATE
   v1.1.0,file:///src/main.ts,UPDATE
   v1.1.0,file:///src/old.ts,DELETE
   ```

3. **確認すべき実装ファイル**
   - `/home/nixos/bin/src/kuzu/data/version_location_relations.csv` - 既存データの移行
   - `/home/nixos/bin/src/kuzu/browse/application/usecase/createDatabaseData.ts` - DML生成ロジック

### 移行戦略
```cypher
// 既存データの移行（初回のみ全てCREATE）
MATCH (v:VersionState)-[r:TRACKS_STATE_OF_LOCATED_ENTITY]->(l:LocationURI)
SET r.change_type = 'CREATE';
```

---

## 3. URIリネーム変更追跡の要件【重要・履歴保持】

### 現状の問題
- ファイル名変更が「削除」+「作成」として記録され、履歴が断絶する
- 例：`utils.ts` → `utilities.ts`への改名で過去の変更履歴が追跡不可能

### 実装方針（2つの選択肢）

#### オプション1: change_type='RENAME'として実装
```csv
# version_location_changes.csv
version_id,id,change_type,rename_from
v1.1.0,file:///src/utilities.ts,RENAME,file:///src/utils.ts
```

#### オプション2: 専用リレーションシップ
```cypher
CREATE REL TABLE RENAMED_TO (
    FROM LocationURI TO LocationURI,
    version_id STRING,
    MANY_MANY
);
```

### 確認すべき実装ファイル
- `/home/nixos/bin/src/kuzu/browse/public/export_data/schema.cypher` - スキーマ定義
- `/home/nixos/bin/src/kuzu/kuzu.init.sh` - テーブル作成とCOPY文の追加
- `/home/nixos/bin/src/kuzu/browse/application/usecase/createSchema.ts` - DDL実行

### DQLサンプル
```cypher
// ファイルの改名履歴を追跡（オプション2の場合）
MATCH path = (original:LocationURI)-[:RENAMED_TO*]->(current:LocationURI)
WHERE original.id = 'file:///src/utils.ts'
RETURN path;
```

---

## 4. URIをファイルパスではなく '#'使った関数パス化【拡張・独立】

### 現状
- LocationURIは主にファイルパスを表現
- 関数・クラス単位の細かい変更追跡が不可能

### なぜ最後か
- 他の機能に依存しない独立した拡張
- 既存システムへの影響が最小限
- 基盤が整ってから実装しても問題ない

### 実装方針
1. **URI形式の拡張**
   ```
   file:///src/main.ts#main           // main関数
   file:///src/utils.ts#parseUri      // parseUri関数
   file:///src/App.tsx#App.render     // Appクラスのrenderメソッド
   ```

2. **CodeEntityとの関連付け強化**
   - CodeEntityのpersistent_idとLocationURIのfragmentを連携
   - HAS_LOCATIONリレーションシップの活用

3. **確認すべき実装ファイル**
   - `/home/nixos/bin/src/kuzu/browse/domain/service/locationUriParser.ts` - URI解析ロジック
   - `/home/nixos/bin/src/kuzu/browse/application/hooks/locationUrisLogic.ts` - parseUriFromId関数
   - `/home/nixos/bin/src/kuzu/data/location_uris.csv` - 既存データの確認

### 実装例
```typescript
// locationUriParser.tsの拡張
function parseCodeEntityUri(uri: string): {
  filePath: string;
  entityPath?: string[];  // ['App', 'render'] のような階層
} {
  const [filePart, fragment] = uri.split('#');
  return {
    filePath: filePart,
    entityPath: fragment?.split('.') || []
  };
}
```

---

## 実装フェーズ

### Phase 1: 基盤構築
1. append-only設計の確定
2. change_type機能の実装（既存データの移行含む）

### Phase 2: 履歴機能
3. リネーム追跡機能の追加（change_type='RENAME'として）

### Phase 3: 拡張機能
4. 関数パス化（#を使った細粒度追跡）

## テストデータ

`/home/nixos/bin/src/kuzu/data/`に以下のテストデータを準備：
- `version_location_changes_test.csv` - change_type付きのテストデータ
- `location_renames_test.csv` - リネーム追跡のテストデータ

## 次のステップ

1. append-only設計の詳細仕様策定
2. スキーマ変更のDDLを作成（change_type追加）
3. 既存データの移行スクリプトを作成
4. kuzu.init.shの更新
5. フロントエンドのクエリロジック更新
