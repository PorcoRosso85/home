# sops-flake User Template

## 概要
このテンプレートは、Home Manager/ユーザーレベルサービス向けのsops-nix統合を提供します。
機密情報を安全に管理し、Gitにコミット可能な形式で暗号化します。

## クイックスタート

```bash
# 1. テンプレートのクローン
cp -r /path/to/templates/user my-tool
cd my-tool

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
├── configuration.nix      # システム設定（userのみ）
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

## User Template固有セクション

### 特徴
- **Home Manager向け**: ユーザーレベルサービス
- **ユーザー権限**: ユーザー権限でのシークレット管理  
- **柔軟な実行**: 手動実行または自動実行対応
- **Timer統合**: systemdタイマーでの定期実行サポート

### 使用ケース
- 🔄 バックアップスクリプト
- 📊 モニタリングツール
- 🔧 システムメンテナンスユーティリティ
- 📁 データ同期ツール
- 🤖 自動化スクリプト

### Home Manager統合手順

#### 1. Home Manager flake.nix への追加
```nix
# ~/.config/home-manager/flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    home-manager.url = "github:nix-community/home-manager";
    sops-nix.url = "github:Mic92/sops-nix";
    my-tool.url = "path:/path/to/my-tool";
  };
  
  outputs = { self, nixpkgs, home-manager, sops-nix, my-tool, ... }: {
    homeConfigurations.username = home-manager.lib.homeManagerConfiguration {
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
      modules = [
        ./home.nix
        sops-nix.homeManagerModules.sops
        my-tool.homeManagerModules.default
      ];
    };
  };
}
```

#### 2. home.nix での有効化
```nix
# ~/.config/home-manager/home.nix
{
  programs.my-tool = {
    enable = true;
    backupPath = "/home/user/backup";
    syncInterval = 60;
    
    # オプション: 自動実行の有効化
    timer = {
      enable = true;
      onCalendar = "daily";  # または "hourly", "*-*-* 02:00:00" など
    };
  };
  
  # sops-nix設定
  sops.age.keyFile = "${config.home.homeDirectory}/.config/sops/age/keys.txt";
}
```

#### 3. デプロイ
```bash
home-manager switch
```

#### 4. ツール使用
```bash
# 手動実行
my-tool backup
my-tool sync
my-tool status

# タイマー確認（有効な場合）
systemctl --user status my-tool.timer
systemctl --user list-timers | grep my-tool

# ログ確認
journalctl --user -u my-tool
```

### NixOS統合（ユーザーサービスとして）

#### システムワイドでのユーザーサービス有効化
```nix
# /etc/nixos/configuration.nix
{
  imports = [
    my-tool.nixosModules.default
  ];
  
  programs.my-tool = {
    enable = true;
    users = [ "alice" "bob" ];  # 利用可能ユーザー
  };
  
  sops.age.keyFile = "/var/lib/sops-nix/key.txt";
}
```

## 実行モード

### 手動実行モード（デフォルト）
- スクリプトがPATHで利用可能
- ユーザーが必要に応じて実行
- 実行制御が完全にユーザー側

### タイマー実行モード（オプション）
- 自動的な定期実行
- systemdタイマー管理
- 再起動後も持続

## トラブルシューティング

### よくある問題

**Q: sops editで「no data key found」エラー**
A: .sops.yamlの公開鍵が正しいか確認し、対応する秘密鍵がSOPS_AGE_KEY_FILEにあることを確認

**Q: Git commitが「plaintext secrets detected」で失敗**
A: secrets/内のファイルを暗号化: `sops -e -i secrets/app.yaml`

**Q: nix developが起動しない**
A: `nix flake update`で依存関係を更新

**Q: Home Managerでサービスが認識されない**
A: `home-manager switch`を実行、モジュール参照パスが正しいかチェック

**Q: ユーザーサービスが起動しない**
A: `systemctl --user status my-tool`でエラー確認、ユーザー権限でsops鍵にアクセス可能かチェック

## セキュリティベストプラクティス

1. **秘密鍵の保護**: Age秘密鍵は絶対にGitにコミットしない
2. **公開鍵の共有**: チームメンバーの公開鍵を.sops.yamlに追加
3. **定期的な鍵更新**: 定期的に暗号化鍵をローテーション
4. **最小権限原則**: 必要なユーザー/サービスのみにアクセス許可
5. **ユーザー鍵管理**: ユーザーディレクトリ内での適切な鍵管理

## 関連リンク

- [sops-nix Documentation](https://github.com/Mic92/sops-nix)
- [age Encryption](https://github.com/FiloSottile/age)
- [SOPS](https://github.com/mozilla/sops)
- [Home Manager Manual](https://nix-community.github.io/home-manager/)

## ライセンス

MIT License