# Cloudflare R2 CLI完結セットアップガイド

## 結論: ほぼCLIで完結可能！

```
初回のみWebが必要:
┌───────────────────┐
│ Cloudflare Web    │
│ Dashboard         │ → API Token取得（初回のみ）
└─────────┬─────────┘
          │
          ↓
┌───────────────────┐
│  以降はCLIで完結  │
│  - バケット作成   │
│  - ファイル操作   │
│  - 管理全般       │
└───────────────────┘
```

## セットアップ手順

### 1. 初回のみ: APIトークン取得（Web必須）
- Cloudflare Dashboard → My Profile → API Tokens
- Create Token → R2 Token テンプレートを選択
- Account ResourcesでR2:Editを設定

### 2. Wrangler CLIインストール
```bash
npm install -g wrangler
```

### 3. CLIで認証
```bash
wrangler login
# または環境変数でトークン設定
export CLOUDFLARE_API_TOKEN="your-api-token"
```

### 4. CLIでR2バケット作成
```bash
# バケット作成
wrangler r2 bucket create my-bucket

# バケット一覧表示
wrangler r2 bucket list

# バケット削除
wrangler r2 bucket delete my-bucket
```

### 5. ファイル操作
```bash
# アップロード
wrangler r2 object put my-bucket/file.txt --file ./local-file.txt

# ダウンロード
wrangler r2 object get my-bucket/file.txt --file ./downloaded.txt

# 一覧表示
wrangler r2 object list my-bucket

# 削除
wrangler r2 object delete my-bucket/file.txt
```

## 代替: S3互換CLIツール

### MinIO Client (mc)
```bash
# エイリアス設定
mc alias set r2 https://[account-id].r2.cloudflarestorage.com \
  [access-key-id] [secret-access-key]

# バケット作成
mc mb r2/my-bucket

# ファイル操作
mc cp file.txt r2/my-bucket/
mc ls r2/my-bucket
```

### AWS CLI
```bash
# 設定
aws configure set aws_access_key_id [access-key-id] --profile r2
aws configure set aws_secret_access_key [secret-access-key] --profile r2
aws configure set region auto --profile r2

# バケット作成
aws s3api create-bucket --bucket my-bucket \
  --endpoint-url https://[account-id].r2.cloudflarestorage.com \
  --profile r2

# ファイル操作
aws s3 cp file.txt s3://my-bucket/ \
  --endpoint-url https://[account-id].r2.cloudflarestorage.com \
  --profile r2
```

## まとめ
- 初回のAPIトークン取得のみWebダッシュボードが必要
- それ以降はすべてCLIで完結可能
- Wrangler、MinIO Client、AWS CLIなど複数の選択肢あり