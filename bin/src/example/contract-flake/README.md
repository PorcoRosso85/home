# Flake Contract System

## 責務

このシステムは、レベル3マルチFlake構成に基づく型安全な契約定義を提供します。

### アーキテクチャレベル

#### レベル3: 真のマルチFlake構成（推奨）
- **buildInputsによるPATH自動管理**
- **パス解決からの完全解放**
- **コマンド名のみでの実行**

### 主要責務の分離

1. **Nix層の責務**
   - 依存Flakeの解決とダウンロード
   - buildInputsを通じたPATH自動管理
   - パス解決の完全自動化
   - 言語非依存のFlake実装をサポート

2. **Zod契約層の責務**
   - 純粋な契約定義（パス情報を含まない）
   - 入出力データの型定義
   - 実行時契約検証
   - コマンド名のみの宣言

3. **TypeScript実行層の責務**
   - コマンド名だけで実行（例: `spawn(['my-go-app'])`）
   - ビジネスロジックに集中
   - パス管理から完全に解放
   - 純粋なデータ変換

4. **Glue層の責務**
   - 最小限の薄い検証のみ
   - データ変換なし
   - ビジネスロジックなし
   - 契約の整合性確認のみ

## アーキテクチャ

```
src/
├── types/
│   └── flake-contract.ts         # 基本的なFlake契約の型定義
├── contracts/
│   ├── data-provider.contract.ts # Zodベースのデータプロバイダ契約
│   ├── data-consumer.contract.ts # Zodベースのデータコンシューマ契約
│   └── level3-contract.ts       # レベル3マルチFlake契約定義
└── glue/
    ├── flake-glue.ts             # フル機能のglue実装
    └── minimal-glue.ts           # 最小限の薄いglue実装

examples/
├── data-provider-flake/          # 構造データを提供するflake
│   └── flake.nix                # 言語非依存の実装
├── data-consumer-flake/          # データを消費・処理するflake
│   └── flake.nix                # jqベースの処理実装
├── level3-producer/              # レベル3: コマンド提供flake
│   └── flake.nix                # PATH管理されたコマンド
└── level3-consumer/              # レベル3: コマンド利用flake
    └── flake.nix                # buildInputsによる自動PATH解決
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

## レベル3実装例

### Producer Flake (go-app/flake.nix)
```nix
{
  outputs = { self, nixpkgs, ... }:
    let pkgs = nixpkgs.legacyPackages.${system};
    in {
      packages.default = pkgs.buildGoModule {
        pname = "my-go-app";
        # コマンド名として 'my-go-app' が PATH に追加される
        # パスを意識する必要なし
      };
    };
}
```

### Consumer Flake (bun-app/flake.nix)
```nix
{
  inputs.go-app.url = "github:my-org/go-app";
  
  outputs = { self, go-app, ... }:
    let pkgs = nixpkgs.legacyPackages.${system};
    in {
      packages.default = pkgs.stdenv.mkDerivation {
        buildInputs = [ 
          go-app.packages.${system}.default  # PATHに自動追加
          pkgs.bun
        ];
        
        buildPhase = ''
          # go-appコマンドが既にPATHに存在
          # パス指定不要
          bun build ./src/index.ts --outfile dist/bundle.js
        '';
      };
    };
}
```

### TypeScript実装 (src/index.ts)
```typescript
import { z } from 'zod';
import { spawn } from 'child_process';

// 契約: コマンド名のみ（パスなし）
const AppContract = z.object({
  command: z.literal('my-go-app'),  // パスではなくコマンド名
  inputs: z.object({ /* ... */ }),
  outputs: z.object({ /* ... */ })
});

// 実行: コマンド名だけ
await spawn(['my-go-app', '--process', data]);
// パス解決はNixが自動で行う
```

## 設計思想

### レベル3マルチFlakeの原則

1. **パス透過性**: アプリケーションコードはパスを意識しない
2. **責務の純粋性**: 各層は自身の責務のみに集中
3. **自動管理**: NixがすべてのPATH管理を自動化
4. **契約の簡潔性**: 契約にパス情報を含めない

### 薄いGlue層の原則

このシステムの核心は「可能な限り薄いglue層」です：

1. **検証のみ、変換なし**: Glueは契約検証のみを行い、データ変換は行いません
2. **Pass-through設計**: データは検証後、そのまま通過します
3. **ビジネスロジックなし**: Glue層にビジネスロジックは含まれません
4. **言語非依存**: Flakeの実装言語は問いません（Bash、Python、Go等）

### 契約による設計

- **Zodスキーマ**: 実行時の型安全性を保証（パス情報を含まない）
- **明示的契約**: すべての入出力は契約で定義（コマンド名のみ）
- **コンパイル時検証**: TypeScriptによる静的型チェック
- **実行時検証**: Zodによる動的検証

このシステムは「契約による設計」と「レベル3マルチFlake構成」の原則に基づき、パス管理から完全に解放された大規模なNixシステムの構築を支援します。