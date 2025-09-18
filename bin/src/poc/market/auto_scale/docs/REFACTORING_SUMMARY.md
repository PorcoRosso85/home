# GraphDBクエリ管理リファクタリング概要

## 実施日
2025-01-27

## 変更の概要
GraphDBのCypherクエリを外部ファイルとして管理する方式にリファクタリングを実施しました。これにより、クエリの管理性、再利用性、テスタビリティが向上しました。

## 主な変更点

### 1. ディレクトリ構造の追加
```
auto_scale_contract/contract_management/cypher/
├── schema/
│   └── contract_schema.cypher    # データベーススキーマ定義
└── queries/
    ├── contract/                 # 契約関連クエリ
    │   ├── check_contract_exists.cypher
    │   ├── check_contract_party_relationship.cypher
    │   ├── create_contract.cypher
    │   ├── create_contract_party_relationship.cypher
    │   ├── find_active_contracts.cypher
    │   ├── find_contract.cypher
    │   ├── find_contracts_by_client.cypher
    │   └── update_contract.cypher
    └── party/                    # 当事者関連クエリ
        ├── check_contract_party_exists.cypher
        ├── create_contract_party_relationship.cypher
        ├── create_party.cypher
        ├── create_referral_chain.cypher
        ├── ensure_party_exists.cypher
        ├── find_contracts_by_party.cypher
        ├── find_parties_by_contract.cypher
        ├── find_party_by_id.cypher
        ├── find_referral_chains.cypher
        └── update_party.cypher
```

### 2. クエリファイルの標準化
各クエリファイルには以下の情報を含めています：
- **Purpose**: クエリの目的を1行で説明
- **Description**: 詳細な説明
- **Parameters**: 必要なパラメータとその型、説明
- **Query**: 実際のCypherクエリ

例：
```cypher
-- Purpose: Create a new contract node in the graph database
-- Description: Creates a contract node with all required properties including
--              financial details, validity period, and associated terms
-- Parameters:
--   $id: STRING - Unique contract identifier (UUID as string)
--   $title: STRING - Contract title
--   ...
CREATE (c:Contract {
    id: $id,
    title: $title,
    ...
})
```

### 3. インフラストラクチャ層の更新
`infrastructure.py`でのクエリ実行方法を更新：

**変更前**：
```python
query = """
CREATE (c:Contract {
    id: $id,
    title: $title,
    ...
})
"""
self.db.execute(query, parameters)
```

**変更後**：
```python
from kuzu_py import load_query_from_file

query_path = Path(__file__).parent / "cypher" / "queries" / "contract" / "create_contract.cypher"
query_result = load_query_from_file(query_path)
self.db.execute(query_result.query, parameters)
```

### 4. スキーマ定義の外部化
データベーススキーマ定義を`contract_schema.cypher`に移動し、タイムスタンプやJSONデータの型をより適切に定義しました。

## 利点

### 1. 保守性の向上
- クエリが独立したファイルとして管理され、変更が容易
- クエリの重複を避けやすい
- バージョン管理でクエリの変更履歴が追跡しやすい

### 2. 開発効率の向上
- クエリの再利用が容易
- クエリの単体テストが可能
- IDEでのCypher構文ハイライトが利用可能

### 3. チーム開発の改善
- クエリレビューが独立して実施可能
- ドメインエキスパートとの協業が容易
- クエリドキュメントの自動生成が可能

### 4. テスタビリティの向上
- クエリファイルの構文チェックが可能
- モックデータでのクエリテストが容易
- パフォーマンステストの独立実施が可能

## 今後の展望

1. **クエリカタログの作成**: 全クエリの一覧と使用方法をまとめたドキュメントの作成
2. **パフォーマンス最適化**: 個別クエリのプロファイリングとインデックス最適化
3. **クエリバージョニング**: 複雑なクエリのバージョン管理戦略の確立
4. **自動テスト**: クエリファイルの自動構文チェックとパフォーマンステストの導入

## 注意事項

- `kuzu_py`パッケージの`load_query_from_file`関数を使用するため、このパッケージの最新バージョンが必要です
- クエリファイルのパスは相対パスで指定されているため、ファイル構造の変更には注意が必要です
- クエリファイルのエンコーディングはUTF-8で統一しています