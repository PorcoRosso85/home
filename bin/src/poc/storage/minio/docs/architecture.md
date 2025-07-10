# MinIO Nix Flake アーキテクチャ

## アーキテクチャ図

```
┌─────────────────────┐
│    Nix flake        │
│  (宣言的な定義)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Docker/Podman      │
│  コンテナランタイム   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     MinIO           │
│  - Port 9000 (API)  │
│  - Port 9001 (Web)  │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│   S3互換クライアント  │
│  (mc, AWS SDK等)    │
└─────────────────────┘
```

## 概説

### 1. Nix Flake層
- **役割**: MinIOの実行環境を宣言的に定義
- **機能**: 
  - 依存関係の管理
  - 再現可能な環境の提供
  - 開発ツールの統合

### 2. コンテナランタイム層
- **役割**: MinIOコンテナの実行基盤
- **選択肢**:
  - Docker (一般的)
  - Podman (rootless対応)
- **管理方法**:
  - systemdサービス
  - process-compose
  - docker-compose互換

### 3. MinIO層
- **役割**: S3互換オブジェクトストレージ
- **ポート構成**:
  - 9000: S3 API エンドポイント
  - 9001: Web管理コンソール
- **データ永続化**: ホストボリュームマウント

### 4. クライアント層
- **役割**: MinIOへのアクセス
- **ツール**:
  - MinIO Client (mc)
  - AWS SDK
  - S3互換ツール

## 実装方針

### Option A: NixOSモジュール方式
```nix
virtualisation.oci-containers.containers.minio = {
  image = "quay.io/minio/minio:latest";
  ports = ["9000:9000" "9001:9001"];
  volumes = ["/data/minio:/data"];
  cmd = ["server", "/data", "--console-address", ":9001"];
};
```

### Option B: devShell方式
```nix
devShells.default = pkgs.mkShell {
  packages = with pkgs; [
    docker
    minio-client
  ];
  shellHook = ''
    docker run -d \
      -p 9000:9000 -p 9001:9001 \
      --name minio \
      quay.io/minio/minio server /data --console-address ":9001"
  '';
};
```

### Option C: process-compose方式（推奨）
```nix
devShells.default = pkgs.mkShell {
  packages = with pkgs; [
    process-compose
    minio-client
  ];
  shellHook = ''
    process-compose up
  '';
};
```

## TODO

1. [ ] flake.nixファイルの作成
2. [ ] process-compose.yamlの定義
3. [ ] 環境変数の設定（認証情報等）
4. [ ] データ永続化ディレクトリの設定
5. [ ] S3互換APIのテストスクリプト作成
6. [ ] クライアント設定の自動化