# DQL (Data Query Language) ディレクトリ

このディレクトリには、KuzuDB用のデータ照会言語（DQL）Cypherクエリファイルを格納します。DQLクエリはデータの検索、集計、関係探索などの読み取り操作に使用されます。

[クエリモジュール全体の説明に戻る](../README.md)

## 目的

DQLクエリの主な目的は、DDLで定義されたスキーマとDMLで操作されたデータに基づいて、kuzu-wasmメモリに格納されているデータを取得・分析することです。具体的には以下を含みます：

- ノード（Node）の検索と取得
- リレーションシップ（Relationship）のトラバーサル
- パターンマッチングによる複雑なグラフ探索
- データの集計と分析
- 結果の射影とフォーマット

## ファイル形式

すべてのDQLクエリファイルは`.cypher`拡張子を持ち、Cypherクエリ言語で記述されます。

## 命名規則

DQLクエリファイルの命名規則：

- `find_<entity>.cypher`: エンティティ検索クエリ
- `get_<entity>_by_<attribute>.cypher`: 特定の属性によるエンティティ取得クエリ
- `count_<entity>.cypher`: エンティティ数の集計クエリ
- `analyze_<pattern>.cypher`: 特定パターンの分析クエリ

## 使用方法

これらのDQLクエリファイルは以下の目的で使用されます：

1. データベースからのデータ取得
2. グラフパターンの検索と分析
3. KuzuDBブラウザアプリケーションによって読み取られ、kuzudb-wasmメモリ内のデータベースに対して実行される

## 例

DQLクエリファイルの例：

```cypher
// find_person.cypher
MATCH (p:Person)
WHERE p.age > $min_age
RETURN p.id, p.name, p.age
ORDER BY p.age DESC;

// find_friends_of_friends.cypher
MATCH (p1:Person)-[:Knows]->(p2:Person)-[:Knows]->(p3:Person)
WHERE p1.id = $start_person_id AND p1 <> p3
RETURN DISTINCT p3.id, p3.name, p3.age
ORDER BY p3.name;
```

## 注意点

- DQLクエリはDDLで定義されたスキーマと、DMLで投入されたデータの構造に依存します。
- パフォーマンスを考慮したクエリ設計が重要です（適切なインデックス利用、効率的なパターンマッチングなど）。
- パラメータ化されたクエリを使用することで、同じクエリテンプレートを異なる条件で再利用できます。
- 結果の形式（JSON, CSV, 表形式など）を考慮してクエリを設計すると、後処理が容易になります。
