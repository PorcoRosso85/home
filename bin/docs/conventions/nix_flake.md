# Nix Flake規約

## 原則

**最小限のFlake構成で、再現可能な開発環境を提供する。**

## 基本構造

```nix
{
  description = "簡潔な説明";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # 開発環境
        devShells.default = pkgs.mkShell { ... };
        
        # 実行可能アプリケーション
        apps.default = { ... };
        apps.test = { ... };
        
        # パッケージ
        packages.default = ...;
      });
}
```

## 環境の継承

### 親flakeの利用
共通の言語環境は `bin/src/flakes/<言語名>/` から継承する：

```nix
inputs = {
  nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  flake-utils.url = "github:numtide/flake-utils";
  python-flake.url = "path:/home/nixos/bin/src/flakes/python";
};

outputs = { self, nixpkgs, flake-utils, python-flake }:
  flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
      # 親flakeから環境を継承
      pythonEnv = python-flake.packages.${system}.pythonEnv;
    in
    {
      # pythonEnvを使用した実装
    });
```

### バージョン管理の原則
- 言語バージョンは親flakeで一元管理
- 子flakeでは親から継承し、バージョンをハードコードしない
- 例外的にバージョン指定が必要な場合は、inputsで明示的に定義

## Python プロジェクトのFlake化

### 問題と解決策

1. **相対インポート問題**
   - 問題: Pythonの相対インポートがNix環境で動作しない
   - 解決: スタンドアロンスクリプトを作成
   
   ```python
   # search_standalone.py - 単一ファイルで完結
   #!/usr/bin/env python3
   # 全ての型定義と実装を含む
   ```

2. **実行可能コマンド**
   ```nix
   # writeScriptBinを使用（シンプル）
   search-symbols = pkgs.writeScriptBin "command-name" ''
     #!${pythonEnv}/bin/python
     ${builtins.readFile ./standalone.py}
   '';
   ```

3. **テスト実行**
   
   標準パターン（推奨）：
   ```nix
   test = {
     type = "app";
     program = "${pkgs.writeShellScript "test" ''
       # ソースディレクトリで実行
       cd ${./.}
       exec ${pythonEnv}/bin/pytest -v "$@"
     ''}";
   };
   ```
   
   書き込み権限が必要な場合：
   ```nix
   test = {
     type = "app";
     program = "${pkgs.writeShellScript "test" ''
       # 一時ディレクトリで実行（書き込み権限の問題を回避）
       export TMPDIR=$(mktemp -d)
       cd $TMPDIR
       
       # ソースとテストファイルをコピー
       cp -r ${./.}/* .
       
       # テストファイルは同じディレクトリに配置されているため
       ${pythonEnv}/bin/pytest test_*.py
       
       rm -rf $TMPDIR 2>/dev/null || true
     ''}";
   };
   ```

## POC例

### Node.js CLIツール（readability）
```bash
bin/src/poc/readability/
├── flake.nix    # npm CLIツールのラッパー
├── .envrc       # use flake
└── .gitignore   # node_modules/, .direnv/
```

使用例：
```bash
nix run ~/bin/src/poc/readability -- -o article.md https://example.com
```

## 必須ファイル

1. `flake.nix` - Flake定義
2. `.envrc` - direnv統合（内容: `use flake`）
3. `.gitignore` - Nix/Python関連の除外設定
   ```
   .direnv/
   __pycache__/
   *.pyc
   .pytest_cache/
   .mypy_cache/
   .coverage
   .ruff_cache/
   ```

## コマンド規約

### 実行方法の選択

#### nix run（推奨）
完成したツールやCLIアプリケーションに最適。

```nix
apps = {
  default = {
    type = "app";
    program = "${package}/bin/command";
  };
};
```

使用例：
```bash
nix run . -- arg1 arg2
nix run .#app-name -- arg1
```

#### nix develop
開発環境構築やデバッグ用途に最適。

```nix
devShells.default = pkgs.mkShell {
  buildInputs = [ package dependencies ];
  shellHook = ''
    echo "開発環境へようこそ"
  '';
};
```

### 必須コマンド
- `nix run .` - デフォルトアプリケーション実行（必ずREADME.mdを表示）
- `nix run .#test` - テスト実行
- `nix develop` - 開発シェル

### エラーハンドリング規約
- 存在しないアプリケーション指定時：エラーメッセージとともにREADME.mdを表示
- デフォルトアプリにオプション引数指定時：エラーメッセージとともにREADME.mdを表示

