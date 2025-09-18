# Flake Contract System

## 目的

**すべてのFlakeが契約を定義し、その契約に基づいて接続可能であることを実証**

### 核心価値
1. どのflakeも契約を忘れないための例示
2. 忘れずに契約を提示したflakeは契約ができることの証明

## 責務

このシステムは、コマンドベースのマルチFlake構成に基づく型安全な契約定義を提供します。

### 主要責務の分離

1. **Nix層の責務**
   - 依存Flakeの解決とダウンロード
   - buildInputsを通じたPATH自動管理
   - パス解決の完全自動化

2. **契約層の責務**
   - 入出力データの型定義
   - 実行時契約検証
   - コマンド名のみの宣言

3. **検証層の責務**
   - 契約の整合性確認
   - 最小限の検証のみ
   - ビジネスロジックなし

## アーキテクチャ

```
src/
├── contracts/      # 契約定義
├── validator.ts    # 契約検証
└── types/          # 共通型定義
```

## 使用方法

### 契約定義

```typescript
// コマンド契約の定義
const contract = {
  command: 'my-processor',
  version: '1.0.0',
  capabilities: ['json-processing']
};
```

### 契約検証

```typescript
import { createValidator } from './src/validator';

const validator = createValidator(producerContract, consumerContract);
const result = validator.validateCompatibility();

if (result.success) {
  console.log('✓ 契約は有効です');
}
```

## 実行

```bash
# 開発環境
nix develop

# テスト実行
bun test

# 契約検証デモ
bun run src/validator.ts
```

## 設計原則

- **KISS**: 最小限の検証機能のみ
- **DRY**: 契約定義の再利用
- **SOLID**: 単一責務（契約検証）
- **YAGNI**: 必要な機能のみ実装

## 成果

このシステムは以下を証明します：
- 契約を定義したFlakeは相互接続可能
- 型安全性とランタイム検証の両立
- 最小限のコードで十分な保証を提供