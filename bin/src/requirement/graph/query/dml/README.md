# DML (Data Manipulation Language) ディレクトリ

このディレクトリには、KuzuDB用のデータ操作言語（DML）Cypherクエリファイルを格納します。
DMLクエリはデータの挿入、更新、削除などの操作に使用されます。

[クエリモジュール全体の説明に戻る](../README.md)

## 使用方法

このディレクトリには次のファイルが含まれます：

1. `*.json` - エンティティ定義ファイル（DML生成のソース）
2. `*.cypher` - 生成されたDMLクエリファイル
3. `templates/` - DMLクエリ生成に使用されるテンプレート

## 自動DML生成

DDLに基づいてDMLを生成するには、以下の手順に従います：

1. JSONエンティティ定義ファイルを作成（例: `entity_name.json`）:

```json
{
  "entity_type": "node",  // "node" または "edge"
  "table_name": "EntityName",
  "templates": ["create", "match", "update"],
  "properties": {
    "id": {
      "type": "string",
      "primary_key": true
    },
    "name": {
      "type": "string"
    }
  }
}
```

2. DML生成ツールを実行:

```bash
cd /home/nixos/bin/src/kuzu/query
./dml_generator.py --entity dml/entity_name.json
```

または、すべてのエンティティのDMLを一括生成:

```bash
./dml_generator.py --all
```

## カスタムテンプレート

独自のDMLテンプレートを作成するには:

1. `templates/` ディレクトリにテンプレートファイルを作成（例: `custom_operation.cypher`）
2. テンプレート内でプレースホルダーを使用（例: `{table_name}`, `{properties}`）
3. JSONエンティティ定義で新しいテンプレートを指定（例: `"templates": ["create", "custom_operation"]`）

## 言語に依存しない使用方法

1. Pythonから:
```python
from query.call_cypher import create_query_loader

loader = create_query_loader()
result = loader["execute_query"](connection, "create_entityname", {
    "id": "12345",
    "name": "テスト名"
})
```

2. TypeScriptから:
```typescript
import { executeQuery } from '../query/mod.ts';

const result = await executeQuery(
  connection, 
  "create_entityname", 
  { id: "12345", name: "テスト名" }
);
```