### 推奨コマンド（言語別）
#### Python
- `nix run .#format` - black/ruff format
- `nix run .#lint` - ruff check
- `nix run .#typecheck` - mypy

#### TypeScript/JavaScript
- `nix run .#format` - deno fmt
- `nix run .#lint` - deno lint
- `nix run .#typecheck` - deno check

#### Nushell
- CLIエントリポイントは`def main`を使用
- 出力は`to json | print`でJSON形式に

## 言語別の標準構成

### Python
- **テストランナー**: pytest（標準）
- **フォーマッター**: black, ruff
- **型チェッカー**: mypy
- **親flake**: `bin/src/flakes/python/flake.nix`

### TypeScript/Deno
- **テストランナー**: deno test
- **フォーマッター**: deno fmt
- **型チェッカー**: deno check
- **親flake**: 将来的に `bin/src/flakes/typescript/flake.nix`

### 詳細実装の参照
具体的な実装例は `bin/src/flakes/` の各言語テンプレートを参照

## Node.js/npm CLIツールのFlake化

### 問題と解決策

1. **npxの実行環境問題**
   - 問題: nixパッケージ内でnpxが正しく動作しない
   - 解決: npmの環境変数を適切に設定
   
   ```nix
   readabilityWrapper = pkgs.writeShellScriptBin "readability" ''
     export PATH="${nodejs}/bin:${nodePackages.npm}/bin:$PATH"
     export NPM_CONFIG_CACHE="''${XDG_CACHE_HOME:-$HOME/.cache}/npm"
     export NPM_CONFIG_PREFIX="''${XDG_DATA_HOME:-$HOME/.local/share}/npm"
     
     mkdir -p "$NPM_CONFIG_CACHE" "$NPM_CONFIG_PREFIX/bin"
     export PATH="$NPM_CONFIG_PREFIX/bin:$PATH"
     
     # 初回実行時のみインストール
     if ! command -v readability &> /dev/null; then
       echo "Installing @mizchi/readability..." >&2
       ${nodePackages.npm}/bin/npm install -g @mizchi/readability
     fi
     
     exec readability "$@"
   '';
   ```

2. **ポータビリティの確保**
   - 問題: システムのnpmに依存すると環境依存になる
   - 解決: nixpkgsのnodejsとnpmを明示的に使用

3. **キャッシュの永続化**
   - 問題: 毎回npmパッケージをダウンロードする
   - 解決: `$HOME/.cache/npm`と`$HOME/.local/share/npm`を使用

## エラーハンドリング

1. **Git未追跡ファイル**
   - エラー: "Path ... is not tracked by Git"
   - 解決: `git add`でファイルを追跡

2. **読み取り専用ファイルシステム**
   - エラー: "Read-only file system"
   - 解決: 一時ディレクトリで実行

3. **モジュールインポートエラー**
   - エラー: "No module named ..."
   - 解決: スタンドアロン実装を使用

## アンチパターン

- ❌ 複雑な`mkDerivation`の使用
- ❌ 相対インポートに依存した構造
- ❌ ハードコードされたパス
- ❌ 環境依存の前提条件
- ❌ 言語バージョンのハードコード（例: `pkgs.python312` を直接使用）
- ❌ 共通環境の重複定義

## ベストプラクティス

- ✅ `writeScriptBin`でシンプルに
- ✅ スタンドアロンスクリプトで相対インポート回避
- ✅ 通常はソースディレクトリでテスト実行（特殊な場合のみ一時ディレクトリ）
- ✅ 明確なエラーメッセージ
- ✅ `nix run`をメインの実行方法として設計
- ✅ 複数実装がある場合は`apps.default`で主要実装を指定
- ✅ デフォルトコマンドは必ずREADME.mdを表示（エラー時も含む）
- ✅ 言語環境は親flakeから継承
- ✅ バージョン管理は親flakeで一元化

## Nushellスクリプトの統合

### スクリプトファイルの埋め込み
```nix
nuScript = pkgs.writeTextFile {
  name = "script.nu";
  text = builtins.readFile ./script.nu;
  executable = false;
};

app = pkgs.writeShellScriptBin "app-name" ''
  export PATH="${pkgs.lib.makeBinPath [pkgs.universal-ctags]}:$PATH"
  exec ${pkgs.nushell}/bin/nu ${nuScript} "$@"
'';
```

### 複数言語実装の共存
```nix
apps = {
  # デフォルト（推奨実装）
  default = {
    type = "app";
    program = "${nushell-app}/bin/app";
  };
  
  # 代替実装
  python = {
    type = "app";
    program = "${python-app}/bin/app";
  };
};
```