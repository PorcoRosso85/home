# アーキテクチャ設計

## 依存関係の方針

### kuzu-wasmの位置づけ
- **infrastructure層のみ**でkuzu-wasmを使用
- 他の層（domain, application, test）からは直接参照禁止
- 型変換アダプターを介した依存関係の制御

## 層の責務分離

### domain層
- ビジネスロジックの核心
- 純粋な関数とビジネス型定義
- 外部依存関係なし

### application層
- ユースケースの実装
- domain層のコンポーネントを組み合わせ
- infrastructureへのインターフェース定義

### infrastructure層
- 外部システムとの接続
- kuzu-wasmとの実際の通信
- 型変換アダプターの実装

### test層
- 各層のテスト
- インテグレーションテスト
- モックとスタブの管理

## 型変換アダプターの役割

- kuzu-wasmの型とdomain型の変換
- エラーハンドリングの統一
- パフォーマンス最適化の隠蔽

## 依存関係図

```
┌─────────────────────────────────────────────────────────────────┐
│                           test層                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  domain_test    │  │ application_test│  │infrastructure_test│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   domain層      │  │ application層   │  │infrastructure層 │
│                 │  │                 │  │                 │
│ ・ビジネス型    │  │ ・ユースケース  │  │ ・kuzu-wasm     │
│ ・ビジネス関数  │◄─┤ ・オーケストレ  │◄─┤ ・型変換アダプタ│
│ ・純粋関数      │  │   ーション      │  │ ・エラー変換    │
│                 │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘

依存の方向: application → domain
           infrastructure → domain (アダプター経由)
           test → 各層

禁止事項: domain → application/infrastructure
         application → infrastructure (直接)
         任意の層 → kuzu-wasm (infrastructure経由のみ)
```

## 実装ガイドライン

1. **依存関係の原則**
   - domain層は他の層に依存しない
   - application層はdomain層のみに依存
   - infrastructure層は型変換でdomain層を参照

2. **型変換の原則**
   - kuzu-wasmの型は infrastructure層で完全に隠蔽
   - domain型とinfrastructure型の明確な分離
   - 変換エラーの統一的処理

3. **テストの原則**
   - 各層の単体テスト
   - 層間の結合テスト
   - infrastructure層のモック化