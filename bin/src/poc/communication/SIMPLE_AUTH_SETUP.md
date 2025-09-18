# 認証セットアップ（5分で完了）

## 1. Google Cloud Consoleで準備（初回のみ）
1. [Google Cloud Console](https://console.cloud.google.com/)
2. 「APIとサービス」→「認証情報」
3. 「OAuth 2.0 クライアント ID」作成
4. リダイレクトURI: `http://localhost:8080/callback`

## 2. 環境変数設定
```bash
export GOOGLE_CLIENT_ID="xxx.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="GOCSPX-xxx"
```

## 3. 実行
```bash
nix run .#gmail
# 初回はブラウザが自動で開く → Googleでログイン → 許可
# 認証後、自動でメールが表示される
```

## 完了！
以降は `nix run .#gmail` だけで動作します。

## トラブルシューティング
- `.gmail_tokens.json`を削除すれば初回認証からやり直せます
- トークンは自動更新されるので期限切れの心配はありません