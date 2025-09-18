# Contract E2E Testing Framework

JSON Schemaベースの契約テストフレームワーク。JSON Schemaから自動的にテストデータを生成してE2Eテストを実行します。

## Usage

### 1. スキーマファイルの準備

プロジェクトにJSON Schemaファイルを配置：

```
your-project/
├── schema/
│   ├── input.schema.json   # 入力形式の定義
│   └── output.schema.json  # 出力形式の定義
```

**input.schema.json例:**
```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string"},
    "limit": {"type": "integer", "minimum": 1, "maximum": 100}
  },
  "required": ["query"]
}
```

**output.schema.json例:**
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {"type": "string"}
    },
    "count": {"type": "integer"}
  },
  "required": ["results", "count"]
}
```

### 2. Pythonコードから使用

```python
from contract_e2e import run_contract_tests, generate_sample_from_schema

# スキーマからテストデータを自動生成
input_schema = {...}  # JSON Schemaオブジェクト
test_data = generate_sample_from_schema(input_schema)

# E2Eテストを実行
result = run_contract_tests(
    executable="./myapp",  # 実行可能ファイルのパス
    input_schema=input_schema,
    output_schema=output_schema,
    test_count=1  # テスト実行回数
)

if result["ok"]:
    print("Test passed!")
else:
    print(f"Test failed: {result}")
```

### 3. 実装要件

アプリケーションは以下を満たす必要があります：

1. **JSON入出力**
   - stdin から JSON を読み取る
   - stdout に JSON を出力する

2. **エラーハンドリング**
   - エラー時も有効なJSONを返す
   - 適切な終了コード（成功: 0、失敗: 非0）

**実装例（Python）:**
```python
import sys
import json

try:
    # 入力を読み取り
    input_data = json.load(sys.stdin)
    
    # 処理を実行
    results = search(input_data["query"], input_data.get("limit", 10))
    
    # 出力
    output = {
        "results": results,
        "count": len(results)
    }
    print(json.dumps(output))
    sys.exit(0)
    
except Exception as e:
    # エラー時もJSONで返す
    error_output = {
        "error": str(e),
        "type": "processing_error"
    }
    print(json.dumps(error_output))
    sys.exit(1)
```

## 実行例

```bash
# 開発環境で実行
cd /home/nixos/bin/src/develop/test/contract_e2e
nix develop

# テストを実行
python examples/calculator/test_e2e.py
```

## 機能

- **JSON Schemaからの自動テストデータ生成**: スキーマ定義に基づいて適切なテストデータを生成
- **プロセス実行とJSON検証**: 実際のプログラムを起動してJSON入出力を検証
- **型付きエラーハンドリング**: ProcessError, ValidationError, ParseErrorを適切に処理

## トラブルシューティング

### テストが失敗する場合

1. **JSON形式を確認**
   ```bash
   # 手動でテスト
   echo '{"query": "test"}' | ./myapp | jq .
   ```

2. **スキーマを検証**
   ```python
   # スキーマが正しいか確認
   import jsonschema
   jsonschema.validate(test_data, schema)
   ```

3. **生成されたテストデータを確認**
   ```python
   from contract_e2e import generate_sample_from_schema
   print(generate_sample_from_schema(your_schema))
   ```

## 制限事項

- 現在はPythonライブラリとしてのみ使用可能
- テストは1回ずつ実行（並列実行未対応）
- 基本的なJSON Schema機能のみサポート（複雑なスキーマは未対応の場合あり）