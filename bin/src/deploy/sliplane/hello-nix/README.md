# NixOS Minimal Hello Container

**責務**: Sliplane向けの最小構成NixOS HTTPサーバーコンテナのテンプレート

## 概要
NixOSベースでnixpkgs#helloを実行するDockerコンテナ。ポート8080でHTTPサーバーとして動作し、Sliplaneでのデプロイに最適化されています。

## 基本的な使い方

### ローカル実行
```bash
# HTTPサーバーを直接実行
nix run .#server

# 確認
curl http://localhost:8080
```

### Docker権限設定（初回のみ）
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### テスト実行
```bash
# 包括的なテストを実行（詳細コマンドはtest.sh参照）
./test.sh
```

## Sliplaneデプロイ設定
1. GitHubリポジトリにプッシュ
2. Sliplaneで新規サービス作成
3. 設定値：
   - **Deploy Source**: GitHub
   - **Dockerfile Path**: `/hello-nix/Dockerfile`
   - **Docker Context**: `/hello-nix`
   - **Expose Service**: ON
   - **Port**: 8080
   - **Protocol**: HTTP

## 詳細情報
- **テストコマンド**: `test.sh`を参照
- **flake.nix構成**: `default`, `server`, `dockerImage`アプリを定義
- **特徴**: Nixによる完全な依存管理と再現性保証