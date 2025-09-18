# Bun Development Environment Flake

## 責務

このFlakeは、Bunベースのプロジェクトに対して以下を提供します：

1. **Bun実行環境**
   - 最新のBunランタイム
   - Node.js互換性レイヤー

2. **開発ツール**
   - TypeScript言語サーバー (typescript-language-server)
   - Linter (ESLint/Biome)
   - Formatter (Prettier/Biome)
   - その他の開発支援ツール

3. **統一された開発環境**
   - このFlakeに依存・継承するすべてのプロジェクトで一貫した開発環境を保証
   - バージョンの固定と再現性の確保

## 使用方法

他のプロジェクトのflake.nixから以下のように参照します：

```nix
{
  inputs = {
    bun-env.url = "path:../flakes/bun";
    # または
    # bun-env.url = "github:your-org/your-repo?dir=src/flakes/bun";
  };

  outputs = { self, bun-env, ... }: {
    # bun-env.packages.${system}.bunEnv を使用
  };
}
```

## 提供パッケージ

- `bunEnv`: Bunランタイム
- `typescript-language-server`: TypeScript LSP（型チェックと補完）
- `biome`: 高速なlinter/formatter（TypeScriptコンパイラ不要）

## 設計方針

- **最小限の依存**: 必要最小限のツールのみを提供
- **高速性**: Bunエコシステムに最適化された高速なツールを優先
- **互換性**: 既存のNode.js/TypeScriptプロジェクトとの互換性を維持