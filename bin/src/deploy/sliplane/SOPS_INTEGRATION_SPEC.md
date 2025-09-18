# deploy/sliplane SOPS暗号化導入仕様書

## 目的
API_KEY、ORG_IDなどの機密情報を含むenv.shを暗号化し、安全にGitにコミット可能にする。

## 現状
- **問題**: env.shに平文の機密情報（API_KEY、ORG_ID）
- **リスク**: Gitにコミットできない、誤って漏洩の可能性

## 実装方式
**方式B（推奨）**: env.sh.encをコミット、env.shはローカル専用

## 実装仕様

### 1. 必要ファイルの配置
poc/sops-flake/examples/env-encryptionから以下をコピー:
- encrypt-env.sh: 暗号化スクリプト
- source-env.sh: 復号化・ロードスクリプト

### 2. Age鍵の準備
```bash
# 既存鍵の確認
if [[ -f ~/.config/sops/age/keys.txt ]]; then
  echo "既存のAge鍵を使用"
else
  age-keygen -o ~/.config/sops/age/keys.txt
fi
```

### 3. env.sh暗号化
```bash
./encrypt-env.sh env.sh
# 生成物:
# - .sops.yaml: SOPS設定（自動生成）
# - env.sh.enc: 暗号化された環境変数
# - env.sh.bak: オリジナルのバックアップ
```

### 4. Git管理設定

#### .gitignore更新
```gitignore
# 平文の環境変数ファイルを除外
env.sh
env.sh.bak

# 暗号化版は追跡
!env.sh.enc
```

### 5. pre-commitフック設定

`.git/hooks/pre-commit`を作成:
```bash
#!/usr/bin/env bash
set -euo pipefail

# 1) env.shが誤ってステージされていないか確認
if git diff --cached --name-only | grep -q '^deploy/sliplane/env\.sh$'; then
  echo "ERROR: Plain env.sh staged. Use env.sh.enc instead"
  exit 1
fi

# 2) env.sh.encが暗号化済みか確認
if git ls-files --error-unmatch deploy/sliplane/env.sh.enc >/dev/null 2>&1; then
  if ! grep -q 'ENC\[AES256_GCM' deploy/sliplane/env.sh.enc; then
    echo "ERROR: env.sh.enc is not properly encrypted"
    exit 1
  fi
fi

# 3) 平文に機密情報が含まれていないか確認
if [[ -f deploy/sliplane/env.sh ]]; then
  if grep -qE 'api_rw_|org_' deploy/sliplane/env.sh; then
    echo "WARNING: Plaintext secrets detected in env.sh (local only)"
  fi
fi
```

### 6. 使用方法

#### ローカル開発
```bash
# 環境変数をロード
source ./source-env.sh env.sh.enc

# 確認
echo $API_KEY  # 復号化された値が使用可能
```

#### CI/CD統合
```yaml
# GitHub Actions例
- name: Setup SOPS
  run: |
    echo "${{ secrets.AGE_SECRET_KEY }}" > /tmp/keys.txt
    export SOPS_AGE_KEY_FILE=/tmp/keys.txt
    
- name: Decrypt and load environment
  run: |
    sops -d deploy/sliplane/env.sh.enc > deploy/sliplane/env.sh
    source deploy/sliplane/env.sh
```

### 7. チーム共有

新メンバーの公開鍵を追加:
```bash
# .sops.yamlを編集して公開鍵を追加
vim .sops.yaml

# 既存の暗号化ファイルを更新
sops updatekeys env.sh.enc
```

## テスト項目

- [ ] encrypt-env.shでenv.shを暗号化できる
- [ ] env.sh.encが生成される
- [ ] source-env.shで環境変数をロードできる
- [ ] env.shがgitignoreされている
- [ ] pre-commitフックが平文をブロックする
- [ ] CI/CDで復号化できる

## セキュリティ考慮事項

1. **秘密鍵の管理**: Age秘密鍵は絶対にコミットしない
2. **バックアップ**: env.sh.bakも.gitignoreに追加
3. **CI/CD**: 秘密鍵はSecrets/環境変数で管理
4. **定期更新**: 鍵は定期的にローテーション

## 実装手順

1. この仕様書に基づいて必要ファイルをコピー
2. Age鍵を生成または確認
3. env.shを暗号化
4. .gitignoreを更新
5. pre-commitフックを設定
6. 動作確認
7. 暗号化ファイルをコミット

## 期待される成果

- env.sh.encを安全にGitにコミット可能
- 機密情報の漏洩リスクを排除
- CI/CDでの自動デプロイ対応
- チーム内での安全な共有が可能