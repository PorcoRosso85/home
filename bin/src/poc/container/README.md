# Nix Container POC

Nixを使用したコンテナ化とオーケストレーションの実証実験

## 目的

1. Nixでコンテナイメージをビルドできることを実証（Dockerfile不要）
2. Nixでコンテナオーケストレーションが可能なことを実証（YAML不要）
3. 宣言的な設定でインフラを管理できることを実証

## Nixの特徴

### Dockerfileなしでコンテナ作成
- **dockerTools.buildImage**: 純粋なNix表現でコンテナイメージを定義
- 再現可能なビルド
- レイヤー最適化
- 依存関係の自動解決

### YAMLなしでオーケストレーション
- **arion**: Nix表現でdocker-compose相当の機能
- **nixos-container**: systemd-nspawnベースの軽量コンテナ
- 型安全な設定
- Nixの評価システムによる設定検証

## ディレクトリ構造

```
container/
├── README.md
├── single/           # 単一コンテナのPOC
│   ├── flake.nix
│   └── test_container_single.sh
└── orchestra/        # オーケストレーションのPOC
    ├── flake.nix
    └── test_container_orchestra.sh
```

## 仕様

### Single Container
- Nixでコンテナイメージをビルド
- 基本的なWebアプリケーションを実行
- curlやjqなどの必要なツールを含む
- エントリーポイントの設定

### Orchestra
- 複数のコンテナを定義（Web、API、DB）
- docker-compose.ymlの生成
- サービス間の通信設定
- ボリューム・ネットワークの設定
- ヘルスチェックの実装

## テスト手順

```bash
# containerディレクトリから実行（重要！）
cd /home/nixos/bin/src/poc/container

# 開発シェルに入る
nix develop

# 開発シェル内でテスト実行
test-all          # すべてのテストを実行
test-single       # 単一コンテナテストのみ
test-orchestra    # オーケストレーションテストのみ

# またはワンライナーで実行
nix develop --command test-all

# 直接batsを使用する場合
cd single && bats test_container.bats
cd orchestra && bats test_orchestra.bats
```

## TDDアプローチ

1. Red: テストを先に書く（完了）
2. Green: 最小限の実装でテストを通す
3. Refactor: コードを改善する