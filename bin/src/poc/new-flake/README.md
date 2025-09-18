# new-flake

## 概要
組織標準のNixフレークテンプレート。新規プロジェクト作成時に必要な標準構造と検証機能を提供。

## 目的
- 標準化されたflake.nix構造の提供
- flake-readme依存関係の必須統合の強制
- 全プロジェクトでのreadme.nixドキュメントの要求
- `nix flake init`によるテンプレート配布の有効化
- 開発者への明確な検証ワークフローの提示

## 非目的
- ドメイン固有機能の提供
- アプリケーションビジネスロジックの包含
- 既存プロジェクトアーキテクチャの置換

## 使用方法

### テンプレートからの新規プロジェクト作成
```bash
# テンプレートから初期化
nix flake init -t path:/home/nixos/bin/src/poc/new-flake

# readme.nixを編集して、プロジェクトの説明と目標を更新
$EDITOR readme.nix

# ドキュメンテーションを検証
nix run .#readme-check

# 完全な検証を実行
nix flake check
```

### 必須ファイル
- `readme.nix`: プロジェクトドキュメントと目標
- `flake.nix`: 必須inputsを含む標準構造

### 検証コマンド
- `nix run .#readme-check`: ドキュメンテーション検証
- `nix flake check`: readme.nixを含む包括的検証

## CI/CD統合
推奨される検証ステップ:
- GitHub Actions: CIパイプラインで`nix flake check`を実行
- GitLab CI: nixベースの検証ステージを追加
- Pre-commit: gitフックとしてreadme-checkを設定

## 言語固有スタック
言語固有のスタックについては、`bin/src/flakes/<lang>/flake.nix`（例：rust、python）を参照し、必要に応じて関連するinputs/modulesを含める。