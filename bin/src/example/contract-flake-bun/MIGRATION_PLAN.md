# TypeScript → JSON Schema 全面移行計画

## 現状分析

### TypeScript依存ファイル（削除対象）
```
削除予定（25ファイル中14ファイル）:
├── package.json
├── bun.lock  
├── tsconfig.json
├── src/
│   ├── contracts/
│   │   ├── command-contract.ts
│   │   ├── data-consumer.contract.ts
│   │   └── data-provider.contract.ts
│   ├── types/
│   │   └── flake-contract.ts
│   └── validator.ts
├── test/
│   └── internal-test.ts
├── test-contract-validation.ts
├── examples/command-consumer/consumer.ts
├── docs/2025-09-04_20-34-13_zod.dev_packages-mini.md
└── MULTI_LANGUAGE_ANALYSIS.md
```

### 保持・変換対象
```
保持:
├── flake.nix（修正）
├── flake.lock
├── README.md（修正）
├── examples/
│   ├── */flake.nix（各4ファイル）
│   └── */flake.lock（各4ファイル）
└── FINAL_STRUCTURE.md（削除）
```

## Baby Steps 実行計画（15-30分単位）

### Step 1: 契約定義のJSON Schema化
**時間**: 20分
**価値**: 言語非依存な契約定義の実現

#### 1.1 価値の明文化（WHY）
- TypeScript依存を排除し、任意の言語から利用可能に
- ネットワーク不要でローカル完結
- shでjqを使った簡易検証が可能

#### 1.2 仕様の定義（WHAT）【RED】
```bash
# schemas/command-contract.json が存在し、
# jqで検証可能であること
test -f schemas/command-contract.json
jq -e '.type == "object"' schemas/command-contract.json
```

#### 1.3 実現（HOW）【GREEN】
```json
# schemas/command-contract.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "command": {"type": "string"},
    "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
    "input": {
      "type": "object",
      "properties": {
        "items": {"type": "array", "items": {"type": "string"}}
      }
    },
    "output": {
      "type": "object",
      "properties": {
        "processed": {"type": "integer", "minimum": 0},
        "failed": {"type": "integer", "minimum": 0},
        "output": {"type": "array"}
      },
      "required": ["processed", "failed", "output"]
    }
  },
  "required": ["command", "version", "output"]
}
```

### Step 2: sh/jqベースのバリデータ作成
**時間**: 25分
**価値**: TypeScript不要な検証システム

#### 2.1 価値の明文化（WHY）
- Nix環境で完結する検証
- 依存関係の最小化
- CI/CDでの実行が簡単

#### 2.2 仕様の定義（WHAT）【RED】
```bash
# bin/validate.sh が実行可能で、
# JSON入力を検証できること
./bin/validate.sh '{"command": "test", "version": "1.0.0"}'
echo $? # 0 = valid
```

#### 2.3 実現（HOW）【GREEN】
```bash
#!/usr/bin/env bash
# bin/validate.sh
set -euo pipefail

SCHEMA_DIR="$(dirname "$0")/../schemas"
INPUT="$1"

# Producer契約検証
validate_producer() {
  echo "$1" | jq -e '
    .processed | type == "number" and
    .failed | type == "number" and
    .output | type == "array"
  ' > /dev/null
}

# Consumer契約検証
validate_consumer() {
  echo "$1" | jq -e '
    .summary | type == "string" and
    .details | type == "object"
  ' > /dev/null
}

# メイン検証
if validate_producer "$INPUT" 2>/dev/null; then
  echo "✅ Valid producer contract"
  exit 0
elif validate_consumer "$INPUT" 2>/dev/null; then
  echo "✅ Valid consumer contract"
  exit 0
else
  echo "❌ Invalid contract"
  exit 1
fi
```

### Step 3: flake.nix checksの移行
**時間**: 30分
**価値**: TypeScript不要なNixテスト

