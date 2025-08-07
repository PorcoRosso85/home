# Bash Development Environment

Bash開発環境のNix Flakeです。シェルスクリプト開発に必要なツールセットを提供します。

## 含まれるツール

- **bash**: Bashシェル本体
- **bash-language-server**: Bash用LSP（Language Server Protocol）サーバー
- **shellcheck**: Bashスクリプトの静的解析ツール
- **bats**: Bash Automated Testing System（テストフレームワーク）
- **shfmt**: Bashスクリプトのフォーマッター

## 使い方

### 開発環境に入る
```bash
nix develop
```

### 利用可能なコマンドを確認
```bash
nix run .
```

### READMEを表示
```bash
nix run .#readme
```

### 直接実行（例）
```bash
# ShellCheckによる静的解析
nix shell . -c shellcheck script.sh

# フォーマッターでコード整形
nix shell . -c shfmt -w script.sh

# テスト実行（BATSテストファイルがある場合）
nix shell . -c bats test/
```

## 特徴

- **パッケージ中心設計**: `packages.default`にツールセットを集約
- **DRY原則**: `devShells.default`は`packages.default`を参照
- **即座に利用可能**: 環境構築不要でBash開発ツールを利用
- **LSP対応**: エディタでの補完・診断機能をサポート