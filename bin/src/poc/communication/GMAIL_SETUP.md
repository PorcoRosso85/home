# Gmail API 実行手順

## 事前準備

### 1. Google Cloud Console での設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）
3. **APIs & Services > Library** で "Gmail API" を検索して有効化
4. **APIs & Services > Credentials** に移動
5. **Create Credentials > OAuth client ID** を選択
6. Application type: **Desktop app** を選択
7. 作成されたClient IDとClient Secretをメモ

### 2. 環境変数の設定

```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

## 実行手順

### 方法1: 手動でトークンを取得

```bash
# 1. 認証URLを取得
nix run .#gmail -- auth

# 2. 表示されたURLをブラウザで開いて認証

# 3. リダイレクト先のURLから code パラメータをコピー
# 例: http://localhost:8080/callback?code=4/0AeaYSH...&scope=...

# 4. curlでトークンを取得
curl -X POST https://oauth2.googleapis.com/token \
  -d "code=取得したコード" \
  -d "client_id=$GOOGLE_CLIENT_ID" \
  -d "client_secret=$GOOGLE_CLIENT_SECRET" \
  -d "redirect_uri=http://localhost:8080/callback" \
  -d "grant_type=authorization_code"

# 5. 取得したaccess_tokenを環境変数に設定
export GMAIL_ACCESS_TOKEN="取得したアクセストークン"

# 6. メールを取得
nix run .#gmail -- fetch --unread --limit 5
```

### 方法2: OAuth2ヘルパーを使用（推奨）

```bash
# ターミナル1: コールバックサーバーを起動
nix run .#oauth -- server

# ターミナル2: 認証フローを開始
# 1. 認証URLを取得
nix run .#gmail -- auth

# 2. 表示されたURLをブラウザで開いて認証
# 3. リダイレクトされたページに表示されたコードをコピー

# 4. トークンに交換
nix run .#oauth -- exchange --code 取得したコード

# 5. 表示されたコマンドを実行
export GMAIL_ACCESS_TOKEN="表示されたトークン"

# 6. メールを取得
nix run .#gmail -- fetch --unread --limit 5
```

## 利用可能なコマンド

```bash
# 認証フローを開始
nix run .#gmail -- auth

# メールを取得（全て）
nix run .#gmail -- fetch

# 未読メールのみ取得
nix run .#gmail -- fetch --unread

# 件数を制限
nix run .#gmail -- fetch --limit 10

# 日付でフィルタ
nix run .#gmail -- fetch --since 2024-01-01

# 組み合わせ
nix run .#gmail -- fetch --unread --limit 5 --since 2024-01-01
```

## トラブルシューティング

### "invalid_client" エラー
- Client IDとClient Secretが正しいか確認
- リダイレクトURIが `http://localhost:8080/callback` と完全一致しているか確認

### "invalid_grant" エラー
- 認証コードは一度しか使えません。再度認証フローを実行してください
- 認証コードの有効期限は短いので、すぐにトークンに交換してください

### "insufficient_permission" エラー
- Gmail APIが有効化されているか確認
- スコープに `https://www.googleapis.com/auth/gmail.readonly` が含まれているか確認

## セキュリティ注意事項

- アクセストークンは機密情報です。Gitにコミットしないでください
- トークンの有効期限は通常1時間です
- 本番環境ではリフレッシュトークンを使用して自動更新を実装してください