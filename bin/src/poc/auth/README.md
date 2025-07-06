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