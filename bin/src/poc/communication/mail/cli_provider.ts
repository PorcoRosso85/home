#!/usr/bin/env -S deno run --allow-net --allow-read --allow-write --allow-env

/**
 * プロバイダー対応メールCLI
 * 複数のメールプロバイダーに対応し、id/secretペアをCLI引数で渡せる
 */

import { GmailClient } from "./infrastructure/gmail_client.ts";
import { InMemoryDatabaseAdapter } from "./infrastructure/mock_adapters.ts";
import { MailService } from "./application/mail_service.ts";
import { OAuth2Helper, TokenData } from "./infrastructure/oauth_helper.ts";
import { OAUTH2_PROVIDERS } from "./infrastructure/oauth_config.ts";
import type { Account, MailServerAdapter, MailFetchOptions, Email, Draft } from "./mod.ts";

const REDIRECT_URI = "http://localhost:8080/callback";

// プロバイダー別のトークンファイル
function getTokenFile(provider: string): string {
  return `.${provider}_token.json`;
}

// トークン管理クラス（プロバイダー対応版）
class TokenManager {
  constructor(private provider: string) {}
  
  async loadToken(): Promise<TokenData | null> {
    try {
      const data = await Deno.readTextFile(getTokenFile(this.provider));
      return JSON.parse(data);
    } catch {
      return null;
    }
  }
  
  async saveToken(token: TokenData): Promise<void> {
    await Deno.writeTextFile(
      getTokenFile(this.provider),
      JSON.stringify(token, null, 2)
    );
  }
  
  async getValidToken(oauth: OAuth2Helper): Promise<string | null> {
    const token = await this.loadToken();
    if (!token) return null;
    
    // 期限切れチェック（5分前に更新）
    if (token.expiresAt && token.expiresAt - Date.now() < 5 * 60 * 1000) {
      if (token.refreshToken) {
        console.log("🔄 トークンを更新中...");
        const newToken = await oauth.refreshToken(token.refreshToken);
        await this.saveToken(newToken);
        return newToken.accessToken;
      }
      return null;
    }
    
    return token.accessToken;
  }
}

// プロバイダー対応のメールアダプター
class ProviderMailAdapter implements MailServerAdapter {
  private tokenManager: TokenManager;
  private oauth: OAuth2Helper;
  private accessToken?: string;
  
  constructor(
    private provider: string,
    clientId?: string,
    clientSecret?: string
  ) {
    this.tokenManager = new TokenManager(provider);
    this.oauth = new OAuth2Helper(provider, REDIRECT_URI, clientId, clientSecret);
  }
  
  async authenticate(account: Account): Promise<{ success: boolean; error?: string }> {
    // 既存のトークンをチェック
    const token = await this.tokenManager.getValidToken(this.oauth);
    if (token) {
      this.accessToken = token;
      return { success: true };
    }
    
    // トークンがない場合は認証フローを開始
    console.log("🔐 認証が必要です。");
    console.log(`\n${this.oauth.getProviderName()}の認証手順:`);
    console.log("\n1. 別のターミナルで以下を実行:");
    console.log("   nix run .#oauth -- server");
    console.log("\n2. 以下のURLをブラウザで開く:");
    console.log(`   ${this.oauth.getAuthorizationUrl("auth-state")}`);
    console.log(`\n3. ${this.oauth.getProviderName()}アカウントでログインし、権限を許可`);
    console.log("\n4. 表示された認証コードをコピー");
    console.log("\n5. 以下のコマンドを実行:");
    console.log(`   nix run .#mail -- ${this.provider} auth --code <認証コード>`);
    
    return { 
      success: false, 
      error: "認証が必要です。上記の手順に従ってください。" 
    };
  }
  
  async fetchEmails(account: Account, options: MailFetchOptions): Promise<Email[]> {
    if (!this.accessToken) {
      throw new Error("認証されていません");
    }
    
    // 現在はGmailのみサポート
    if (this.provider === "gmail") {
      const client = new GmailClient(this.accessToken);
      return client.fetchEmails(options);
    } else {
      throw new Error(`${this.provider}のメール取得は未実装です`);
    }
  }
  
  async sendEmail(account: Account, draft: Draft): Promise<{ success: boolean; messageId?: string }> {
    throw new Error("送信は未実装");
  }
  
  async exchangeCodeForToken(code: string): Promise<void> {
    const token = await this.oauth.exchangeAuthorizationCode(code, "auth-state");
    await this.tokenManager.saveToken(token);
    this.accessToken = token.accessToken;
    
    console.log(`✅ ${this.oauth.getProviderName()}の認証に成功しました！`);
  }
}