#### 3.1 価値の明文化（WHY）
- `nix flake check`でTypeScript不要に
- 純粋Nix環境での検証
- 高速化（bun起動不要）

#### 3.2 仕様の定義（WHAT）【RED】
```bash
nix flake check # TypeScript不使用で成功
```

#### 3.3 実現（HOW）【GREEN】
```nix
checks = {
  contract-validation = pkgs.runCommand "contract-validation" {} ''
    # Producer出力検証
    PRODUCER_OUTPUT=$(${self.packages.${system}.producer}/bin/my-go-processor)
    
    # jqで契約検証
    echo "$PRODUCER_OUTPUT" | ${pkgs.jq}/bin/jq -e '
      .processed >= 0 and 
      .failed >= 0 and
      .output | type == "array"
    '
    
    touch $out
  '';
};
```

### Step 4: 不要ファイルの削除
**時間**: 15分
**価値**: 最小構成の実現

#### 4.1 価値の明文化（WHY）
- 保守性向上
- 依存関係の削減
- 理解しやすさ

#### 4.2 仕様の定義（WHAT）【RED】
```bash
# TypeScript関連ファイルが存在しないこと
! test -f package.json
! test -f tsconfig.json
! test -d src
! test -d test
```

#### 4.3 実現（HOW）【GREEN】
```bash
rm -rf src/ test/ node_modules/
rm package.json bun.lock tsconfig.json
rm test-contract-validation.ts
rm examples/command-consumer/consumer.ts
rm docs/*.md
rm MULTI_LANGUAGE_ANALYSIS.md FINAL_STRUCTURE.md
```

### Step 5: README更新と最終確認
**時間**: 15分
**価値**: ドキュメント整合性

#### 5.1 価値の明文化（WHY）
- 新システムの使い方を明確化
- 移行完了の証明

#### 5.2 仕様の定義（WHAT）【RED】
```bash
grep -q "JSON Schema" README.md
grep -q "jq" README.md
! grep -q "TypeScript" README.md
```

## 最終的なディレクトリ構造

```
contract-flake/
├── flake.nix           # checksはsh/jq実装
├── flake.lock
├── README.md           # JSON Schema説明
│
├── schemas/            # JSON Schema契約定義
│   ├── producer.json
│   ├── consumer.json
│   └── common.json
│
├── bin/               # 検証スクリプト
│   └── validate.sh    # jqベースバリデータ
│
└── examples/          # 実装例（flakeのみ）
    ├── command-producer/
    │   ├── flake.nix
    │   └── flake.lock
    ├── command-consumer/
    │   ├── flake.nix
    │   └── flake.lock
    ├── data-provider-flake/
    │   ├── flake.nix
    │   └── flake.lock
    └── data-consumer-flake/
        ├── flake.nix
        └── flake.lock
```

## 実行コマンド順序

```bash
# Step 1: JSON Schema作成
mkdir schemas
vim schemas/command-contract.json

# Step 2: バリデータ作成
mkdir bin
vim bin/validate.sh
chmod +x bin/validate.sh

# Step 3: flake.nix修正
vim flake.nix

# Step 4: 不要ファイル削除
rm -rf src test node_modules
rm package.json bun.lock tsconfig.json test-contract-validation.ts
rm examples/command-consumer/consumer.ts
rm docs/*.md MULTI_LANGUAGE_ANALYSIS.md FINAL_STRUCTURE.md

# Step 5: README更新
vim README.md

# 最終確認
nix flake check
```

## 合計時間
- Step 1: 20分
- Step 2: 25分
- Step 3: 30分
- Step 4: 15分
- Step 5: 15分
- **合計: 105分（約1時間45分）**

## リスクと対策
- **リスク**: JSON Schemaの表現力不足
- **対策**: 必要最小限の検証に絞る（YAGNI原則）

## 成功基準
1. TypeScriptファイルが0
2. `nix flake check`が成功
3. jqのみで契約検証可能
4. ネットワーク不要で動作