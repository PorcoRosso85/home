# Claude UI Flake Usage Guide

## ✨ Features

- **パス独立**: Flake依存により、どこからでも利用可能
- **システム独立**: すべての依存をNixが管理
- **再利用可能**: 他のFlakeプロジェクトから簡単に統合

## 🚀 スタンドアロン使用

### 1. 直接実行

```bash
# 現在のディレクトリでClaude Codeを起動
nix run github:user/claude-ui

# 特定のディレクトリで起動
nix run github:user/claude-ui -- ~/projects/myapp

# fzfでプロジェクト選択
nix run github:user/claude-ui -- --flake
```

### 2. プロファイルへのインストール

```bash
# ユーザー環境にインストール
nix profile install github:user/claude-ui

# その後は通常のコマンドとして使用
claude
claude --flake
claude ~/projects/myapp
```

## 🔗 他のFlakeプロジェクトからの使用

### 1. 開発環境への統合

```nix
# your-project/flake.nix
{
  description = "Your project with Claude UI integration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    claude-ui.url = "path:/home/nixos/bin/src/develop/claude/ui";
    # または GitHub から:
    # claude-ui.url = "github:user/claude-ui";
  };

  outputs = { self, nixpkgs, claude-ui, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          # Claude CLIを開発環境に含める
          claude-ui.packages.${system}.claude-cli
        ];
        
        shellHook = ''
          echo "Claude UI is available!"
          echo "Run 'claude' to launch Claude Code"
        '';
      };
    };
}
```

### 2. カスタムラッパーの作成

```nix
# custom-launcher/flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    claude-ui.url = "path:/home/nixos/bin/src/develop/claude/ui";
  };

  outputs = { self, nixpkgs, claude-ui, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system}.my-claude = pkgs.writeShellApplication {
        name = "my-claude";
        runtimeInputs = [
          claude-ui.packages.${system}.claude-cli
        ];
        text = ''
          # カスタムロジックを追加
          echo "🚀 Starting custom Claude launcher..."
          
          # プロジェクト固有の設定
          export MY_PROJECT_CONFIG="custom-value"
          
          # Claude UIを呼び出し
          claude "$@"
        '';
      };
    };
}
```

### 3. 個別コンポーネントの利用

```nix
{
  inputs.claude-ui.url = "path:/home/nixos/bin/src/develop/claude/ui";
  
  outputs = { self, claude-ui, ... }:
    let
      system = "x86_64-linux";
    in
    {
      # 個別のツールを選択的に使用
      packages.${system} = {
        # プロジェクト選択ツールのみ
        project-selector = claude-ui.packages.${system}.select-project;
        
        # MCP設定ツールのみ
        mcp-setup = claude-ui.packages.${system}.setup-mcp;
        
        # Claude起動ツールのみ
        launcher = claude-ui.packages.${system}.launch-claude;
      };
    };
}
```

## 📦 提供されるパッケージ

| パッケージ名 | コマンド | 説明 |
|------------|---------|------|
| `claude-cli` | `claude` | メインCLI（すべての機能を統合） |
| `select-project` | `claude-select-project` | fzfプロジェクト選択 |
| `launch-claude` | `claude-launch` | Claude Code起動 |
| `setup-mcp` | `claude-setup-mcp` | MCPサーバー設定 |

## 🎯 使用例

### プロジェクトテンプレートでの利用

```nix
# project-template/flake.nix
{
  inputs = {
    claude-ui.url = "github:user/claude-ui";
    # ... other inputs
  };

  outputs = { self, claude-ui, ... }: {
    # テンプレートに含める
    templates.default = {
      path = ./template;
      description = "Project template with Claude UI";
      welcomeText = ''
        Project created!
        
        This template includes Claude UI integration.
        Run 'nix develop' then 'claude' to start coding with AI assistance.
      '';
    };
  };
}
```

### CI/CDパイプラインでの利用

```yaml
# .github/workflows/develop.yml
name: Development Environment
on: [push]

jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: cachix/install-nix-action@v22
      
      - name: Setup Claude UI
        run: |
          nix run .#claude-setup-mcp
          
      - name: Launch development
        run: |
          nix run .#claude -- .
```

## 🔄 移行ガイド

### 従来のshスクリプトから

```bash
# Before (パス依存)
./claude-shell.sh
/home/nixos/bin/src/develop/claude/ui/claude-shell.sh

# After (Flake依存)
nix run github:user/claude-ui
claude  # (after nix profile install)
```

### 既存プロジェクトへの追加

1. `flake.nix`にinputを追加
2. `devShell`のpackagesに含める
3. `nix develop`で利用可能に

## 📝 注意事項

- 初回実行時はNixがパッケージをビルド/ダウンロードするため時間がかかります
- `flake.lock`ファイルで依存バージョンが固定されます
- `nix flake update`で最新版に更新できます

## 🛠️ トラブルシューティング

### "Git tree is dirty"警告

```bash
# 解決方法1: 変更をコミット
git add . && git commit -m "wip"

# 解決方法2: --impureフラグを使用
nix run --impure github:user/claude-ui
```

### パッケージが見つからない

```bash
# flake.lockを更新
nix flake update claude-ui

# キャッシュをクリア
nix-collect-garbage -d
```