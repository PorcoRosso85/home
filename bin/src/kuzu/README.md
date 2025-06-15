# 要件トレーサビリティシステム

## 概要
要件→テスト→実装の一方向フローを実現するグラフデータベース。
詳細: query/ddl/schema.cypher（データモデル）、kuzu.init.sh（初期化処理）

## データ構造
```
要件 → テスト → 実装（単一方向）
 ↓        ↓        ↓
CSV:requirement_entities → is_verified_by → tests
```

## 新機能追加の完全手順

### 1. 要件を定義
```csv
# data/requirement_entities.csvに1行追加
req_新機能ID,機能タイトル,詳細説明,high,functional,true
```

### 2. テストコードを定義
```csv
# data/code_entities.csvに追加
test_新機能ID_v1.0,test_新機能名,function,"test('新機能のテスト')",3,10,40
```

### 3. 実装コードを定義
```csv
# data/code_entities.csvに追加  
func_新機能ID_v1.0,新機能名,function,"新機能名(): void",5,50,100
```

### 4. 関係を接続
```csv
# data/is_verified_by.csv - 要件→テスト
req_新機能ID,test_新機能ID_v1.0,unit

# data/tests.csv - テスト→実装
test_新機能ID_v1.0,func_新機能ID_v1.0,unit
```

### 5. システムに反映
```bash
cd ~/bin/src/kuzu && bash kuzu.init.sh
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