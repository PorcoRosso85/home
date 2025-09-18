# sops-flake Systemd Template

## 概要
このテンプレートは、NixOSシステムサービス向けのsops-nix統合を提供します。
機密情報を安全に管理し、Gitにコミット可能な形式で暗号化します。

## クイックスタート

```bash
# 1. テンプレートのクローン
cp -r /path/to/templates/systemd my-service
cd my-service

# 2. 初期化（ワンステップ）
./scripts/init-template.sh

# 3. 開発環境起動
nix develop

# 4. シークレット編集
sops edit secrets/app.yaml
```

## 機能

- ✅ age/SSH両暗号化方式サポート
- ✅ Git pre-commitフックで平文漏洩防止
- ✅ 環境別設定（development/staging/production）
- ✅ 自動暗号化検証
- ✅ NixOS/Home Manager統合対応

## ディレクトリ構造

```
.
├── flake.nix              # Nix flake定義
├── flake.lock             # 依存関係ロック
├── configuration.nix      # システム設定（systemdのみ）
├── module.nix             # sops-appモジュール
├── .sops.yaml             # SOPS設定
├── secrets/               # 暗号化されたシークレット
│   └── app.yaml          # アプリケーションシークレット
├── scripts/               # ヘルパースクリプト
│   ├── init-template.sh  # 初期化スクリプト
│   ├── setup-age-key.sh  # Age鍵設定
│   ├── setup-ssh-recipient.sh  # SSH鍵設定
│   ├── verify-encryption.sh  # 暗号化検証
│   └── check-no-plaintext-secrets.sh  # 平文チェック
└── README.md              # このファイル
```

## セットアップ詳細

### 1. Age鍵の準備

```bash
# 新規作成
./scripts/setup-age-key.sh

# または既存鍵を使用
export SOPS_AGE_KEY_FILE=/path/to/your/keys.txt
```

### 2. .sops.yaml設定

公開鍵を.sops.yamlのREPLACE_MEと置換:

```bash
# 公開鍵取得
age-keygen -y ~/.config/sops/age/keys.txt

# .sops.yaml編集
vim .sops.yaml  # REPLACE_MEを公開鍵に置換
```

### 3. 暗号化方式の選択

#### Age鍵（推奨：新規プロジェクト）
```bash
# Age鍵生成
./scripts/setup-age-key.sh
# .sops.yamlのREPLACE_ME_AGEを公開鍵に置換
```

#### SSH鍵（既存インフラ活用）
```bash
# SSH鍵をage形式に変換
./scripts/setup-ssh-recipient.sh ~/.ssh/id_ed25519.pub
# .sops.yamlのREPLACE_ME_SSHを変換後の鍵に置換

# 復号化時は変換されたage鍵を使用
nix develop  # ssh-to-age含む
```

#### 混在環境（チーム開発）
両方式の受信者を.sops.yamlに追加可能:
```yaml
- age:
    - age1xxx...  # Age鍵ユーザー
    - age1yyy...  # SSH鍵から変換
```

### 4. シークレット管理

```bash
# 暗号化して編集
sops edit secrets/app.yaml

# 暗号化状態確認
./scripts/verify-encryption.sh

# 復号化（一時的）
sops decrypt secrets/app.yaml
```

## Systemd Template固有セクション

### 特徴
- **NixOSシステムサービス向け**: systemdユニットとして統合
- **ルート権限**: システムレベルでのシークレット管理
- **自動起動**: ブート時に自動開始
- **systemctl管理**: 標準的なサービス制御

### 使用ケース
- 🗄️ データベースサーバー（PostgreSQL, MySQL）
- 🔄 バックグラウンドワーカー
- 📡 インフラストラクチャサービス（Redis, RabbitMQ）
- 🔒 システム権限が必要なサービス

### NixOS統合手順

#### 1. システム flake.nix への追加
```nix
# /etc/nixos/flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    sops-nix.url = "github:Mic92/sops-nix";
    my-service.url = "path:/path/to/my-service";
  };
  
  outputs = { self, nixpkgs, sops-nix, my-service, ... }: {
    nixosConfigurations.hostname = nixpkgs.lib.nixosSystem {
      modules = [
        ./configuration.nix
        sops-nix.nixosModules.sops
        my-service.nixosModules.default
      ];
    };
  };
}
```

#### 2. configuration.nix での有効化
```nix
# /etc/nixos/configuration.nix
{
  services.my-service = {
    enable = true;
    port = 8080;
    # その他のサービス設定
  };
  
  # sops-nix設定
  sops.age.keyFile = "/var/lib/sops-nix/key.txt";
}
```

#### 3. デプロイ
```bash
sudo nixos-rebuild switch
```

#### 4. サービス管理
```bash
# ステータス確認
systemctl status my-service

# ログ確認
journalctl -u my-service -f

# 再起動
systemctl restart my-service
```

## トラブルシューティング

### よくある問題

**Q: sops editで「no data key found」エラー**
A: .sops.yamlの公開鍵が正しいか確認し、対応する秘密鍵がSOPS_AGE_KEY_FILEにあることを確認

**Q: Git commitが「plaintext secrets detected」で失敗**
A: secrets/内のファイルを暗号化: `sops -e -i secrets/app.yaml`

**Q: nix developが起動しない**
A: `nix flake update`で依存関係を更新

**Q: systemd serviceが起動しない**
A: `sudo systemctl status my-service`でエラー確認、sops鍵が正しく配置されているかチェック

**Q: nixos-rebuildが失敗する**
A: flake.nixの構文確認、モジュール参照パスが正しいかチェック

## セキュリティベストプラクティス

1. **秘密鍵の保護**: Age秘密鍵は絶対にGitにコミットしない
2. **公開鍵の共有**: チームメンバーの公開鍵を.sops.yamlに追加
3. **定期的な鍵更新**: 定期的に暗号化鍵をローテーション
4. **最小権限原則**: 必要なユーザー/サービスのみにアクセス許可
5. **システム鍵管理**: 本番環境では専用のシステム鍵を使用

## 関連リンク

- [sops-nix Documentation](https://github.com/Mic92/sops-nix)
- [age Encryption](https://github.com/FiloSottile/age)
- [SOPS](https://github.com/mozilla/sops)
- [NixOS Manual - systemd Services](https://nixos.org/manual/nixos/stable/index.html#sec-systemd)

## ライセンス

MIT License