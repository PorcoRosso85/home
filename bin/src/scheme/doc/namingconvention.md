# スキーマシステム命名規則

## 基本原則

- ファイル名はパスカルケース（PascalCase）を基本とする
- ディレクトリ名は小文字を使用する
- ファイルおよびディレクトリ名にはハイフンを使用しない（アンダースコアも原則的に使用しない）
- ファイルの種類は拡張子の前に付与する形式を採用
- 型の選択は静的配列から選択する（例: `String`, `Struct`, `Function`）

## ファイル命名規則

### メタスキーマファイル
- パターン: `<Type>.meta.json`
- 例: `String.meta.json`, `Function.meta.json`
- 場所: `data/meta/`

### 設定ファイル
- パターン: `<概念名>.<Type>.config.json`
- 例: `Email.String.config.json`, `UserRegister.Function.config.json`
- 場所: `data/config/`

### 生成スキーマファイル
- パターン: `<概念名>.<Type>.schema.json`
- 例: `Email.String.schema.json`, `UserRegister.Function.schema.json`
- 場所: `data/generated/`

### 一時ファイル（必要な場合）
- パターン: `<概念名>.<Type>.tmp.<タイムスタンプ>.json`
- 例: `Email.String.tmp.20250321.json`
- 場所: `data/tmp/`

## 型定義

スキーマの型は以下の静的配列から選択する:

```typescript
const SchemaTypes = [
  "String",
  "Struct", 
  "Function",
  "Enum",
  "Option",
  "Result",
  "Range",
  "Tuple",
  "FixedArray",
  "Slice",
  "Boolean",
  "Character",
  "SignedInteger",
  "UnsignedInteger",
  "FloatingPoint",
  "Dynamic",
  "Generic",
  "Literal",
  "Union",
  "Async"
] as const;

type SchemaType = typeof SchemaTypes[number];
```

これにより、型安全性を確保し、一貫性のある命名規則を実現します。

## ディレクトリ命名規則

- ディレクトリ名は小文字を使用し、ハイフンやアンダースコアは使用しない
  - 例: `generated`, `config`, `meta`, `tmp`