// メイン処理
async function main() {
  const args = Deno.args;
  
  // ヘルプ表示
  if (args.length === 0 || args[0] === "help" || args[0] === "--help") {
    console.log(`
プロバイダー対応メールCLI

使用方法:
  nix run .#mail -- <provider> [command] [options]

プロバイダー:
  ${Object.keys(OAUTH2_PROVIDERS).join(", ")}

コマンド:
  fetch [options]        # メールを取得
  auth                   # 認証状態を確認
  auth --code <code>     # 認証コードでトークンを取得

オプション:
  --client-id <id>       # OAuth2 Client ID（環境変数より優先）
  --client-secret <sec>  # OAuth2 Client Secret（環境変数より優先）
  --unread               # 未読メールのみ
  --limit <number>       # 取得件数制限
  --since <date>         # 指定日以降のメール

環境変数:
  <PROVIDER>_CLIENT_ID     # プロバイダーのClient ID（例: GMAIL_CLIENT_ID）
  <PROVIDER>_CLIENT_SECRET # プロバイダーのClient Secret

例:
  # Gmail
  nix run .#mail -- gmail fetch --unread --limit 5
  nix run .#mail -- gmail auth --code abc123
  
  # Outlook（CLI引数でID/Secret指定）
  nix run .#mail -- outlook fetch \\
    --client-id "your-id" \\
    --client-secret "your-secret"
`);
    return;
  }
  
  // プロバイダーを取得
  const provider = args[0].toLowerCase();
  if (!OAUTH2_PROVIDERS[provider]) {
    console.error(`❌ 不明なプロバイダー: ${provider}`);
    console.error(`対応プロバイダー: ${Object.keys(OAUTH2_PROVIDERS).join(", ")}`);
    Deno.exit(1);
  }
  
  // Client ID/Secretを取得（CLI引数優先）
  let clientId: string | undefined;
  let clientSecret: string | undefined;
  
  const clientIdIndex = args.indexOf("--client-id");
  if (clientIdIndex !== -1 && args[clientIdIndex + 1]) {
    clientId = args[clientIdIndex + 1];
  }
  
  const clientSecretIndex = args.indexOf("--client-secret");
  if (clientSecretIndex !== -1 && args[clientSecretIndex + 1]) {
    clientSecret = args[clientSecretIndex + 1];
  }
  
  // アダプターとサービスを初期化
  const db = new InMemoryDatabaseAdapter();
  const mailServer = new ProviderMailAdapter(provider, clientId, clientSecret);
  const mailService = new MailService(db, mailServer);
  
  // アカウント設定
  const account: Account = {
    id: `${provider}-auto`,
    email: Deno.env.get(`${provider.toUpperCase()}_ACCOUNT`) || `user@${provider}.com`,
    provider: provider,
    authType: "oauth2",
    createdAt: new Date(),
    updatedAt: new Date()
  };
  await db.saveAccount(account);
  
  // コマンド処理
  const command = args[1] || "fetch";
  
  // 認証コマンド
  if (command === "auth") {
    const codeIndex = args.indexOf("--code");
    if (codeIndex !== -1 && args[codeIndex + 1]) {
      // 認証コードをトークンに交換
      try {
        await mailServer.exchangeCodeForToken(args[codeIndex + 1]);
      } catch (error) {
        console.error("❌ トークン交換エラー:", error.message);
        Deno.exit(1);
      }
    } else {
      // 認証フローを開始
      const authResult = await mailServer.authenticate(account);
      if (authResult.success) {
        console.log(`✅ ${provider}は既に認証済みです。`);
      }
    }
  }
  
  // メール取得コマンド
  else if (command === "fetch") {
    // 認証チェック
    const authResult = await mailServer.authenticate(account);
    if (!authResult.success) {
      console.error("❌", authResult.error);
      Deno.exit(1);
    }
    
    // オプションをパース
    const options: MailFetchOptions = {
      account: account.email,
      unreadOnly: args.includes("--unread"),
      limit: undefined,
      since: undefined
    };
    
    const limitIndex = args.indexOf("--limit");
    if (limitIndex !== -1 && args[limitIndex + 1]) {
      options.limit = parseInt(args[limitIndex + 1]);
    }
    
    const sinceIndex = args.indexOf("--since");
    if (sinceIndex !== -1 && args[sinceIndex + 1]) {
      options.since = new Date(args[sinceIndex + 1]);
    }
    
    try {
      console.log(`📧 ${provider}のメールを取得中...`);
      const emails = await mailService.fetchEmails(options);
      
      console.log(`\n✅ 取得したメール: ${emails.length}件\n`);
      
      for (const email of emails) {
        console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        console.log(`📧 ${email.subject}`);
        console.log(`👤 ${email.fromAddress}`);
        console.log(`📅 ${email.receivedAt.toLocaleString("ja-JP")}`);
        console.log(`📖 ${email.isRead ? "既読" : "未読"}`);
        
        if (email.bodyText && email.bodyText.length > 0) {
          const preview = email.bodyText.substring(0, 100).replace(/\n/g, " ");
          console.log(`\n${preview}${email.bodyText.length > 100 ? "..." : ""}`);
        }
      }
      
      if (emails.length === 0) {
        console.log("メールが見つかりませんでした。");
      }
    } catch (error) {
      console.error("❌ エラー:", error.message);
      Deno.exit(1);
    }
  }
  
  else {
    console.error(`❌ 不明なコマンド: ${command}`);
    console.error(`ヘルプを表示: nix run .#mail help`);
    Deno.exit(1);
  }
}

// 実行
if (import.meta.main) {
  main().catch(error => {
    console.error("❌ 予期しないエラー:", error);
    Deno.exit(1);
  });
}