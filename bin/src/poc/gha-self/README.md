# GitHub Actions Self-Hosted Runner POC

## 責務
1. GitHub Actions self-hosted runnerをnixpkgsで環境整備
2. cronジョブのテストのみ実施

## 目的
nixpkgsのgithub-runnerパッケージを使用してGitHub Actions self-hosted runnerの環境を構築し、5分ごとに実行されるcronジョブテストワークフローの動作確認を行う。

## 使用方法

### 1. 環境セットアップ
```bash
# 開発環境に入る
nix develop
```

### 2. Runnerの登録
```bash
# GitHubリポジトリから登録トークンを取得後、実行
./setup.sh YOUR_REGISTRATION_TOKEN
```

### 3. Cronジョブテスト
`.github/workflows/cron-test.yml`が5分ごとに自動実行される

## 前提条件
- GitHub repository settingsから生成した登録トークン
- Docker（nixpkgsから提供）

## ファイル構成
```
gha-self/
├── flake.nix                    # nixpkgs環境定義
├── README.md                    # 責務と使用方法
├── setup.sh                     # runner登録スクリプト
└── .github/
    └── workflows/
        └── cron-test.yml       # 5分ごとのテストジョブ
```

## アーキテクチャ上の位置づけ
- モノレポの一部として動作
- リポジトリルートの`.github/workflows/`からのみ実行される
- 各サブディレクトリの`.github/workflows/`は無視される（GitHub仕様）

## Self-hosted Runner戦略
### 各flake専用runner
- 各flakeごとに独立したrunner環境を構築
- ラベル規約: `self-hosted,nix,flake-{FLAKE_NAME}`
- 作業ディレクトリ: `_work_{FLAKE_NAME}`

### Runner登録方法
1. gh CLIを使用したトークン取得
2. github-runnerパッケージでの登録

## Workflow設定パターン
### パス制限による実行制御
- pathsフィルタでディレクトリごとの実行を制御

### 作業ディレクトリの指定
- defaults.run.working-directoryで実行場所を指定

### Runnerラベルによる実行環境選択
- runs-onでflake専用runnerを選択

## 制約事項
- GitHub Actionsのworkflowはリポジトリルートのみ有効
- 各ディレクトリごとのworkflow定義は不可
- Self-hosted runnerの登録にはリポジトリのadmin権限が必要

## 依存関係に関する注記
- flake間の依存解決はこのPOCのスコープ外
- 依存関係管理は別途architecture層で設計予定