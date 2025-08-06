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

## パッケージ中心設計の原則

### なぜパッケージを中心に置くべきか

**パッケージ定義は、Nix Flakeにおける「唯一の真実の源（Single Source of Truth）」として機能します。**

1. **再利用性の最大化**
   - `nix shell`での直接利用
   - `nix run`でのアプリケーション実行
   - 外部flakeからの参照（buildInputs）
   - devShellへの組み込み

2. **DRY原則の徹底**
   ```nix
   # ❌ アンチパターン：重複定義
   devShells.default = pkgs.mkShell {
     buildInputs = [ bash shellcheck bats shfmt ];  # 重複
   };
   packages.default = pkgs.buildEnv {
     paths = [ bash shellcheck bats shfmt ];  # 重複
   };

   # ✅ ベストプラクティス：パッケージを参照
   packages.default = pkgs.buildEnv {
     name = "my-tools";
     paths = [ bash shellcheck bats shfmt ];
   };
   devShells.default = pkgs.mkShell {
     buildInputs = [ self.packages.${system}.default ];
   };
   ```

3. **外部参照の簡潔性**
   ```nix
   # 外部flakeでの利用が単純明快
   inputs.bash-dev.url = "github:user/bash-dev";
   buildInputs = [ bash-dev.packages.${system}.default ];
   ```

4. **段階的拡張の容易さ**
   - 基本：packageのみ提供
   - 必要に応じて：devShell追加（環境変数・shellHook）
   - 高度な統合：overlay提供

## パッケージとOverlayの提供

### 設計の優先順位

1. **packages（必須）** - すべてのflakeはパッケージを提供すべき
2. **devShells（推奨）** - パッケージを参照し、開発環境固有の設定を追加
3. **overlays（オプション）** - 特殊な統合が必要な場合のみ

### 基本方針
- **パッケージ定義を唯一の真実の源とする**: `packages.default`にツールセットを集約
- **他の出力はパッケージを参照**: devShellもoverlayもパッケージを基点に構築
- **Overlayは補助的に提供**: 以下のケースではoverlayの提供を検討

### Overlayが適切なケース
1. **複数パッケージの統合利用**
   - 関連する複数のパッケージを一括で提供する場合
   - 例: Pythonパッケージと関連ツールのセット

2. **既存パッケージの拡張**
   - nixpkgsの既存パッケージを拡張・修正する場合
   - 例: `pythonPackagesExtensions`による拡張

3. **ライブラリとしての提供**
   - 他のflakeから再利用されることを前提とした汎用ライブラリ
   - 例: ログライブラリ、共通ユーティリティ

### 実装例
```nix
{
  outputs = { self, nixpkgs, flake-utils }:
    let
      # Overlay定義（必要な場合のみ）
      overlay = final: prev: {
        myPackage = final.callPackage ./. {};
        # Pythonパッケージの場合
        pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
          (python-final: python-prev: {
            myPythonLib = python-final.buildPythonPackage { ... };
          })
        ];
      };
    in
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ overlay ];  # 自身のoverlayを適用
        };
      in
      {
        # パッケージ提供（基本）
        packages.default = pkgs.myPackage;
        
        # Overlay提供（適切な場合のみ）
        overlays.default = overlay;
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

#### nix run
アプリケーションパッケージとして配布する場合に使用。

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

**注意事項**：
- モノレポではファイルアクセスが多くなる（1000+ファイル）
- 初回起動が遅い（20-30秒）
- 再利用可能なパッケージとして配布する場合に適切

#### nix shell（高速起動が必要な場合）
頻繁に実行される開発ツールやスクリプトに最適。

```bash
#!/usr/bin/env bash
# run-with-shell.sh
exec nix shell \
  nixpkgs#package1 \
  nixpkgs#package2 \
  --command ./actual-script "$@"
```

**利点**：
- 起動速度が3倍高速（0.1秒 vs 0.3秒）
- ファイルアクセスが最小限（50ファイル vs 1000+ファイル）
- CI/CD環境での初回実行が20倍高速

**使用すべきケース**：
- 開発中に頻繁に実行されるツール
- CI/CDパイプラインでの実行
- モノレポ内でのローカルツール

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
- `nix run .` - デフォルトアプリケーション実行（利用可能なアプリ一覧を動的に表示）
- `nix run .#test` - テスト実行（単体・統合・E2E統合実行）
- `nix run .#readme` - README.mdを表示
- `nix develop` - 開発シェル

#### テスト実行の最適化
開発中の頻繁なテスト実行では`nix shell`を使用可能：
```bash
# 開発中の高速テスト実行
alias test-fast="nix shell . -c pytest"

# 正式なテスト実行（CI/CD同等）
nix run .#test
```

**使い分けの指針**：
- **開発中**: `nix shell`で高速実行（ストアコピーを回避）
- **最終確認/CI**: `nix run`で完全性確認（パッケージング検証を含む）

### エラーハンドリング規約
- 存在しないアプリケーション指定時：エラーメッセージとともに利用可能なアプリ一覧を表示
- デフォルトアプリにオプション引数指定時：エラーメッセージとともに利用可能なアプリ一覧を表示

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
- ❌ devShellとpackagesで同じツールリストを重複定義
- ❌ パッケージなしでdevShellのみ提供

## ベストプラクティス

- ✅ nix shell shebangでスクリプト単位の環境定義
- ✅ Flake評価を最小限に抑える
- ✅ 使用箇所に最も近いところで環境を定義
- ✅ 開発中はnix shell、公開時はnix run
- ✅ `writeScriptBin`でシンプルに
- ✅ スタンドアロンスクリプトで相対インポート回避
- ✅ 通常はソースディレクトリでテスト実行（特殊な場合のみ一時ディレクトリ）
- ✅ 明確なエラーメッセージ
- ✅ 言語環境は親flakeから継承
- ✅ バージョン管理は親flakeで一元化
- ✅ パッケージ定義を中心に、devShellは参照で構築
- ✅ ツールの定義は一箇所（packages）に集約

## デフォルトアプリの動的一覧表示

BuildTime評価を使用して、利用可能なアプリを動的に表示：

```nix
apps = rec {
  default = {
    type = "app";
    program = let
      # ビルド時に利用可能なアプリ名を取得
      appNames = builtins.attrNames (removeAttrs self.apps.${system} ["default"]);
      helpText = ''
        プロジェクト: <プロジェクト名>
        
        利用可能なコマンド:
        ${builtins.concatStringsSep "\n" (map (name: "  nix run .#${name}") appNames)}
      '';
    in "${pkgs.writeShellScript "show-help" ''
      cat << 'EOF'
      ${helpText}
      EOF
    ''}";
  };
  
  test = { ... };
  readme = {
    type = "app";
    program = "${pkgs.writeShellScript "show-readme" ''
      cat ${./README.md}
    ''}";
  };
};
```

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