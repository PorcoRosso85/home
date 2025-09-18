# Sliplane Deployment with Nix

## 概要
Sliplaneは月額固定料金で無制限のコンテナをホスティングできるPaaSサービス。
本プロジェクトはflake.nixの設定をDockerfile経由でSliplaneにデプロイする方法を提供。

## Sliplaneの特徴
- **料金体系**: サーバー単位の固定料金（€9/月〜）
- **ビルド機能**: GitHubリポジトリ + Dockerfileから自動ビルド
- **対応レジストリ**: Docker Hub, GitHub Container Registry (GHCR)
- **無料試用**: 48時間のDemoサーバー

## 制約事項
- **Dockerfile必須**: GitHubからのビルドにはDockerfileが必要
- **flake.nix非対応**: Nix flakeの直接ビルドは不可
- **GCR非対応**: Google Container Registryは未対応

## デプロイ方法

### 方法1: Dockerfile内でNixビルド
```dockerfile
FROM nixos/nix:latest AS builder
COPY flake.nix flake.lock ./
RUN nix build .#dockerImage
```

### 方法2: 事前ビルド + レジストリ経由
```bash
# ローカルでビルド
nix build .#dockerImage
docker load < result

# GHCRにプッシュ
docker tag app:latest ghcr.io/username/app:latest
docker push ghcr.io/username/app:latest

# Sliplaneでレジストリソースとしてデプロイ
```

### 方法3: GitHub Actions統合
```yaml
- name: Build with Nix
  run: nix build .#dockerImage
- name: Push to GHCR
  run: |
    docker load < result
    docker push ghcr.io/${{ github.repository }}:latest
```

## プロジェクト責務
1. flake.nix設定をDockerfileへ完全再現
2. Nix環境のコンテナ化ベストプラクティス提供
3. Sliplane向け最適化設定の管理

## クイックスタート

### 1. Sliplaneアカウント作成
```bash
# https://sliplane.io でGitHubアカウントでサインアップ
# 48時間無料のDemoサーバーが自動作成される
```

### 2. リポジトリ準備
```bash
# Dockerfile.nix-exampleを参考にDockerfile作成
cp Dockerfile.nix-example Dockerfile
# 必要に応じて編集
```

### 3. デプロイ
1. Sliplaneダッシュボードで "Deploy Service" をクリック
2. GitHubリポジトリを選択
3. Dockerfileパスを指定（デフォルト: /Dockerfile）
   - 特定ディレクトリの場合: `/services/api/Dockerfile`
4. Docker Contextを設定（必要に応じて）
   - Dockerfileの親ディレクトリを指定: `/services/api`
5. 環境変数等を設定してデプロイ

## モノレポでの設定例

### ディレクトリ構成
```
repo/
├── services/
│   ├── web/
│   │   ├── Dockerfile
│   │   └── flake.nix
│   └── api/
│       ├── Dockerfile
│       └── flake.nix
└── shared/
```

### Sliplane設定
| サービス | Dockerfile Path | Docker Context | 説明 |
|---------|----------------|----------------|------|
| Web | `/services/web/Dockerfile` | `/services/web` | webディレクトリのみビルド |
| API | `/services/api/Dockerfile` | `/services/api` | apiディレクトリのみビルド |
| Root | `/Dockerfile` | `/` | リポジトリ全体をビルド |

## ファイル構成
```
.
├── README.md                 # このファイル
├── Dockerfile.nix-example    # Nix + Dockerfileのサンプル
├── flake.nix                # Nixパッケージ定義
├── flake.lock              # 依存関係ロック
└── docs/                   # Sliplane公式ドキュメント
```

## 参考リンク
- [Sliplane公式](https://sliplane.io)
- [Sliplaneドキュメント](https://docs.sliplane.io)
- [料金プラン](https://sliplane.io/#pricing)