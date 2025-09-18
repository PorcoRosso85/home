# 既存プロジェクトへのsops統合ガイド

## 概要
既存プロジェクトのenv.shファイルを**5分で暗号化**し、安全にGitリポジトリで管理するための統合ガイドです。

## env.shファイルの暗号化

既存のenv.shファイルを暗号化してGitにコミット可能にする手順:

### 1. 暗号化実行
```bash
./encrypt-env.sh /path/to/env.sh
```

この操作により:
- env.shが暗号化されてenv.sh.encとして保存
- 元のenv.shファイルは削除
- .sops.yamlが自動生成/更新

### 2. Gitへのコミット
```bash
git add env.sh.enc .sops.yaml
git commit -m "Add encrypted environment variables"
```

### 3. 使用時の復号化
```bash
source ./source-env.sh env.sh.enc
```

## クイックスタート

```bash
# 1. セットアップスクリプトを実行
./setup.sh

# 2. env.shを作成（既存のものがあればそれを使用）
cp env.sh.example env.sh
vim env.sh  # 実際の値を入力

# 3. 暗号化
./encrypt-env.sh

# 4. 平文を削除
rm env.sh

# 5. 使用
source ./source-env.sh
echo $API_KEY  # 復号化された値が使える
```

## ファイル構成

```
deploy/sliplane/
├── env.sh.enc        # 暗号化されたenv（Gitにコミット）
├── env.sh.example    # テンプレート（Gitにコミット）
├── .sops.yaml        # 暗号化設定（Gitにコミット）
├── source-env.sh     # 復号化ヘルパー（Gitにコミット）
├── encrypt-env.sh    # 暗号化ヘルパー（Gitにコミット）
└── env.sh           # 平文（.gitignoreに追加、絶対コミットしない）
```

## CI/CD統合

### GitHub Actions例
```yaml
name: Deploy with encrypted env

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Install sops and age
      run: |
        wget https://github.com/mozilla/sops/releases/latest/download/sops-v3.7.3.linux.amd64 -O sops
        chmod +x sops && sudo mv sops /usr/local/bin/
        wget https://github.com/FiloSottile/age/releases/latest/download/age-v1.1.1-linux-amd64.tar.gz
        tar xf age-*.tar.gz && sudo mv age/age* /usr/local/bin/
        
    - name: Setup SOPS
      run: |
        echo "${{ secrets.AGE_SECRET_KEY }}" > keys.txt
        export SOPS_AGE_KEY_FILE=keys.txt
        
    - name: Decrypt secrets
      run: sops decrypt env.sh.enc > env.sh
      
    - name: Deploy
      run: |
        source ./env.sh
        ./deploy.sh
```

### GitLab CI例
```yaml
deploy:
  stage: deploy
  before_script:
    - apk add --no-cache wget tar
    - wget -O sops https://github.com/mozilla/sops/releases/latest/download/sops-v3.7.3.linux.amd64
    - chmod +x sops && mv sops /usr/local/bin/
    - echo "$AGE_SECRET_KEY" > keys.txt
    - export SOPS_AGE_KEY_FILE=keys.txt
  script:
    - sops decrypt env.sh.enc > env.sh
    - source ./env.sh
    - ./deploy.sh
  after_script:
    - rm -f env.sh keys.txt  # クリーンアップ
```

### Jenkins Pipeline例
```groovy
pipeline {
    agent any
    stages {
        stage('Decrypt Secrets') {
            steps {
                withCredentials([string(credentialsId: 'age-secret-key', variable: 'AGE_SECRET_KEY')]) {
                    sh '''
                        echo "$AGE_SECRET_KEY" > keys.txt
                        export SOPS_AGE_KEY_FILE=keys.txt
                        sops decrypt env.sh.enc > env.sh
                    '''
                }
            }
        }
        stage('Deploy') {
            steps {
                sh '''
                    source ./env.sh
                    ./deploy.sh
                '''
            }
        }
    }
    post {
        always {
            sh 'rm -f env.sh keys.txt'
        }
    }
}
```

## チーム共有

### 1. チーム全体での導入手順

#### リーダーの作業
```bash
# 1. セットアップ実行
./setup.sh

# 2. チームメンバーの公開鍵を収集
# Slackで「age-keygen -y ~/.config/sops/age/keys.txt」の結果を共有してもらう

# 3. .sops.yamlに追加
vim .sops.yaml
# age:
#   - age1xxx...  # 自分
#   - age1yyy...  # メンバーA
#   - age1zzz...  # メンバーB

# 4. 暗号化してコミット
./encrypt-env.sh
git add env.sh.enc .sops.yaml source-env.sh encrypt-env.sh
git commit -m "feat: add encrypted env.sh"
git push
```

#### メンバーの作業
```bash
# 1. Pull
git pull

# 2. Age鍵生成（初回のみ）
age-keygen -o ~/.config/sops/age/keys.txt

# 3. 公開鍵をリーダーに送る
age-keygen -y ~/.config/sops/age/keys.txt
# この出力をSlackで共有

# 4. リーダーが.sops.yaml更新後
git pull
source ./source-env.sh  # 使用開始！
```

### 2. 新メンバー追加手順

#### 既存メンバーの作業
```bash
# 1. 新メンバーに公開鍵生成を依頼
# "age-keygen -o ~/.config/sops/age/keys.txt && age-keygen -y ~/.config/sops/age/keys.txt"

# 2. .sops.yamlに公開鍵追加
vim .sops.yaml

# 3. 鍵を更新（重要: 全員がアクセスできるように再暗号化）
sops updatekeys env.sh.enc

# 4. コミット
git add .sops.yaml env.sh.enc
git commit -m "chore: add new team member key"
git push
```

