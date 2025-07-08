/**
 * Google OAuth2クライアント
 * google-auth-library（Apache 2.0）を使用した実装
 */

import { OAuth2Client } from "npm:google-auth-library@9.14.2";
import type { Credentials } from "npm:google-auth-library@9.14.2";

export interface GoogleOAuth2Config {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  scopes: string[];
}

export class GoogleOAuth2Helper {
  private oauth2Client: OAuth2Client;
  
  constructor(private config: GoogleOAuth2Config) {
    this.oauth2Client = new OAuth2Client(
      config.clientId,
      config.clientSecret,
      config.redirectUri
    );
  }
  
  /**
   * 認証URLを生成
   */
  getAuthUrl(state?: string): string {
    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: this.config.scopes,
      state: state,
      prompt: 'consent'
    });
  }
  
  /**
   * 認証コードをトークンに交換
   */
  async getToken(code: string): Promise<Credentials> {
    const { tokens } = await this.oauth2Client.getToken(code);
    this.oauth2Client.setCredentials(tokens);
    return tokens;
  }
  
  /**
   * トークンを設定
   */
  setCredentials(tokens: Credentials): void {
    this.oauth2Client.setCredentials(tokens);
  }
  
  /**
   * アクセストークンを取得（必要に応じて自動リフレッシュ）
   */
  async getAccessToken(): Promise<string> {
    const { token } = await this.oauth2Client.getAccessToken();
    if (!token) {
      throw new Error('Failed to get access token');
    }
    return token;
  }
  
  /**
   * OAuth2クライアントを取得（Gmail APIで使用）
   */
  getClient(): OAuth2Client {
    return this.oauth2Client;
  }
}