#!/usr/bin/env -S deno run --allow-net --allow-read --allow-write --allow-env

/**
 * Gmail CLI - 自動認証版
 * トークンをローカルに保存し、期限切れ時は自動更新
 */

import { GmailClient } from "./infrastructure/gmail_client.ts";
import { InMemoryDatabaseAdapter } from "./infrastructure/mock_adapters.ts";
import { MailService } from "./application/mail_service.ts";
import type { Account, MailServerAdapter, MailFetchOptions, Email, Draft } from "./mod.ts";

const TOKEN_FILE = ".gmail_token.json";
const CLIENT_ID = Deno.env.get("GOOGLE_CLIENT_ID");
const CLIENT_SECRET = Deno.env.get("GOOGLE_CLIENT_SECRET");
const REDIRECT_URI = "http://localhost:8080/callback";

interface TokenData {
  access_token: string;
  refresh_token?: string;
  expires_at: number;
}

// トークン管理クラス
class TokenManager {
  async loadToken(): Promise<TokenData | null> {
    try {
      const data = await Deno.readTextFile(TOKEN_FILE);
      return JSON.parse(data);
    } catch {
      return null;
    }
  }
  
  async saveToken(token: TokenData): Promise<void> {
    await Deno.writeTextFile(TOKEN_FILE, JSON.stringify(token, null, 2));
  }
  
  async refreshToken(refreshToken: string): Promise<TokenData> {
    const response = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: CLIENT_ID!,
        client_secret: CLIENT_SECRET!,
        refresh_token: refreshToken,
        grant_type: "refresh_token"
      })
    });
    
    if (!response.ok) {
      throw new Error(`Token refresh failed: ${await response.text()}`);
    }
    
    const data = await response.json();
    const newToken: TokenData = {
      access_token: data.access_token,
      refresh_token: refreshToken, // リフレッシュトークンは変わらない
      expires_at: Date.now() + (data.expires_in * 1000)
    };
    
    await this.saveToken(newToken);
    return newToken;
  }
  
  async getValidToken(): Promise<string | null> {
    const token = await this.loadToken();
    if (!token) return null;
    
    // 期限切れチェック（5分前に更新）
    if (token.expires_at - Date.now() < 5 * 60 * 1000) {
      if (token.refresh_token) {
        console.log("🔄 トークンを更新中...");
        const newToken = await this.refreshToken(token.refresh_token);
        return newToken.access_token;
      }
      return null;
    }
    
    return token.access_token;
  }
}

// 自動認証対応のGmailアダプター
class AutoAuthGmailAdapter implements MailServerAdapter {
  private tokenManager = new TokenManager();
  private accessToken?: string;
  
  async authenticate(account: Account): Promise<{ success: boolean; error?: string }> {
    // 既存のトークンをチェック
    const token = await this.tokenManager.getValidToken();
    if (token) {
      this.accessToken = token;
      return { success: true };
    }
    
    // トークンがない場合は認証フローを開始
    console.log("🔐 認証が必要です。");
    console.log("\n以下の手順で認証してください:");
    console.log("\n1. 別のターミナルで以下を実行:");
    console.log("   nix run .#oauth -- server");
    console.log("\n2. 以下のURLをブラウザで開く:");
    console.log(`   ${this.getAuthUrl()}`);
    console.log("\n3. Googleアカウントでログインし、権限を許可");
    console.log("\n4. 表示された認証コードをコピー");
    console.log("\n5. 以下のコマンドを実行:");
    console.log("   nix run .#gmail -- auth --code <認証コード>");
    
    return { 
      success: false, 
      error: "認証が必要です。上記の手順に従ってください。" 
    };
  }
  
  async fetchEmails(account: Account, options: MailFetchOptions): Promise<Email[]> {
    if (!this.accessToken) {
      throw new Error("認証されていません");
    }
    
    const client = new GmailClient(this.accessToken);
    return client.fetchEmails(options);
  }
  
