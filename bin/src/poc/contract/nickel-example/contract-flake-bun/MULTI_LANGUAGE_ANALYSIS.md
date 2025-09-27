# 多言語実装における契約システムの分析

## ケース1: Go言語でflake実装

### 内部実装
```go
// 契約をJSON Schemaで読み込み
type Contract struct {
    Input  json.RawMessage `json:"input"`
    Output json.RawMessage `json:"output"`
}

// 自己検証
func ValidateInput(data []byte) error {
    return schema.Validate(contractSchema, data)
}
```

### 契約定義
```yaml
# contract.yaml（言語中立）
input:
  type: object
  properties:
    items: 
      type: array
```

**評価**: Go内部でJSON Schema検証可能、TypeScript不要

## ケース2: Rust実装

### 内部実装
```rust
// serde + jsonschemaで検証
#[derive(Deserialize, Validate)]
struct Input {
    #[validate(length(min = 1))]
    items: Vec<String>,
}
```

### 特徴
- コンパイル時型検証
- ランタイム検証も可能
- **最も堅牢**

## ケース3: Python実装

### 内部実装
```python
# pydanticで検証
from pydantic import BaseModel

class Contract(BaseModel):
    items: list[str]
    
    class Config:
        schema_extra = {...}  # JSON Schema出力
```

### 特徴
- pydanticがJSON Schema生成
- 他言語との相互運用性高い

## ケース4: bashのみ実装

### 内部実装
```bash
# jqで簡易検証
validate_input() {
  echo "$1" | jq -e '.items | type == "array"'
}
```

### 限界
- 複雑なスキーマ検証不可
- エラーメッセージ貧弱
- **非推奨**

## ケース5: 言語混在システム

```
Producer: Go
Consumer: Python  
Validator: ???
```

### 解決策A: 言語中立な契約

```yaml
# contracts/api.yaml（OpenAPI形式）
paths:
  /process:
    post:
      requestBody:
        $ref: '#/components/schemas/Input'
```

各言語が独自に解釈：
- Go: `oapi-codegen`
- Python: `pydantic`
- Rust: `openapi-generator`

### 解決策B: Protocol Buffers

```protobuf
// contract.proto
message Contract {
  repeated string items = 1;
}
```

**利点**: 
- 全言語で共通定義
- 型安全
- バイナリ効率的

## 結論マトリックス

| 実装言語 | 契約定義 | 内部検証 | 外部検証の必要性 |
|---------|---------|---------|----------------|
| Go | JSON Schema | ✅ 可能 | △ 任意 |
| Rust | JSON/Proto | ✅ 強力 | ✖ 不要 |
| Python | Pydantic | ✅ 可能 | △ 任意 |
| bash | なし | ✖ 困難 | ✅ 必須 |
| 混在 | OpenAPI/Proto | ✅ 各自 | ✅ 推奨 |

## 最終提案

### 1. 契約は言語中立に

```yaml
# contract.yaml（すべてのflakeが持つ）
version: 1.0
input:
  schema: ./schemas/input.json
output:  
  schema: ./schemas/output.json
```

### 2. 各言語が自己検証

- Go: `go-jsonschema`
- Rust: `jsonschema-rs`
- Python: `jsonschema`
- TypeScript: `zod` or `ajv`

### 3. 外部検証は調停役

```bash
# 言語非依存な検証（Nix checks内）
nix flake check  # 全言語共通のテスト
```

## TypeScriptの位置づけ

**TypeScriptは選択肢の一つ**：
- 利点: Zodが優秀、エコシステム充実
- 欠点: Node.js依存、他言語との統合複雑
- **結論**: 言語中立な契約 + 各言語内部検証が理想

## 実用的な推奨

### 単一言語プロジェクト
→ その言語のベストプラクティスで検証

### 多言語プロジェクト  
→ OpenAPI or Protocol Buffers + 各言語ライブラリ

### bashスクリプト中心
→ 外部validator必須（TypeScript/Python等）

## まとめ

**契約の本質は言語非依存**：
1. 契約定義は標準形式（JSON Schema/OpenAPI/Proto）
2. 各実装が内部で契約遵守
3. 外部検証は相互運用性の保証

TypeScriptに固執する必要はない。