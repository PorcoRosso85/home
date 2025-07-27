# trd_dml
/trd_dml

# 説明
bin/src/requirement/graphシステムを使用して、TRD（Traced Requirements Driven）データベースの構築・データ投入を行う

# 実行内容
0. 禁止事項確認: `bin/docs/conventions/prohibited_items.md`
1. **requirement/graphシステムの初期化**
   ```bash
   cd ~/bin/src/requirement/graph
   nix develop
   ```

2. **データベースの作成とスキーマ定義**
   ```bash
   # Neo4jコンテナの起動
   docker-compose up -d
   
   # スキーマの適用
   python -m cypher_queries.ddl.apply_schema
   ```

3. **データの投入（DML）**
   ```bash
   # CSVデータのインポート
   python -m data_import.csv_to_neo4j
   
   # または個別にデータ投入
   python -m cypher_queries.dml.insert_requirements
   python -m cypher_queries.dml.insert_tests
   python -m cypher_queries.dml.insert_implementations
   ```

4. **データ検証**
   ```bash
   # 投入データの確認
   python -m cypher_queries.dql.verify_data_integrity
   
   # 要件トレーサビリティの確認
   python -m cypher_queries.dql.check_traceability
   ```

# 使用するシステム
- **ディレクトリ**: ~/bin/src/requirement/graph
- **データベース**: Neo4j（Docker経由）
- **言語**: Python
- **フレームワーク**: py2neo または neo4j-python-driver

# データ構造
```
要件(Requirement) → テスト(Test) → 実装(Implementation)
      ↓                ↓              ↓
   VERIFIED_BY       TESTS      IMPLEMENTS
```

# 前提条件
- Docker/Docker Composeがインストール済み
- requirement/graphディレクトリのflake.nixが正しく設定済み

# エラー時の対処
- Neo4j接続エラー: `docker ps`でコンテナ状態を確認
- 認証エラー: .envファイルのNEO4J_AUTH設定を確認
- スキーマエラー: DDLスクリプトを再実行