# Similarity Detection Tool Flake

## Flakeの責務

このNix flakeは以下の責務を持ちます：

1. **非クローン原則**: Nixの標準的なfetchやbuildフェーズを使用せず、実行時に動的にツールを取得
2. **構造化された出力**: Nixのflake出力仕様に準拠した明確な構造

## Flake構造

### inputs（入力）

```nix
{
  nixpkgs      # Nixパッケージコレクション
  flake-utils  # マルチシステム対応ユーティリティ
  similarity   # 上流リポジトリ（README表示用のみ、ビルドには使用しない）
}
```

重要：`similarity`入力はREADME表示のためだけに使用され、実際のツールは実行時に`cargo install --git`で直接インストールします。

### outputs（出力）

#### apps（実行可能アプリケーション）

| Output | 型 | 説明 | Nix flakeでの役割 |
|--------|---|------|-----------------|
| `apps.default` | app | README表示 | flakeのデフォルト動作定義 |
| `apps.similarity` | app | 使用方法案内 | 統合エントリーポイント |
| `apps.ts` | app | TypeScript解析 | 特定言語向け機能の分離 |
| `apps.py` | app | Python解析 | 特定言語向け機能の分離 |
| `apps.rs` | app | Rust解析 | 特定言語向け機能の分離 |
| `apps.test` | app | テスト実行 | 品質保証機能の提供 |

#### devShells（開発環境）

| Output | 型 | 説明 |
|--------|---|------|
| `devShells.default` | shell | 開発に必要な依存関係を含む環境 |

## Flakeの設計原則

### 1. 純粋性の緩和

通常のNix flakeは完全な再現性を保証しますが、このflakeは：

- **ビルド時固定** → **実行時取得**
- **Nixストア管理** → **ユーザーキャッシュ管理**
- **宣言的定義** → **命令的実行**

### 2. flake-utilsによるマルチプラットフォーム対応

```nix
flake-utils.lib.eachDefaultSystem (system: ...)
```

これにより以下のシステムで自動的に動作：
- `x86_64-linux`
- `aarch64-linux`
- `x86_64-darwin`
- `aarch64-darwin`

### 3. writeShellScriptBinパターン

各appは`writeShellScriptBin`で作成されたシェルスクリプト：

```nix
apps.名前 = {
  type = "app";
  program = "${pkgs.writeShellScriptBin "名前" ''
    # シェルスクリプト
  ''}/bin/名前";
};
```

このパターンにより：
- 実行可能ファイルの動的生成
- 環境変数の適切な設定
- エラーハンドリングの実装

## Flake出力の仕組み

### app型の構造

Nix flakeにおける`app`型は以下の構造を持つ：

```nix
{
  type = "app";
  program = "実行可能ファイルへのパス";
}
```

このflakeでは、`program`に`writeShellScriptBin`の出力を指定することで、動的にシェルスクリプトを生成・実行しています。

### 引数処理の違い

- **default app**: 引数を受け付けない（`$# -ne 0`でエラー）
- **その他のapp**: `"$@"`で全引数を下流コマンドに渡す

### 環境変数の管理

各appは独自の環境変数を設定：

```bash
export PATH="${pkgs.cargo}/bin:${pkgs.rustc}/bin:$PATH"
export CARGO_HOME="${XDG_CACHE_HOME:-$HOME/.cache}/cargo"
export RUSTUP_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/rustup"
```

これにより、システムの環境を汚染せずに実行環境を構築。

## 使用方法

### 統合エントリーポイント

```bash
# 使用方法の確認
nix run /home/nixos/bin/src/poc/similarity#similarity
```

### 言語別の実行

```bash
# TypeScriptファイルの類似性検出
nix run /home/nixos/bin/src/poc/similarity#ts -- ./src

# Pythonファイルの類似性検出
nix run /home/nixos/bin/src/poc/similarity#py -- ./python_project

# Rustファイルの類似性検出
nix run /home/nixos/bin/src/poc/similarity#rs -- ./rust_src
```

## Flakeの利点

### 1. 宣言的なインターフェース

```bash
# 一貫した実行方法
nix run .#similarity  # 使用方法を表示
nix run .#ts         # TypeScript版を実行
nix run .#py         # Python版を実行
nix run .#rs         # Rust版を実行
```

### 2. 依存関係の自動解決

`devShells.default`により、必要なツールが自動的に利用可能：

```nix
buildInputs = with pkgs; [
  cargo
  rustc
  pkg-config
  openssl
];
```

### 3. 再現可能な開発環境

`flake.lock`により、使用するnixpkgsのバージョンが固定され、チーム間で同一の環境を保証。

## 通常のNix flakeとの違い

### 標準的なRust flake

```nix
# 通常のアプローチ
packages.default = pkgs.rustPlatform.buildRustPackage {
  pname = "similarity";
  src = similarity;
  cargoSha256 = "...";
};
```

### このflakeのアプローチ

```nix
# 実行時インストール
apps.ts = {
  program = "${pkgs.writeShellScriptBin "similarity-ts" ''
    cargo install --git https://github.com/mizchi/similarity similarity-ts
  ''}/bin/similarity-ts";
};
```

主な違い：
- **ビルド時** vs **実行時**
- **Nixストア管理** vs **ユーザーディレクトリ管理**
- **完全な純粋性** vs **実用性重視**

## テスト

E2Eテストによりすべての機能が動作することを保証：

```bash
# テストの実行
nix run .#test
```

テスト構造：
```
e2e/internal/
├── test_e2e_similarity_app.py  # 統合アプリのテスト
├── test_e2e_ts_similarity.py   # TypeScript版のテスト
├── test_e2e_py_similarity.py   # Python版のテスト
└── test_e2e_rs_similarity.py   # Rust版のテスト
```

## 関連リソース

- [Nix flakes仕様](https://nixos.wiki/wiki/Flakes)
- [flake-utils](https://github.com/numtide/flake-utils)
- [writeShellScriptBin](https://nixos.org/manual/nixpkgs/stable/#trivial-builder-writeShellScriptBin)
- [上流リポジトリ](https://github.com/mizchi/similarity)