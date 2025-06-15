# 要件トレーサビリティシステム（TRD: Traced Requirements Driven）

## 🚨 UsecaseDriven開発の鉄則
**すべての機能開発はユースケース（DQL）から始まる**

## 概要
要件→テスト→実装の一方向フローを実現するグラフデータベース。
詳細: query/ddl/schema.cypher（データモデル）、kuzu.init.sh（初期化処理）

## データ構造
```
要件 → テスト → 実装（単一方向）
 ↓        ↓        ↓
CSV:requirement_entities → is_verified_by → tests
```

## 新機能追加フロー

### Phase 1: ユースケース設計【Sequential】
- [ ] 1-1: ビジネス要求の明確化
- [ ] 1-2: ユースケースシナリオの作成
- [ ] 1-3: DQLクエリの設計
- [ ] 1-4: 必要なスキーマ（ノード・エッジ・プロパティ）の洗い出し

#### DQL設計例
```cypher
# 例: 招待トレースシステムの場合
# ユースケース1: 特定の招待コードから系譜を追跡
MATCH path = (inviter:User)-[:INVITED*]->(invitee:User {code: $code})
RETURN path

# ユースケース2: アフィリエイト階層の取得
MATCH (root:User)-[:INVITED*0..]->(member:User)
WHERE root.id = $userId
RETURN root, member, length(path) as depth
```

**ゲートチェック**: DQL設計レビュー完了？ → No なら Phase 1 をやり直し

### Phase 2: TRD要件定義【Sequential】
- [ ] 2-1: 要件CSVへの追加（requirement_entities.csv）
  ```csv
  req_新機能ID,機能タイトル,詳細説明,high,functional,true
  ```
- [ ] 2-2: テストコード定義（code_entities.csv）
  ```csv
  test_新機能ID_v1.0,test_新機能名,function,"test('新機能のテスト')",3,10,40
  ```
- [ ] 2-3: 実装コード定義（code_entities.csv）
  ```csv
  func_新機能ID_v1.0,新機能名,function,"新機能名(): void",5,50,100
  ```
- [ ] 2-4: 関係性の定義
  ```csv
  # data/is_verified_by.csv - 要件→テスト
  req_新機能ID,test_新機能ID_v1.0,unit
  
  # data/tests.csv - テスト→実装
  test_新機能ID_v1.0,func_新機能ID_v1.0,unit
  ```

**並列実行可能タスク**:
- [ ] 2-P1: 既存要件との整合性チェック
- [ ] 2-P2: 命名規則の確認

### Phase 3: データベース反映と検証【Sequential】
- [ ] 3-1: kuzu.init.sh実行
  ```bash
  cd ~/bin/src/kuzu && bash kuzu.init.sh
  ```
- [ ] 3-2: テストスキーマ作成（CREATE NODE TABLE等）
- [ ] 3-3: テストデータ投入
- [ ] 3-4: ユースケースDQL実行確認

#### DQL動作確認例
```bash
# テストデータの投入（DML）
echo "CREATE (:User {id: 'user1', name: 'Alice'});" | kuzu kuzu_db
echo "CREATE (:User {id: 'user2', name: 'Bob', code: 'ABC123'});" | kuzu kuzu_db
echo "MATCH (a:User {id: 'user1'}), (b:User {id: 'user2'}) CREATE (a)-[:INVITED]->(b);" | kuzu kuzu_db

# ユースケースDQLの実行
echo "MATCH path = (inviter:User)-[:INVITED*]->(invitee:User {code: 'ABC123'}) RETURN path;" | kuzu kuzu_db
```

**並列実行可能タスク**:
- [ ] 3-P1: トレーサビリティクエリ実行
- [ ] 3-P2: 要件ステータス確認

**ゲートチェック**: DQLが期待通り動作？ → No なら Phase 1 に戻る

### Phase 4: 実装開始【実装フェーズ】
- [ ] 4-1: テストコード実装
- [ ] 4-2: 本体コード実装
- [ ] 4-3: 統合テスト

