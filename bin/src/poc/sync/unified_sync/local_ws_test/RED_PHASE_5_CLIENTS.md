# TDD Red Phase - 5 Clients Complex Operations

## 新規テストケース

### five clients should maintain consistent state with complex operations

このテストは以下を検証します：
1. **5クライアントの同時接続**
2. **複雑なグラフ構造の作成**
   - 5人のPerson（Alice, Bob, Charlie, Dave, Eve）
3. **各クライアントが異なるリレーションシップを追加**
   - Alice -> Bob (KNOWS)
   - Bob -> Charlie (WORKS_WITH)
   - Charlie -> Dave (MANAGES)
   - Dave -> Eve (COLLABORATES_WITH)
   - Eve -> Alice (FRIENDS_WITH)
4. **並行更新**
   - 5クライアントが同時にAliceの年齢を更新

## 期待される失敗

### 1. 複数CREATE文の処理
```cypher
CREATE (alice:Person {id: 'alice', name: 'Alice', age: 30})
CREATE (bob:Person {id: 'bob', name: 'Bob', age: 25})
CREATE (charlie:Person {id: 'charlie', name: 'Charlie', age: 35})
CREATE (dave:Person {id: 'dave', name: 'Dave', age: 28})
CREATE (eve:Person {id: 'eve', name: 'Eve', age: 32})
```
現在の実装は単一のCREATE文のみサポート

### 2. 複数MATCH文のパターン
```cypher
MATCH (a:Person {id: 'alice'})
MATCH (b:Person {id: 'bob'})
CREATE (a)-[:KNOWS]->(b)
```
現在の実装はこのパターンに未対応

### 3. Person型のサポート
現在はUser型とTestNode型のみサポート

### 4. 異なるリレーションシップタイプ
WORKS_WITH, MANAGES, COLLABORATES_WITH, FRIENDS_WITH などの新しいタイプ

## 実装方針

1. **パーサーの拡張**
   - 複数のCREATE文を個別に処理
   - 複数のMATCH文をサポート
   - 任意のノードタイプを受け入れる

2. **リレーションシップの改善**
   - 実際のエッジ情報を保存
   - リレーションシップタイプを記録

3. **並行性の改善**
   - イベント順序の保証
   - 最終的一貫性の確保

## テスト実行コマンド

```bash
nix run
# または
deno test --no-check --allow-net kuzu-sync-client.test.ts --filter "five clients"
```