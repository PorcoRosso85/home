# Similarity Detection Tool Flake

## 責務

このflakeの唯一の責務：上流リポジトリのREADMEを表示する。

## 使用方法

```bash
nix run /home/nixos/bin/src/poc/similarity
```

## 実装詳細

- **入力**: `similarity`（github:mizchi/similarity）
- **出力**: `apps.default`（README表示のみ）
- **依存**: 最小限（nixpkgs、flake-utils、上流リポジトリ）

ツール自体の使用は上流の指示に従ってください。