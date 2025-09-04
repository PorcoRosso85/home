# Flake Contract System

## 責務

このシステムは、Nix flakesに対する型安全な契約定義とglue機能を提供します。

### 主要責務

1. **Flake契約の型定義**
   - Nix flakeのinputs/outputsをTypeScriptの型システムで表現
   - 型レベルでflake間の依存関係を保証
   - **Zodスキーマによる実行時契約検証**

2. **Flake Glue機能**
   - 複数のflakeを型安全に結合
   - flake間のインターフェース整合性を実行時に検証
   - **最小限の薄いglue層による結合**

3. **構造データの統合**
   - **構造データを出力する複数flakeの統合**
   - **Zod型制約による契約ベースの結合**
   - **言語非依存のflake実装をサポート**

4. **将来的なCLI拡張**
   - Bunによる高速実行環境
   - LLM-firstな操作体系への進化

## アーキテクチャ

```
src/
├── types/
│   └── flake-contract.ts         # 基本的なFlake契約の型定義
├── contracts/
│   ├── data-provider.contract.ts # Zodベースのデータプロバイダ契約
│   └── data-consumer.contract.ts # Zodベースのデータコンシューマ契約
└── glue/
    ├── flake-glue.ts             # フル機能のglue実装
    └── minimal-glue.ts           # 最小限の薄いglue実装

examples/
├── data-provider-flake/          # 構造データを提供するflake
│   └── flake.nix                # 言語非依存の実装
└── data-consumer-flake/          # データを消費・処理するflake
    └── flake.nix                # jqベースの処理実装
```

## 契約システムの原則

### 1. 型による契約
各flakeは`FlakeContract`型を実装し、以下を宣言します：
- 必要なinputs（依存flake）
- 提供するoutputs（成果物）
- 実装するcapabilities（機能）

### 2. 実行時検証
glueシステムは実行時に以下を検証：
- inputsの存在確認
- outputsの型整合性
- capabilitiesの互換性

### 3. 段階的拡張
現在：型定義とglue機能
将来：CLIツール、LLM統合、自動契約生成

## 使用方法

### 開発環境
```bash
nix develop
```

### 型チェック
```bash
bun run type-check
```

### 実行
```bash
# フル機能のglue
bun run src/glue/flake-glue.ts

# 最小限のglue
bun run src/glue/minimal-glue.ts
```

### サンプルflakeの使用
```bash
# データプロバイダのビルド
cd examples/data-provider-flake
nix build

# データコンシューマのビルド
cd examples/data-consumer-flake
nix build
```

## 設計思想

### 薄いGlue層の原則

このシステムの核心は「可能な限り薄いglue層」です：

1. **検証のみ、変換なし**: Glueは契約検証のみを行い、データ変換は行いません
2. **Pass-through設計**: データは検証後、そのまま通過します
3. **ビジネスロジックなし**: Glue層にビジネスロジックは含まれません
4. **言語非依存**: Flakeの実装言語は問いません（Bash、Python、Go等）

### 契約による設計

- **Zodスキーマ**: 実行時の型安全性を保証
- **明示的契約**: すべての入出力は契約で定義
- **コンパイル時検証**: TypeScriptによる静的型チェック
- **実行時検証**: Zodによる動的検証

このシステムは「契約による設計」の原則に基づき、flake間の接続を明示的かつ型安全にすることで、大規模なNixシステムの構築を支援します。