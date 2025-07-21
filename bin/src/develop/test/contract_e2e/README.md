# Contract E2E Testing Framework

JSON Schemaベースの契約テストフレームワーク。プロパティベーステストで網羅的なE2Eテストを自動実行します。

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

### 2. flake.nixの設定

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    contract-e2e.url = "github:yourorg/contract_e2e";
  };

  outputs = { self, nixpkgs, contract-e2e, ... }: {
    # あなたのアプリケーション
    packages.default = pkgs.writeShellScriptBin "myapp" ''
      # stdin/stdoutでJSON入出力するアプリケーション
      python ${./src/main.py}
    '';

    # E2Eテストの定義
    apps.test-e2e = contract-e2e.lib.mkContractE2ETest {
      name = "myapp";
      executable = self.packages.default;
      inputSchema = ./schema/input.schema.json;
      outputSchema = ./schema/output.schema.json;
      # オプション設定
      testCount = 200;        # デフォルト: 100
      timeout = 5000;         # ミリ秒、デフォルト: 3000
      verbose = true;         # デフォルト: false
    };
  };
}
```

### 3. 実行

```bash
# E2Eテストを実行
nix run .#test-e2e

# 特定のシードで再現
nix run .#test-e2e -- --hypothesis-seed=12345

# 詳細出力
nix run .#test-e2e -- --verbose
```

## 実装要件

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

## 高度な設定

### カスタムバリデーション

```nix
apps.test-e2e = contract-e2e.lib.mkContractE2ETest {
  # ... 基本設定 ...
  
  # カスタムバリデータ（オプション）
  customValidators = {
    # 出力の追加検証
    validateOutput = ''
      def validate_output(output):
          # カウントと結果数が一致することを確認
          assert output["count"] == len(output["results"])
    '';
  };
  
  # 特定のテストケースを除外
  excludePatterns = [
    { "query": "" }  # 空クエリは除外
  ];
};
```

### CI/CD統合

```yaml
# .github/workflows/test.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: cachix/install-nix-action@v22
      - name: Run E2E tests
        run: |
          nix run .#test-e2e -- --junit-xml=test-results.xml
      - uses: test-summary/action@v2
        with:
          paths: test-results.xml
```

## トラブルシューティング

### テストが失敗する場合

1. **JSON形式を確認**
   ```bash
   # 手動でテスト
   echo '{"query": "test"}' | nix run .#default | jq .
   ```

2. **スキーマを検証**
   ```bash
   # スキーマの妥当性チェック
   nix run .#test-e2e -- --validate-schemas-only
   ```

3. **詳細ログを確認**
   ```bash
   # デバッグ情報付きで実行
   nix run .#test-e2e -- --verbose --show-inputs
   ```

### パフォーマンス改善

```nix
# 並列実行でテスト時間短縮
apps.test-e2e = contract-e2e.lib.mkContractE2ETest {
  # ...
  parallel = true;        # 並列実行を有効化
  workers = 4;           # ワーカー数
};
```

## 最小構成例

最もシンプルな設定：

```nix
# flake.nix
{
  inputs.contract-e2e.url = "github:yourorg/contract_e2e";
  
  outputs = { self, contract-e2e, ... }: {
    apps.test-e2e = contract-e2e.lib.mkContractE2ETest {
      executable = ./myapp;
      inputSchema = ./input.schema.json;
      outputSchema = ./output.schema.json;
    };
  };
}
```

以上で、プロパティベーステストによる網羅的なE2Eテストが実行されます。