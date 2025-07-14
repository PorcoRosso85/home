# parse_schema

Unix tool間の契約テスト。JSON Schema + ajv-cli。

```
Producer → Schema → Consumer
```

## このツールの意義

**開発時に契約を検証することで、本番環境では検証ツールが不要になる。**

これにより：
- 本番環境のオーバーヘッドなし
- 開発時に契約違反を確実に発見
- Unix哲学（シンプルなパイプ）を維持

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

## 本番環境での価値

本番では契約テストツールは不要。直接パイプ：
```bash
tool1 | tool2  # parse_schemaパッケージなし、オーバーヘッドゼロ
```

**この「不要化」こそが契約テストの成功を意味する。**
開発時の厳密な検証により、本番では安心してシンプルなパイプを使える。

`nix run .` でこのREADME表示。