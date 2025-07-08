# OAuth2実装 - n8nアプローチ

## n8nのOAuth2実装分析

### 1. アクセストークン自動取得
- **実装済み**: n8nは自動的にトークンを取得・更新
- `OAuth2CredentialController`がOAuth2フロー全体を管理
- トークンは暗号化してデータベースに保存

### 2. 共通実装アーキテクチャ
```typescript
// n8nの階層構造
OAuth2Api (基底)
  └─ GoogleOAuth2Api (Google共通)
      └─ GmailOAuth2Api (Gmail固有スコープ)
```

### 3. プロバイダー設定管理
n8nの各プロバイダー設定：
- `authUrl`: 認証エンドポイント
- `tokenUrl`: トークン取得エンドポイント  
- `scopes`: 必要な権限スコープ
- `authQueryParameters`: 追加クエリパラメータ

## CLIでのプロバイダー対応実装

### 設定ファイル構成
```typescript
// oauth_config.ts
export const OAUTH2_PROVIDERS = {
  gmail: {
    authUrl: "https://accounts.google.com/o/oauth2/v2/auth",
    tokenUrl: "https://oauth2.googleapis.com/token",
    scopes: ["https://mail.google.com/", ...],
    authQueryParams: { access_type: "offline", prompt: "consent" }
  },
  outlook: { ... },
  yahoo: { ... }
}
```

### ID/Secretペアの渡し方

1. **環境変数**（推奨）
```bash
export GMAIL_CLIENT_ID="your-id"
export GMAIL_CLIENT_SECRET="your-secret"
```

2. **CLI引数**（一時的な使用）
```bash
nix run .#mail -- gmail fetch \
  --client-id "your-id" \
  --client-secret "your-secret"
```

3. **優先順位**
- CLI引数 > 環境変数 > エラー

### トークン管理
- プロバイダー別にトークンファイルを保存
  - `.gmail_token.json`
  - `.outlook_token.json`
- 自動リフレッシュ機能（期限5分前に更新）
- トークンファイルはローカル保存（本番環境では暗号化推奨）

### 使用例
```bash
# Gmail認証フロー
nix run .#mail -- gmail auth
# ブラウザで認証後
nix run .#mail -- gmail auth --code <認証コード>

# メール取得
nix run .#mail -- gmail fetch --unread --limit 10

# 別プロバイダー（CLI引数でクレデンシャル指定）
nix run .#mail -- outlook fetch \
  --client-id "xxx" \
  --client-secret "yyy"
```

## セキュリティ考慮事項
1. **クレデンシャル保護**
   - 環境変数での管理を推奨
   - CLI引数はシェル履歴に残る可能性
   
2. **トークン保護**
   - 現在は平文保存（POC段階）
   - 本番環境では暗号化必須

3. **スコープ最小化**
   - 必要最小限の権限のみ要求
   - プロバイダー別に適切なスコープ設定