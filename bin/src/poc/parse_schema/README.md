# parse_schema

Unix tool間の契約テスト。JSON Schema + ajv-cli。

```
Producer → Schema → Consumer
```

## 意義

**開発時に契約を検証 → 本番では検証ツール不要 → オーバーヘッドゼロ**

## 責務

**【内】検証実行・結果報告・ツール提供**  
**【外】スキーマ定義・データ変換・本番使用**

## CLI使用

```bash
test-producer schema.json ./my-logger     # Producer検証
test-consumer schema.json sample.json     # Consumer検証  
contract-test schema.json ./producer ./consumer  # 統合
```

## pytest統合

```python
# test_output_contract.py
import subprocess
from pathlib import Path

def test_my_tool_output():
    """自ツールの出力契約を検証"""
    result = subprocess.run([
        "nix", "run", "../parse_schema#test-producer", "--",
        "output_schema.json",      # 自ツールのスキーマ
        "./my-tool"                # 自ツールの実行
    ], capture_output=True)
    assert result.returncode == 0
```

## 本番

```bash
tool1 | tool2  # 検証済み、parse_schemaなし
```

**「検証ツールの不要化」＝成功**