#### 新メンバーの作業
```bash
# 1. リポジトリクローン
git clone <repository>
cd <repository>

# 2. Age鍵生成（まだしていない場合）
age-keygen -o ~/.config/sops/age/keys.txt

# 3. 公開鍵を既存メンバーに送る
age-keygen -y ~/.config/sops/age/keys.txt

# 4. updatekeys完了後
git pull
source ./source-env.sh  # 使用可能！
```

## ワークフロー統合パターン

### パターン1: デプロイスクリプトでの使用
```bash
#!/bin/bash
# deploy.sh

# 環境変数を読み込む
source ./source-env.sh

# 既存のコードは変更不要
curl -H "Authorization: Bearer $API_KEY" \
     -H "X-Org-Id: $ORG_ID" \
     https://api.example.com/deploy
```

### パターン2: Makefileでの使用
```makefile
.PHONY: deploy test

deploy: 
	@source ./source-env.sh && ./deploy.sh

test:
	@source ./source-env.sh && npm test

build:
	@source ./source-env.sh && npm run build
```

### パターン3: Docker Composeでの使用

#### 方法A: env_file使用
```bash
# 事前に復号化してenv_fileで読み込む
sops -d env.sh.enc > .env.decrypted
docker-compose up
# 終了後に必ず削除
rm .env.decrypted
```

```yaml
# docker-compose.yml
version: '3'
services:
  app:
    build: .
    env_file:
      - .env.decrypted  # 事前に復号化したファイル
```

#### 方法B: シェルスクリプトでラップ
```bash
#!/bin/bash
# docker-run.sh
TEMP_ENV=$(mktemp)
trap 'rm -f "$TEMP_ENV"' EXIT

sops -d env.sh.enc > "$TEMP_ENV"
docker-compose --env-file "$TEMP_ENV" up
```

### パターン4: Terraform統合
```bash
#!/bin/bash
# terraform-apply.sh

# シークレットを復号化
source ./source-env.sh

# Terraform変数として利用
terraform apply \
  -var="database_url=$DATABASE_URL" \
  -var="api_key=$API_KEY" \
  -auto-approve
```

## 高度な使用方法

### 環境別設定
```bash
# 異なる環境ごとに暗号化ファイルを分離
├── env.development.enc
├── env.staging.enc
├── env.production.enc
└── .sops.yaml  # 環境ごとに異なる公開鍵設定可能
```

```bash
# 環境指定での使用
source ./source-env.sh env.staging.enc
```

### ロールベース管理
```yaml
# .sops.yaml - ロールベースアクセス制御
creation_rules:
  - path_regex: env\.development\.enc$
    age: >-
      age1dev1...,
      age1dev2...
  - path_regex: env\.production\.enc$
    age: >-
      age1admin1...,
      age1admin2...
```

## セキュリティ注意事項

### してはいけないこと
- ❌ 平文のenv.shをコミット
- ❌ 秘密鍵（~/.config/sops/age/keys.txt）を共有
- ❌ 復号化したファイルを残す
- ❌ CI/CDログに環境変数を出力

### すべきこと
- ✅ env.shを.gitignoreに追加
- ✅ 定期的に鍵をローテーション
- ✅ CI/CD用の専用鍵を作成
- ✅ 最小権限原則でアクセス制御
- ✅ 使用後の一時ファイル削除

## トラブルシューティング

### 「Failed to decrypt」エラー
```bash
# 1. 鍵の存在確認
ls -la ~/.config/sops/age/keys.txt

# 2. 公開鍵が.sops.yamlにあるか確認
age-keygen -y ~/.config/sops/age/keys.txt
grep <公開鍵> .sops.yaml

# 3. 手動で鍵パス指定
SOPS_AGE_KEY_FILE=/path/to/key sops -d env.sh.enc
```

### チームメンバーを追加
```bash
# 1. .sops.yamlに公開鍵追加
vim .sops.yaml

# 2. 鍵を更新
sops updatekeys env.sh.enc

# 3. コミット
git add .sops.yaml env.sh.enc
git commit -m "chore: add new team member key"
```

### CI/CDでの認証エラー
```bash
# 環境変数確認
echo "SOPS_AGE_KEY_FILE: $SOPS_AGE_KEY_FILE"
echo "SOPS_AGE_KEY length: ${#SOPS_AGE_KEY}"

# 手動テスト
export SOPS_AGE_KEY="age1..."
sops decrypt env.sh.enc
```

## 導入前後の比較

| 項目 | Before | After |
|------|---------|--------|
| env.sh管理 | ローカルのみ/Slackで共有 | Gitで暗号化管理 |
| セキュリティ | 平文で危険 | 暗号化で安全 |
| チーム共有 | 手動でコピー | git pullで自動 |
| 変更履歴 | 追跡不可 | Gitで完全追跡 |
| CI/CD | 手動設定 | 同じ暗号化ファイル使用 |
| 導入時間 | - | 5分 |
| メンテナンス | 各自で管理 | 統一された手順 |

## まとめ

このガイドにより、既存プロジェクトに以下の価値を提供:

- **5分で導入完了**: 既存ワークフローへの最小影響
- **既存コードの変更不要**: デプロイスクリプトや設定の変更なし
- **チーム全員が同じ設定を安全に共有**: 暗号化による安全性
- **Git管理で変更履歴を追跡可能**: 透明性とアカウンタビリティ
- **CI/CD完全統合**: 自動化デプロイメントパイプラインとの相性
- **環境別管理**: 開発・ステージング・本番の分離