  async sendEmail(account: Account, draft: Draft): Promise<{ success: boolean; messageId?: string }> {
    throw new Error("送信は未実装");
  }
  
  private getAuthUrl(): string {
    if (!CLIENT_ID) {
      return "エラー: GOOGLE_CLIENT_ID が設定されていません";
    }
    
    const params = new URLSearchParams({
      client_id: CLIENT_ID,
      redirect_uri: REDIRECT_URI,
      response_type: "code",
      scope: "https://www.googleapis.com/auth/gmail.readonly",
      access_type: "offline",
      prompt: "consent"
    });
    
    return `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
  }
  
  async exchangeCodeForToken(code: string): Promise<void> {
    const response = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        code,
        client_id: CLIENT_ID!,
        client_secret: CLIENT_SECRET!,
        redirect_uri: REDIRECT_URI,
        grant_type: "authorization_code"
      })
    });
    
    if (!response.ok) {
      throw new Error(`Token exchange failed: ${await response.text()}`);
    }
    
    const data = await response.json();
    const token: TokenData = {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      expires_at: Date.now() + (data.expires_in * 1000)
    };
    
    await this.tokenManager.saveToken(token);
    this.accessToken = token.access_token;
    
    console.log("✅ 認証に成功しました！トークンを保存しました。");
  }
}

// メイン処理
async function main() {
  const args = Deno.args;
  
  // 環境変数チェック
  if (!CLIENT_ID || !CLIENT_SECRET) {
    console.error("❌ エラー: 環境変数が設定されていません");
    console.error("\n以下の環境変数を設定してください:");
    console.error("  export GOOGLE_CLIENT_ID='your-client-id'");
    console.error("  export GOOGLE_CLIENT_SECRET='your-client-secret'");
    console.error("\n詳細は GMAIL_SETUP.md を参照してください。");
    Deno.exit(1);
  }
  
  const db = new InMemoryDatabaseAdapter();
  const mailServer = new AutoAuthGmailAdapter();
  const mailService = new MailService(db, mailServer);
  
  // アカウント設定
  const account: Account = {
    id: "gmail-auto",
    email: Deno.env.get("GMAIL_ACCOUNT") || "user@gmail.com",
    provider: "gmail",
    authType: "oauth2",
    createdAt: new Date(),
    updatedAt: new Date()
  };
  await db.saveAccount(account);
  
  // コマンドなしまたは fetch の場合はメール取得
  if (args.length === 0 || args[0] === "fetch") {
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
      console.log("📧 メールを取得中...");
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
      console.error("❌ エラー:", error);
      Deno.exit(1);
    }
  }
  
  // 認証コマンド
  else if (args[0] === "auth") {
    if (args[1] === "--code" && args[2]) {
      // 認証コードをトークンに交換
      try {
        await mailServer.exchangeCodeForToken(args[2]);
      } catch (error) {
        console.error("❌ トークン交換エラー:", error);
        Deno.exit(1);
      }
    } else {
      // 認証フローを開始
      const authResult = await mailServer.authenticate(account);
      if (authResult.success) {
        console.log("✅ 既に認証済みです。");
      }
    }
  }
  
  // ヘルプ
  else if (args[0] === "help" || args[0] === "--help") {
    console.log(`
Gmail CLI - 自動認証版

使用方法:
  nix run .#gmail                    # メールを取得（認証済みの場合）
  nix run .#gmail fetch [options]    # メールを取得
  nix run .#gmail auth               # 認証状態を確認
  nix run .#gmail auth --code <code> # 認証コードでトークンを取得

オプション:
  --unread              # 未読メールのみ
  --limit <number>      # 取得件数制限
  --since <date>        # 指定日以降のメール

例:
  nix run .#gmail fetch --unread --limit 5
  nix run .#gmail fetch --since 2024-01-01
`);
  }
  
  else {
    console.error(`❌ 不明なコマンド: ${args[0]}`);
    console.error(`ヘルプを表示: nix run .#gmail help`);
    Deno.exit(1);
  }
}

// 実行
if (import.meta.main) {
  main();
}