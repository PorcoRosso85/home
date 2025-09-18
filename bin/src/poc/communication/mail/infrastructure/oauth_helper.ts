import { OAuth2Client } from "https://deno.land/x/oauth2_client@v1.0.2/mod.ts";
import { loadProviderConfig, OAuth2Config, OAuth2Provider } from "./oauth_config.ts";

// 独自定義: n8nではoauthTokenDataの一部として管理
// 参考: packages/cli/src/controllers/oauth/oauth2-credential.controller.ts:144-148
export interface TokenData {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: number;
  tokenType: string;
}

// OAuth2ヘルパークラス
// 独自実装: n8nはOAuth2CredentialControllerでサーバーサイド実装
// 参考: packages/cli/src/controllers/oauth/oauth2-credential.controller.ts
export class OAuth2Helper {
  private client: OAuth2Client;
  private config: OAuth2Config;
  private redirectUri: string;

  constructor(
    provider: string,
    redirectUri: string,
    clientId?: string,
    clientSecret?: string,
  ) {
    this.config = loadProviderConfig(provider, clientId, clientSecret);
    this.redirectUri = redirectUri;
    
    this.client = new OAuth2Client({
      clientId: this.config.clientId,
      clientSecret: this.config.clientSecret,
      authorizationEndpointUri: this.config.provider.authUrl,
      tokenUri: this.config.provider.tokenUrl,
      redirectUri: redirectUri,
      defaults: {
        scope: this.config.provider.scopes.join(" "),
      },
    });
  }

  // 認証URL生成
  // 借用元概念: packages/cli/src/controllers/oauth/oauth2-credential.controller.ts:57-83
  // 特にauthQueryParametersの処理は62-64行目
  getAuthorizationUrl(state?: string): string {
    const options: any = { state };
    
    // プロバイダー固有のクエリパラメータを追加
    if (this.config.provider.authQueryParams) {
      Object.assign(options, this.config.provider.authQueryParams);
    }
    
    const uri = this.client.code.getAuthorizationUri(options);
    return uri.toString();
  }

  // 認証コードをトークンに交換
  // 借用元概念: packages/cli/src/controllers/oauth/oauth2-credential.controller.ts:133-136
  // トークンデータのマージ処理は144-148行目
  async exchangeAuthorizationCode(
    code: string,
    state?: string,
  ): Promise<TokenData> {
    try {
      const tokens = await this.client.code.getToken(
        new URL(`${this.redirectUri}?code=${code}&state=${state || ""}`),
      );
      
      return {
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
        expiresAt: tokens.expiresIn
          ? Date.now() + tokens.expiresIn * 1000
          : undefined,
        tokenType: tokens.tokenType || "Bearer",
      };
    } catch (error) {
      throw new Error(`Failed to exchange authorization code: ${error.message}`);
    }
  }

  // トークン更新
  // 独自実装: n8nでは各ノード実行時にトークンをチェック・更新
  // 参考: packages/nodes-base/nodes/Google/Gmail/GenericFunctions.ts
  async refreshToken(refreshToken: string): Promise<TokenData> {
    try {
      const tokens = await this.client.refreshToken.refresh(refreshToken);
      return {
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
        expiresAt: tokens.expiresIn
          ? Date.now() + tokens.expiresIn * 1000
          : undefined,
        tokenType: tokens.tokenType || "Bearer",
      };
    } catch (error) {
      throw new Error(`Failed to refresh token: ${error.message}`);
    }
  }
  
  getProviderName(): string {
    return this.config.provider.name;
  }
}