## コマンドテンプレート集

### 要件追加前の確認（並列実行）
```bash
{
  # 現在の要件状況
  echo "MATCH (r:RequirementEntity) RETURN count(r) as total_reqs;" | kuzu kuzu_db &
  
  # 未実装要件
  echo "MATCH (r:RequirementEntity) WHERE r.verification_required = true 
        OPTIONAL MATCH (r)-[:IS_VERIFIED_BY]->(t) 
        WITH r WHERE t IS NULL RETURN count(r) as unimplemented;" | kuzu kuzu_db &
  
  wait
}
```

### 要件トレーサビリティ確認（並列実行）
```bash
{
  # テスト駆動実装の確認
  echo "MATCH (r:RequirementEntity)-[:IS_VERIFIED_BY]->(t:CodeEntity)-[:TESTS]->(i:CodeEntity) 
        RETURN r.id, t.name as test, i.name as impl 
        ORDER BY r.id;" | kuzu kuzu_db > implemented.txt &
  
  # 未実装要件の抽出
  echo "MATCH (r:RequirementEntity) WHERE r.verification_required = true 
        OPTIONAL MATCH (r)-[:IS_VERIFIED_BY]->(t:CodeEntity)-[:TESTS]->(i:CodeEntity) 
        WITH r,t,i WHERE t IS NULL 
        RETURN r.id, r.title;" | kuzu kuzu_db > unimplemented.txt &
  
  wait
  echo "=== 実装済み ===" && cat implemented.txt
  echo "=== 未実装 ===" && cat unimplemented.txt
}
```

## 要件状態の確認

### 単一クエリ
```bash
# 未実装要件
echo "MATCH (r:RequirementEntity) WHERE r.verification_required = true OPTIONAL MATCH (r)-[:IS_VERIFIED_BY]->(t:CodeEntity)-[:TESTS]->(i:CodeEntity) WITH r,t,i WHERE t IS NULL RETURN r.id, r.title;" | kuzu kuzu_db

# テスト済み要件
echo "MATCH (r:RequirementEntity)-[:IS_VERIFIED_BY]->(t:CodeEntity)-[:TESTS]->(i:CodeEntity) RETURN r.id, t.name, i.name;" | kuzu kuzu_db
```

### 並列タスク実行パターン
```bash
cd ~/bin/src/kuzu
{
  # 未実装要件の抽出（優先度高い開発対象の特定）
  echo "MATCH (r:RequirementEntity) WHERE r.verification_required = true OPTIONAL MATCH (r)-[:IS_VERIFIED_BY]->(t) WITH r WHERE t IS NULL RETURN r.id, r.title, r.priority ORDER BY r.priority;" | kuzu kuzu_db > unimplemented.txt &
  
  # テスト未作成の検出（TDD違反の発見）
  echo "MATCH (r:RequirementEntity)-[:IS_VERIFIED_BY]->(t:CodeEntity) WHERE NOT EXISTS((t)-[:TESTS]->(:CodeEntity)) RETURN r.id, t.name;" | kuzu kuzu_db > untested.txt &
  
  # 実装済み確認（進捗の可視化）
  echo "MATCH (r:RequirementEntity)-[:IS_VERIFIED_BY]->(t:CodeEntity)-[:TESTS]->(i:CodeEntity) RETURN r.id, t.name, i.name;" | kuzu kuzu_db > implemented.txt &
  
  wait
}
cat unimplemented.txt untested.txt implemented.txt
```

## エラー時の対処

- `Copy exception: Unable to find primary key`: 該当IDがlocation_uris.csvに未登録
  → data/location_uris.csvに`file:///test/新機能.test.ts#test_新機能`を追加

- 重複パス検出: IS_IMPLEMENTED_BYに直接登録している
  → is_implemented_by.csvを空にして、必ずテスト経由にする

## CSV形式
- requirement_entities.csv: id,title,description,priority,requirement_type,verification_required
- is_verified_by.csv: from_id,to_id,test_type