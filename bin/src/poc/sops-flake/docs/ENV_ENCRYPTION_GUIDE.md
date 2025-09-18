# env.sh 暗号化実装ガイド

## 1. 最小構成のセットアップ（5分で完了）

### Step 1: Age鍵の生成（初回のみ）
```bash
# 開発者各自のローカルで実行
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt

# 公開鍵を取得（チームで共有）
age-keygen -y ~/.config/sops/age/keys.txt
# 出力例: age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
```

### Step 2: プロジェクトルートに.sops.yamlを作成
```yaml
# deploy/.sops.yaml
creation_rules:
  - path_regex: .*env\.sh$
    key_groups:
      - age:
          # チームメンバーの公開鍵を追加
          - age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p  # Developer A
          - age1another_key_here...  # Developer B
```

### Step 3: env.shを暗号化
```bash
cd deploy/sliplane
sops -e env.sh > env.sh.enc
rm env.sh  # 平文削除
```

## 2. 他の開発者の使用方法

### 方法A: 自動復号化スクリプト（推奨・セキュア版）
```bash
#!/bin/bash
# deploy/sliplane/source-env.sh
set -euo pipefail

# セキュアな一時ファイルを作成
TEMP_ENV=$(mktemp -t env.XXXXXX)
chmod 600 "$TEMP_ENV"
trap "shred -u $TEMP_ENV 2>/dev/null || rm -f $TEMP_ENV" EXIT

# SOPSで復号化してsource（evalは使わない！）
if [[ -f env.sh.enc ]]; then
    sops -d env.sh.enc > "$TEMP_ENV"
    source "$TEMP_ENV"
else
    echo "Error: env.sh.enc not found"
    exit 1
fi
```

使用例:
```bash
# 環境変数を読み込む
source ./source-env.sh

# 確認
echo $API_KEY  # 復号化された値が表示される
```

### 方法B: 一時ファイル作成
```bash
# 復号化して一時的に使用
sops -d env.sh.enc > /tmp/env.sh
source /tmp/env.sh
rm /tmp/env.sh
```

### 方法C: Docker/CI環境での使用
```bash
# .gitlab-ci.yml や GitHub Actions
script:
  - export SOPS_AGE_KEY=$CI_AGE_PRIVATE_KEY
  - sops -d env.sh.enc > env.sh
  - source env.sh
  - ./deploy.sh
```

## 3. 既存プロジェクトへの最小影響導入

### Option 1: 段階的移行（推奨）
```bash
deploy/
├── sliplane/
│   ├── env.sh.enc      # 新規：暗号化版
│   ├── env.sh.example  # 新規：テンプレート
│   ├── source-env.sh   # 新規：復号化ヘルパー
│   └── deploy.sh       # 既存：変更不要
```

実装:
```bash
# env.sh.example
export API_KEY=your_api_key_here
export ORG_ID=your_org_id_here
```

```bash
# source-env.sh
#!/bin/bash
if [[ -f env.sh.enc ]]; then
    # セキュアな一時ファイル経由で復号化
    TEMP_ENV=$(mktemp -t env.XXXXXX)
    chmod 600 "$TEMP_ENV"
    sops -d env.sh.enc > "$TEMP_ENV"
    source "$TEMP_ENV"
    rm -f "$TEMP_ENV"
elif [[ -f env.sh ]]; then
    # 後方互換性：平文がある場合は警告しつつ使用
    echo "Warning: Using unencrypted env.sh (deprecated)" >&2
    source env.sh
else
    echo "Error: No env.sh or env.sh.enc found"
    exit 1
fi
```

### Option 2: Makefileでラップ
```makefile
# Makefile
.PHONY: deploy
deploy: decrypt-env
	./deploy.sh

.PHONY: decrypt-env
decrypt-env:
	@sops -d env.sh.enc > .env.tmp
	@source .env.tmp && rm .env.tmp

.PHONY: encrypt-env
encrypt-env:
	sops -e env.sh > env.sh.enc
```

### Option 3: Git Hookで自動化
```bash
# .git/hooks/pre-commit
#!/bin/bash
# env.shが存在する場合、コミットを防ぐ
if git diff --cached --name-only | grep -q "env\.sh$"; then
    echo "Error: Attempting to commit unencrypted env.sh"
    echo "Run: sops -e env.sh > env.sh.enc"
    exit 1
fi
```

## 4. チーム導入の実践例

### 初期セットアップ（リードDev）
```bash
# 1. Ageキー生成
age-keygen -o ~/.config/sops/age/keys.txt

# 2. チームメンバーから公開鍵収集
# Slackなどで共有してもらう

# 3. .sops.yaml作成
cat > .sops.yaml <<EOF
creation_rules:
  - path_regex: .*env\.sh$
    key_groups:
      - age:
          - age1dev_a_public_key
          - age1dev_b_public_key
          - age1ci_public_key
EOF

# 4. 暗号化
sops -e env.sh > env.sh.enc

# 5. コミット
git add .sops.yaml env.sh.enc env.sh.example source-env.sh
git commit -m "feat: add SOPS encryption for env.sh"
```

### 他のDeveloperの作業
```bash
# 1. リポジトリをpull
git pull

# 2. 自分のAge鍵生成（初回のみ）
age-keygen -o ~/.config/sops/age/keys.txt

# 3. 公開鍵をリードDevに送る
age-keygen -y ~/.config/sops/age/keys.txt

# 4. リードDevが.sops.yaml更新後、使用開始
source ./source-env.sh
```

## 5. トラブルシューティング

### 復号化できない場合
```bash
# Age鍵の確認
ls -la ~/.config/sops/age/keys.txt

# 公開鍵が.sops.yamlに含まれているか確認
age-keygen -y ~/.config/sops/age/keys.txt
grep $(age-keygen -y ~/.config/sops/age/keys.txt) .sops.yaml

# 手動で鍵パスを指定
SOPS_AGE_KEY_FILE=/path/to/keys.txt sops -d env.sh.enc
```

### CI/CDでの使用
```yaml
# GitHub Actions
- name: Decrypt env
  env:
    SOPS_AGE_KEY: ${{ secrets.SOPS_AGE_KEY }}
  run: |
    echo "$SOPS_AGE_KEY" > /tmp/keys.txt
    export SOPS_AGE_KEY_FILE=/tmp/keys.txt
    sops -d env.sh.enc > env.sh
    source env.sh
```

## メリット
- ✅ env.shを安全にGitにコミット可能
- ✅ チーム全員が同じ設定を共有
- ✅ CI/CDでも同じ暗号化ファイルを使用
- ✅ 設定の変更履歴が追跡可能
- ✅ 5分で導入可能