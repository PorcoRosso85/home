# kuzu_sqlite

## 責務

このディレクトリは以下の責務を持つPOC（Proof of Concept）です：

1. **SQLite永続化**: データをSQLiteデータベースに永続化する
2. **KuzuDB連携**: SQLiteをKuzuDBにアタッチすることでCypherクエリを実行可能にする

## 目的

SQLiteの安定した永続化機能とKuzuDBのグラフクエリ機能を組み合わせることで、以下を実現します：

- リレーショナルデータのグラフDB表現
- Cypherクエリによる柔軟なデータ探索
- SQLiteの信頼性とKuzuDBの表現力の両立

## 技術スタック

- **SQLite**: 永続化層
- **KuzuDB**: グラフクエリエンジン
- **Cypher**: クエリ言語