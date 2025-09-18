/**
 * 自動認証マネージャー
 * 初回認証後は自動的にトークンを管理
 */

import { OAuth2Client } from "npm:google-auth-library@9.14.2";
import type { Credentials } from "npm:google-auth-library@9.14.2";

export interface AutoAuthConfig {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  scopes: string[];
  tokenFile: string;
}

export class AutoAuthManager {
  private oauth2Client: OAuth2Client;
  
  constructor(private config: AutoAuthConfig) {
    this.oauth2Client = new OAuth2Client(
      config.clientId,
      config.clientSecret,
      config.redirectUri
    );
  }
  
  /**
   * 自動認証を試みる
   * 1. 保存されたトークンを探す
   * 2. あれば設定（期限切れは自動リフレッシュ）
   * 3. なければ初回認証フロー
   */
  async authenticate(): Promise<boolean> {
    try {
      // 保存されたトークンを読み込み
      const savedTokens = await this.loadTokens();
      
      if (savedTokens?.refresh_token) {
        // リフレッシュトークンがあれば設定
        this.oauth2Client.setCredentials(savedTokens);
        
        // トークンの有効性をテスト（自動リフレッシュされる）
        await this.oauth2Client.getAccessToken();
        
        console.log("✅ 自動認証成功");
        return true;
      }
    } catch (error) {
      console.log("⚠️ 保存されたトークンが無効:", error.message);
    }
    
    // 初回認証が必要
    console.log("🔐 初回認証が必要です");
    console.log(`認証URL: ${this.getAuthUrl()}`);
    return false;
  }
  
  /**
   * 初回認証（一度だけ必要）
   */
  async performInitialAuth(code: string): Promise<void> {
    const { tokens } = await this.oauth2Client.getToken(code);
    
    // トークンを保存（特にrefresh_token）
    await this.saveTokens(tokens);
    this.oauth2Client.setCredentials(tokens);
    
    console.log("✅ 初回認証完了！今後は自動認証されます");
  }
  
  /**
   * アクセストークンを取得（自動リフレッシュ付き）
   */
  async getAccessToken(): Promise<string> {
    const { token } = await this.oauth2Client.getAccessToken();
    if (!token) throw new Error('Failed to get access token');
    
    // 更新されたトークンを保存
    const credentials = this.oauth2Client.credentials;
    if (credentials) {
      await this.saveTokens(credentials);
    }
    
    return token;
  }
  
  getAuthUrl(): string {
    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: this.config.scopes,
      prompt: 'consent' // refresh_tokenを確実に取得
    });
  }
  
  getClient(): OAuth2Client {
    return this.oauth2Client;
  }
  
  private async loadTokens(): Promise<Credentials | null> {
    try {
      const data = await Deno.readTextFile(this.config.tokenFile);
      return JSON.parse(data);
    } catch {
      return null;
    }
  }
  
  private async saveTokens(tokens: Credentials): Promise<void> {
    await Deno.writeTextFile(
      this.config.tokenFile,
      JSON.stringify(tokens, null, 2)
    );
  }
}