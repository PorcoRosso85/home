# Hono OAuth2ミドルウェアのテスト戦略分析

## 🔍 テスト手法: MSW (Mock Service Worker)

### 概要
MSWを使用して、実際のOAuth2プロバイダーのAPIレスポンスを完全にモックしています。

```typescript
import { HttpResponse, http } from 'msw'
```

## 📋 テスト戦略の特徴

### 1. **プロバイダーごとのモック実装**
各プロバイダーの実際のAPIエンドポイントをモック：
- Google: `oauth2.googleapis.com`
- Facebook: `graph.facebook.com`
- GitHub: `github.com/login/oauth`
- その他多数

### 2. **成功・失敗パターンの網羅**
```typescript
// 成功パターン
if (body.code === dummyCode) {
  return HttpResponse.json(dummyToken)
}
// 失敗パターン
return HttpResponse.json(googleCodeError)
```

### 3. **共通のダミーデータ**
```typescript
export const dummyCode = '4/0AfJohXl9tS46Em...'
export const dummyToken = {
  access_token: '15d42a4d-1948-4de4-ba78-b8a893feaf45',
  expires_in: 60000,
  scope: 'openid email profile',
}
```

## 🎯 テストシナリオ

### Authorization Code フロー
1. **認証コードの検証**
   ```typescript
   http.post('https://oauth2.googleapis.com/token', async ({ request }) => {
     const body = await request.json()
     if (body.code === dummyCode) {
       return HttpResponse.json(dummyToken)
     }
     return HttpResponse.json(googleCodeError)
   })
   ```

2. **ユーザー情報の取得**
   ```typescript
   http.get('https://www.googleapis.com/oauth2/v2/userinfo', async ({ request }) => {
     const authorization = request.headers.get('authorization')
     if (authorization === `Bearer ${dummyToken.access_token}`) {
       return HttpResponse.json(googleUser)
     }
     return HttpResponse.json(googleTokenError)
   })
   ```

### Refresh Token フロー
```typescript
if (grant_type === 'refresh_token') {
  const refresh_token = params.get('refresh_token')
  if (refresh_token === 'wrong-refresh-token') {
    return HttpResponse.json(discordRefreshTokenError)
  }
  return HttpResponse.json(discordRefreshToken)
}
```

### Token Revocation
```typescript
http.post('https://api.twitter.com/2/oauth2/revoke', async ({ request }) => {
  const token = new URLSearchParams(request.url.split('?')[1]).get('token')
  if (token === 'wrong-token') {
    return HttpResponse.json(xRevokeTokenError)
  }
  return HttpResponse.json({ revoked: true })
})
```

## 💡 このアプローチの利点

1. **完全にオフライン**
   - 外部APIへの依存なし
   - テスト環境でのネットワーク問題なし
   - CI/CDで安定動作

2. **プロバイダー固有の挙動を再現**
   - Googleの`tokeninfo`エンドポイント
   - Facebookのグラフクエリ形式
   - Twitchの`validate`エンドポイント

3. **エラーケースの網羅**
   - 無効なコード
   - 無効なトークン
   - リフレッシュトークンエラー
   - Revocationエラー

## 🔧 実際のテストコード例（推測）

```typescript
import { setupServer } from 'msw/node'
import { handlers } from './mocks'

const server = setupServer(...handlers)

describe('OAuth2 Middleware', () => {
  beforeAll(() => server.listen())
  afterEach(() => server.resetHandlers())
  afterAll(() => server.close())

  test('Google OAuth2フロー', async () => {
    // 1. 認証URLの生成
    const authUrl = middleware.generateAuthUrl('google')
    expect(authUrl).toContain('https://accounts.google.com')

    // 2. コールバック処理（MSWがモックレスポンスを返す）
    const token = await middleware.handleCallback('google', dummyCode)
    expect(token.access_token).toBe(dummyToken.access_token)

    // 3. ユーザー情報取得（MSWがモックユーザーを返す）
    const user = await middleware.getUserInfo('google', token)
    expect(user.email).toBe('example@email.com')
  })
})
```

## 🎯 POCへの応用

このアプローチを参考に、我々のPOCでも：

1. **MSWでOAuth2プロバイダーをモック**
2. **成功・失敗の両パターンをテスト**
3. **トークンリフレッシュも含めた完全なフロー**
4. **プロバイダー固有の挙動も再現**

これにより、外部依存なしで完全な自動テストが実現可能です。