# Similarity Detection Tool Flake

## 責務

このflakeは以下の責務を持ちます：

1. **非クローン原則**: リポジトリをクローンせず、`cargo install --git`を使用して直接インストール
2. **言語別ツールの提供**: ts/py/rs各言語版の独立したツールを提供

## 使用方法

### README表示（デフォルト）
```bash
nix run /home/nixos/bin/src/poc/similarity
```

### TypeScript/JavaScript向け
```bash
nix run /home/nixos/bin/src/poc/similarity#ts -- ./src
```

### Python向け
```bash
nix run /home/nixos/bin/src/poc/similarity#py -- ./python_project
```

### Rust向け
```bash
nix run /home/nixos/bin/src/poc/similarity#rs -- ./rust_src
```

## 実装詳細

- **入力**: `similarity`（github:mizchi/similarity）
- **出力**: 
  - `apps.default`（README表示）
  - `apps.ts`（TypeScript向け類似度検出）
  - `apps.py`（Python向け類似度検出）
  - `apps.rs`（Rust向け類似度検出）
- **特徴**: 初回実行時にツールをインストール、以降はキャッシュを使用