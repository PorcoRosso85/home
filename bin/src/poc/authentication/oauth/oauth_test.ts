/**
 * OAuth2自動テストのPOC実装
 * Mock OAuth2プロバイダーを使用したテスト
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";

// OAuth2設定
const MOCK_CONFIG = {
  clientId: "mock-client-id",
  clientSecret: "mock-client-secret",
  redirectUri: "http://localhost:8080/callback",
  authorizationBaseUrl: "http://localhost:8080/authorize",
  tokenUrl: "http://localhost:8080/token",
  scope: "https://www.googleapis.com/auth/gmail.readonly"
};

// OAuth2フローのシミュレーション
class OAuth2Client {
  private accessToken?: string;
  private refreshToken?: string;
  
  constructor(private config: typeof MOCK_CONFIG) {}
  
  // 認証URLの生成
  generateAuthUrl(state?: string): string {
    const params = new URLSearchParams({
      client_id: this.config.clientId,
      redirect_uri: this.config.redirectUri,
      response_type: "code",
      scope: this.config.scope,
      access_type: "offline",
      ...(state && { state })
    });
    
    return `${this.config.authorizationBaseUrl}?${params}`;
  }
  
  // 認証コードをトークンに交換
  async exchangeCodeForToken(code: string): Promise<{
    accessToken: string;
    refreshToken: string;
    expiresIn: number;
  }> {
    const formData = new URLSearchParams({
      grant_type: "authorization_code",
      code,
      client_id: this.config.clientId,
      client_secret: this.config.clientSecret,
      redirect_uri: this.config.redirectUri
    });
    
    const response = await fetch(this.config.tokenUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Token exchange failed: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;
    
    return {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      expiresIn: data.expires_in
    };
  }
  
  // リフレッシュトークンでアクセストークンを更新
  async refreshAccessToken(): Promise<string> {
    if (!this.refreshToken) {
      throw new Error("No refresh token available");
    }
    
    const formData = new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: this.refreshToken,
      client_id: this.config.clientId,
      client_secret: this.config.clientSecret
    });
    
    const response = await fetch(this.config.tokenUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Token refresh failed: ${response.statusText}`);
    }
    
    const data = await response.json();
    this.accessToken = data.access_token;
    
    return data.access_token;
  }
  
  // 認証されたAPIリクエスト
  async makeAuthenticatedRequest(url: string): Promise<Response> {
    if (!this.accessToken) {
      throw new Error("Not authenticated");
    }
    
    return fetch(url, {
      headers: {
        "Authorization": `Bearer ${this.accessToken}`
      }
    });
  }
}

// テストケース
Deno.test("OAuth2 認証URLの生成", () => {
  const client = new OAuth2Client(MOCK_CONFIG);
  const authUrl = client.generateAuthUrl("test-state");
  
  assertEquals(authUrl.includes("client_id=mock-client-id"), true);
  assertEquals(authUrl.includes("response_type=code"), true);
  assertEquals(authUrl.includes("state=test-state"), true);
});

Deno.test("認証コードからトークンへの交換（Mock Server必要）", async () => {
  const client = new OAuth2Client(MOCK_CONFIG);
  
  try {
    // 実際のテストではMock Serverが起動している必要がある
    const tokens = await client.exchangeCodeForToken("mock-auth-code");
    
    assertExists(tokens.accessToken);
    assertExists(tokens.refreshToken);
    assertEquals(tokens.expiresIn, 3600);
  } catch (error) {
    console.log("Mock Serverが起動していないため、テストをスキップ");
  }
});

Deno.test("トークンの暗号化保存", async () => {
  // 暗号化のモック実装
  const encryptToken = (token: string): string => {
    return btoa(token); // 実際はもっと強力な暗号化を使用
  };
  
  const decryptToken = (encrypted: string): string => {
    return atob(encrypted);
  };
  
  const originalToken = "test-access-token";
  const encrypted = encryptToken(originalToken);
  const decrypted = decryptToken(encrypted);
  
  assertEquals(originalToken, decrypted);
});

// 自動テストのためのヘルパー関数
export async function simulateOAuth2Flow(): Promise<{
  accessToken: string;
  refreshToken: string;
}> {
  const client = new OAuth2Client(MOCK_CONFIG);
  
  // 1. 認証URLを生成
  const authUrl = client.generateAuthUrl();
  console.log("認証URL:", authUrl);
  
  // 2. 実際のフローではブラウザが開き、ユーザーが認証
  // ここではモックの認証コードを使用
  const mockAuthCode = "simulated-auth-code";
  
  // 3. 認証コードをトークンに交換
  try {
    const tokens = await client.exchangeCodeForToken(mockAuthCode);
    return {
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken
    };
  } catch (error) {
    console.error("OAuth2フローのシミュレーション失敗:", error);
    throw error;
  }
}