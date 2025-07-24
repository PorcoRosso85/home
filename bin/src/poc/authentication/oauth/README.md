# OAuth 自動テスト化 POC

OAuth認証フローの自動テスト化を実現するPOC

## 目的
- OAuth2認証フローの自動化
- CIでのテスト実行を可能にする
- 手動介入なしでの認証テスト

## 技術的課題と解決策

### 1. OAuth2フローの自動化
- **課題**: ブラウザでの手動認証が必要
- **解決**: ヘッドレスブラウザ（Playwright/Puppeteer）でのフロー自動化

### 2. リフレッシュトークンの管理
- **課題**: アクセストークンの有効期限
- **解決**: リフレッシュトークンの永続化と自動更新

### 3. テスト用認証情報の安全な管理
- **課題**: 本番認証情報の漏洩リスク
- **解決**: 
  - テスト専用のOAuth2アプリケーション
  - 環境変数での認証情報管理
  - ローカル暗号化ストレージ

## 実装アプローチ

### Phase 1: Mock OAuth2 Provider
```typescript
// ローカルでOAuth2プロバイダーをモック
// 開発・テスト環境での高速な反復
```

### Phase 2: Real Provider Integration
```typescript
// 実際のGmail OAuth2での自動テスト
// ヘッドレスブラウザでの認証フロー
```

### Phase 3: Token Management
```typescript
// リフレッシュトークンの自動管理
// 暗号化ストレージへの保存
```

## 実行方法
```bash
# デフォルト: README表示
nix run .

# テスト実行
nix run .#test

# Mock OAuth2サーバー起動
nix run .#mock-server

# 実際のOAuth2フローテスト
nix run .#real-oauth-test
```

## 参考実装
- n8nのGmailOAuth2Api実装
- Google APIs Node.js Clientの認証フロー
- OAuth2 Mock Serverプロジェクト

## n8nのOAuth2実装調査

### n8nの独自実装アプローチ
n8nは汎用的なOAuth2ライブラリを使用せず、**独自のOAuth2クライアントライブラリ**（`@n8n/client-oauth2`）を実装している。

#### 実装の構造
```
packages/@n8n/client-oauth2/
├── ClientOAuth2 クラス (メインクライアント)
├── CodeFlow (Authorization Code フロー)
├── CredentialsFlow (Client Credentials フロー)
└── PKCEサポート
```

#### 認証情報の階層構造
```
OAuth2Api (基底クラス)
├── GoogleOAuth2Api (Google共通設定)
│   ├── GmailOAuth2Api (Gmail固有のscope)
│   ├── GoogleDriveOAuth2Api
│   └── GoogleSheetsOAuth2Api
├── MicrosoftOAuth2Api
├── SlackOAuth2Api
└── 30+ その他のプロバイダー
```

### なぜ独自実装なのか？

1. **統一的なインターフェース**
   - すべてのOAuth2プロバイダーを同じ方法で扱える
   - ワークフロー内での一貫した認証体験

2. **n8n固有の要件**
   - ワークフロー実行中のトークン自動更新
   - 認証情報の暗号化と永続化
   - UIとの密な統合

3. **エンタープライズ対応**
   - プロキシ設定のサポート
   - SSL証明書の柔軟な設定
   - カスタムOAuth2エンドポイント

### 一般的なOAuth2ライブラリとの比較

#### 汎用ライブラリの例
- **passport.js**: Express向けの認証ミドルウェア
- **simple-oauth2**: シンプルなOAuth2クライアント
- **node-oauth2-server**: OAuth2サーバー実装

#### n8nアプローチの利点
- ワークフローエンジンとの深い統合
- 統一的なエラーハンドリング
- プロバイダー固有の quirks への対応

### POCへの応用
このPOCでは、n8nのアプローチを参考にしつつ：
1. まずシンプルなOAuth2クライアント実装から開始
2. 自動テストに必要な最小限の機能を実装
3. 必要に応じてn8nの設計パターンを採用

## @n8n/client-oauth2 の単独使用

### 利点
- **ワークフロー非依存**: OAuth2部分のみを切り出して使用可能
- **プロバイダー抽象化**: Google, Microsoft, Slack等を統一インターフェースで扱える
- **自動更新**: リフレッシュトークンによる自動更新機能内蔵
- **PKCE対応**: セキュアな認証フロー

### 使用例
```typescript
import { ClientOAuth2 } from '@n8n/client-oauth2';

const client = new ClientOAuth2({
  clientId: process.env.GOOGLE_CLIENT_ID,
  clientSecret: process.env.GOOGLE_CLIENT_SECRET,
  accessTokenUri: 'https://oauth2.googleapis.com/token',
  authorizationUri: 'https://accounts.google.com/o/oauth2/v2/auth',
  redirectUri: 'http://localhost:3000/callback',
  scopes: ['https://www.googleapis.com/auth/gmail.readonly']
});

// 認証URLの生成
const authUrl = client.code.getUri();

// コールバック処理
const token = await client.code.getToken(req.originalUrl);
```

### 自動テストの実現可能性

#### 方法1: Mock OAuth2 Server
- **実装**: `oauth2-mock-server` パッケージを使用
- **利点**: 完全にローカルで動作、高速
- **欠点**: 実際のプロバイダーとの差異

#### 方法2: Playwright + 実プロバイダー
- **実装**: ヘッドレスブラウザで実際の認証フロー
- **利点**: 本番に近い環境でのテスト
- **欠点**: テスト用アカウントの管理が必要

#### 方法3: Service Account (推奨)
- **実装**: OAuth2ではなくService Account認証を使用
- **利点**: ブラウザ不要、CI/CDで安定動作
- **欠点**: OAuth2フロー自体のテストではない

### 実装計画
1. `@n8n/client-oauth2` を使った基本実装
2. Mock Serverでの単体テスト
3. Playwrightでの統合テスト（オプション）
4. Service Accountでの自動テスト環境構築