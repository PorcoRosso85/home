# Nix Container Capabilities

## はい、本当です！

NixはDockerfileやdocker-compose.ymlなしでコンテナ化・オーケストレーションが可能です。

### 1. dockerTools.buildImage（Dockerfile不要）

```nix
dockerTools.buildImage {
  name = "my-app";
  tag = "latest";
  
  # コンテナの内容を定義
  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [ pkgs.curl pkgs.jq myApp ];
  };
  
  # エントリーポイント設定
  config = {
    Entrypoint = [ "${myApp}/bin/app" ];
    Env = [ "PORT=8080" ];
    ExposedPorts = { "8080/tcp" = {}; };
  };
}
```

**利点:**
- 純粋関数的なイメージ定義
- 自動的なレイヤー最適化
- 依存関係の完全な追跡
- ビルドの再現性保証

### 2. arion（docker-compose.yml不要）

```nix
# arion-compose.nix
{
  services.web = {
    image = import ./web-image.nix;
    ports = [ "8080:8080" ];
    environment.DATABASE_URL = "postgres://db:5432/myapp";
    depends_on = [ "db" ];
  };
  
  services.db = {
    image = "postgres:14";
    volumes = [ "db-data:/var/lib/postgresql/data" ];
    environment.POSTGRES_PASSWORD = "secret";
  };
  
  networks.default = {};
  volumes.db-data = {};
}
```

**実行:**
```bash
arion up  # docker-compose upと同等
```

### 3. nixos-container（Dockerなしで軽量コンテナ）

```nix
containers.web = {
  autoStart = true;
  privateNetwork = true;
  hostAddress = "192.168.100.10";
  localAddress = "192.168.100.11";
  
  config = { config, pkgs, ... }: {
    services.nginx = {
      enable = true;
      virtualHosts.default = {
        locations."/" = {
          proxyPass = "http://localhost:3000";
        };
      };
    };
    
    systemd.services.my-app = {
      wantedBy = [ "multi-user.target" ];
      script = "${myApp}/bin/app";
    };
  };
};
```

### 4. microvm.nix（超軽量VM）

より高度な分離が必要な場合：

```nix
microvm.vms.app = {
  config = {
    microvm.vcpu = 2;
    microvm.mem = 512;
    microvm.shares = [{
      source = "/nix/store";
      mountPoint = "/nix/store";
    }];
    
    # NixOSモジュールで設定
    services.myapp.enable = true;
  };
};
```

## 比較表

| 機能 | Docker方式 | Nix方式 | 利点 |
|------|------------|---------|------|
| イメージ定義 | Dockerfile | dockerTools.buildImage | 型安全、再現可能 |
| オーケストレーション | docker-compose.yml | arion | Nix評価、型チェック |
| 軽量コンテナ | Docker | nixos-container | systemd統合 |
| VM | docker-machine | microvm.nix | 宣言的VM管理 |

## なぜNixなのか？

1. **再現性**: 同じ入力から必ず同じ出力
2. **宣言的**: 状態ではなく望む結果を記述
3. **型安全**: 設定ミスをビルド時に検出
4. **統合性**: OS、パッケージ、コンテナを同じ言語で管理

## 実証されたユースケース

- **Determinate Systems**: Nix Enterprise向けソリューション
- **Flox**: Nix開発環境プラットフォーム
- **Cachix**: Nixビルドキャッシュサービス

これらの企業はプロダクションでNixコンテナを活用しています。