# sops-flake App-Standalone Template

## 概要
このテンプレートは、独立アプリケーション向けのsops-nix統合を提供します。
機密情報を安全に管理し、Gitにコミット可能な形式で暗号化します。

## クイックスタート

```bash
# 1. テンプレートのクローン
cp -r /path/to/templates/app-standalone my-app
cd my-app

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

## App-Standalone Template固有セクション

### 特徴
- **OS独立**: NixOS設定変更不要
- **nix run対応**: 直接実行サポート
- **Docker対応**: コンテナビルド組み込み済み
- **ランタイム復号化**: 実行時にsopsでシークレット復号化

### 使用ケース
- 🚀 マイクロサービス
- 🌐 Web API
- 🛠️ 開発ツール
- 📦 コンテナ化アプリケーション

### 実行方法

#### 直接実行
```bash
# ローカル実行
nix run

# リモートから実行
nix run github:yourorg/my-app

# 引数付き実行
nix run . -- --port 8080 --config production
```

#### Docker実行
```bash
# コンテナイメージのビルド
nix build .#container

# Dockerイメージとして読み込み
docker load < result

# 実行
docker run -p 8080:8080 my-app:latest
```

#### 開発環境
```bash
# 開発環境起動（依存関係含む）
nix develop

# 環境内でのビルド・実行
cargo run  # Rustの場合
npm start  # Node.jsの場合
python main.py  # Pythonの場合
```

### 利点

1. **OS変更不要**: `/etc/nixos/`の変更なしにデプロイ可能
2. **ポータブル**: Nixがあればどこでも実行可能
3. **スケーラブル**: OS肥大化なしに100のアプリをデプロイ可能
4. **CI/CD親和性**: 自動化デプロイに最適

### シークレット管理統合

#### アプリケーション内での使用例

##### Rust
```rust
use serde_yaml;
use std::process::Command;

fn load_secrets() -> Result<AppSecrets, Box<dyn std::error::Error>> {
    let output = Command::new("sops")
        .args(&["-d", "secrets/app.yaml"])
        .output()?;
    
    let secrets: AppSecrets = serde_yaml::from_slice(&output.stdout)?;
    Ok(secrets)
}
```

##### Python
```python
import subprocess
import yaml

def load_secrets():
    result = subprocess.run(['sops', '-d', 'secrets/app.yaml'], 
                          capture_output=True, text=True)
    return yaml.safe_load(result.stdout)
```

##### Node.js
```javascript
const { execSync } = require('child_process');
const yaml = require('js-yaml');

function loadSecrets() {
    const output = execSync('sops -d secrets/app.yaml', { encoding: 'utf8' });
    return yaml.load(output);
}
```

### 本番環境デプロイ

#### Dockerでの本番デプロイ
```bash
# マルチステージビルドでのセキュア構成
# Dockerfile例:
FROM nixos/nix as builder
COPY . /app
WORKDIR /app
RUN nix build .#container

FROM scratch
COPY --from=builder /app/result /app
EXPOSE 8080
ENTRYPOINT ["/app/bin/my-app"]
```

#### Kubernetes統合
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: my-app
        image: my-app:latest
        env:
        - name: SOPS_AGE_KEY
          valueFrom:
            secretKeyRef:
              name: sops-keys
              key: age-key
```

## トラブルシューティング

### よくある問題

**Q: sops editで「no data key found」エラー**
A: .sops.yamlの公開鍵が正しいか確認し、対応する秘密鍵がSOPS_AGE_KEY_FILEにあることを確認

**Q: Git commitが「plaintext secrets detected」で失敗**
A: secrets/内のファイルを暗号化: `sops -e -i secrets/app.yaml`

**Q: nix developが起動しない**
A: `nix flake update`で依存関係を更新

**Q: nix runでアプリケーションが起動しない**
A: flake.nixのoutputsでappsが正しく定義されているかチェック

**Q: Dockerコンテナ内でシークレットが復号化できない**
A: コンテナ内にSOPS_AGE_KEYまたはSOPS_AGE_KEY_FILEが設定されているかチェック

## セキュリティベストプラクティス

1. **秘密鍵の保護**: Age秘密鍵は絶対にGitにコミットしない
2. **公開鍵の共有**: チームメンバーの公開鍵を.sops.yamlに追加
3. **定期的な鍵更新**: 定期的に暗号化鍵をローテーション
4. **最小権限原則**: 必要なユーザー/サービスのみにアクセス許可
5. **ランタイムセキュリティ**: シークレットは実行時のみメモリに保持
6. **コンテナセキュリティ**: イメージに平文シークレットを含めない

## 関連リンク

- [sops-nix Documentation](https://github.com/Mic92/sops-nix)
- [age Encryption](https://github.com/FiloSottile/age)
- [SOPS](https://github.com/mozilla/sops)
- [Nix Flakes Book](https://nixos.wiki/wiki/Flakes)

## ライセンス

MIT License