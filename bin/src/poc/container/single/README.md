# Single Flake Multi-Container Builder

## 概要

単一のNix flakeから複数タイプのDockerコンテナをビルドするシステムです。
外部flakeへの依存なしに、異なるランタイム環境（Node.js、Python、Go）を持つコンテナを生成できます。

## 機能

- **単一flake管理**: 全てのコンテナ定義を一つのflake.nixで管理
- **複数コンテナタイプ**: Base、Node.js、Python、Goの4種類のコンテナをサポート
- **共通ビルド関数**: `buildContainer`関数による重複排除
- **インタラクティブ選択**: flake-selectorによるコンテナ選択UI
- **Podman対応**: rootless実行可能なコンテナイメージ生成

## アーキテクチャ

```
flake.nix
├── 内部アプリケーション定義
│   ├── nodejsApp - Node.jsランタイムアプリ
│   ├── pythonApp - Pythonランタイムアプリ
│   ├── goApp     - Goランタイムアプリ
│   └── baseApp   - 基本ツールのみ
│
├── buildContainer関数 - 共通ビルドロジック
│
└── packages出力
    ├── container-base
    ├── container-nodejs
    ├── container-python
    └── container-go
```

## 使用方法

### 開発環境に入る
```bash
nix develop
```

### コンテナのビルド
```bash
# 特定のコンテナをビルド
nix build .#container-nodejs
nix build .#container-python
nix build .#container-go
nix build .#container-base

# インタラクティブに選択
nix run .#flake-selector
```

### Podmanでの実行
```bash
# イメージをロード
gunzip -c $(nix build .#container-nodejs --print-out-paths) | podman load

# コンテナを実行
podman run --rm localhost/nodejs-container:latest
```

### テストの実行
```bash
nix develop --command bats test_container.bats
```

## テスト項目

全23項目のテストにより以下を検証:
- flake構造の正当性
- 各コンテナのビルド成功
- Podmanでのイメージロードと実行
- ランタイムの動作確認
- メタデータの正確性

## 設計原則

### 採用した原則
- **KISS**: 単一flakeでシンプルに管理
- **DRY**: buildContainer関数で重複排除  
- **YAGNI**: 必要な機能のみ実装（外部flake統合は未実装）

### 今後の拡張性
将来的に外部flakeとの統合が必要になった場合、現在の構造を基盤として拡張可能です。

## ディレクトリ構成

```
single/
├── flake.nix              # メイン定義ファイル
├── flake.lock             # 依存関係のロック
├── test_container.bats    # テストスイート
└── README.md              # このファイル
```

## 注意事項

- sample-flakesディレクトリへの参照は削除済み（実際には使用されていなかった）
- 全てのアプリケーション定義はflake.nix内で完結
- テストにはPodmanが必要（Dockerより権限問題が少ない）