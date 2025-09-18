// OAuth2プロバイダー設定
// 独自実装: n8nは各プロバイダーを個別のcredentialファイルで管理
// 参考: packages/nodes-base/credentials/GoogleOAuth2Api.credentials.ts等
export interface OAuth2Provider {
  name: string;
  authUrl: string;
  tokenUrl: string;
  scopes: string[];
  authQueryParams?: Record<string, string>;
}

export interface OAuth2Config {
  clientId: string;
  clientSecret: string;
  provider: OAuth2Provider;
}

// プロバイダー定義
export const OAUTH2_PROVIDERS: Record<string, OAuth2Provider> = {
  gmail: {
    name: "Gmail",
    // 借用元: packages/nodes-base/credentials/GoogleOAuth2Api.credentials.ts:25
    authUrl: "https://accounts.google.com/o/oauth2/v2/auth",
    // 借用元: packages/nodes-base/credentials/GoogleOAuth2Api.credentials.ts:31
    tokenUrl: "https://oauth2.googleapis.com/token",
    // 借用元: packages/nodes-base/credentials/GmailOAuth2Api.credentials.ts:3-10
    scopes: [
      "https://www.googleapis.com/auth/gmail.labels",
      "https://mail.google.com/",
      "https://www.googleapis.com/auth/gmail.modify",
      "https://www.googleapis.com/auth/gmail.compose",
    ],
    // 借用元: packages/nodes-base/credentials/GoogleOAuth2Api.credentials.ts:37
    authQueryParams: {
      access_type: "offline",
      prompt: "consent",
    },
  },
  outlook: {
    name: "Outlook",
    authUrl: "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    tokenUrl: "https://login.microsoftonline.com/common/oauth2/v2.0/token",
    scopes: [
      "https://outlook.office.com/Mail.Read",
      "https://outlook.office.com/Mail.Send",
      "offline_access",
    ],
  },
  yahoo: {
    name: "Yahoo Mail",
    authUrl: "https://api.login.yahoo.com/oauth2/request_auth",
    tokenUrl: "https://api.login.yahoo.com/oauth2/get_token",
    scopes: ["mail-r", "mail-w"],
  },
};

// プロバイダー設定を環境変数またはCLI引数から読み込む
// 独自実装: n8nはDBに暗号化保存、CLIでは環境変数/引数で管理
// 参考にした概念: packages/cli/src/controllers/oauth/oauth2-credential.controller.ts
export function loadProviderConfig(
  provider: string,
  clientId?: string,
  clientSecret?: string,
): OAuth2Config {
  const providerConfig = OAUTH2_PROVIDERS[provider.toLowerCase()];
  if (!providerConfig) {
    throw new Error(
      `Unknown provider: ${provider}. Available: ${Object.keys(OAUTH2_PROVIDERS).join(", ")}`,
    );
  }

  // CLI引数優先、なければ環境変数から読み込み
  const id = clientId || Deno.env.get(`${provider.toUpperCase()}_CLIENT_ID`);
  const secret = clientSecret ||
    Deno.env.get(`${provider.toUpperCase()}_CLIENT_SECRET`);

  if (!id || !secret) {
    throw new Error(
      `Missing OAuth2 credentials for ${provider}. ` +
        `Provide via CLI args or environment variables: ` +
        `${provider.toUpperCase()}_CLIENT_ID and ${provider.toUpperCase()}_CLIENT_SECRET`,
    );
  }

  return {
    clientId: id,
    clientSecret: secret,
    provider: providerConfig,
  };
}
