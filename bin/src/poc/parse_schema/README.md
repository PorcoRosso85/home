# parse_schema

Unix tool間の契約テスト。JSON Schema + ajv-cli。

```
Producer → Schema → Consumer
```

## 使用例（従来のCLI）

```bash
# 環境準備
nix develop

# Producer出力を検証
test-producer schema.json ./my-logger

# Consumer入力を検証  
test-consumer schema.json sample.json

# 統合テスト
contract-test schema.json ./producer ./consumer
```

## LLM-firstな使用例

```bash
# Producer検証（JSON入力）
echo '{
  "type": "validate_producer",
  "schema": {
    "type": "object",
    "required": ["message", "level"],
    "properties": {
      "message": {"type": "string"},
      "level": {"enum": ["INFO", "WARN", "ERROR"]}
    }
  },
  "producer": "echo {\"message\":\"test\",\"level\":\"INFO\"}"
}' | nix run .#run

# 統合テスト（JSON入力）
echo '{
  "type": "contract_test",
  "schema": {
    "type": "object",
    "required": ["timestamp", "data"],
    "properties": {
      "timestamp": {"type": "string"},
      "data": {"type": "object"}
    }
  },
  "producer": "./my-producer.sh",
  "consumer": "./my-consumer.sh"
}' | nix run .#run
```

## テスト実行

```bash
# pytestで実行
nix run .#test

# または開発環境で
python -m pytest test_contract.py -v
```

`nix run .` でこのREADME表示。