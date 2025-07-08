#!/usr/bin/env -S deno run --allow-net --allow-read --allow-write --allow-env

/**
 * 実際のGmail APIを使用するCLI実装
 * OAuth2認証フローを含む
 */

import { GmailClient } from "./infrastructure/gmail_client.ts";
import { InMemoryDatabaseAdapter } from "./infrastructure/mock_adapters.ts";
import { MailService } from "./application/mail_service.ts";
import type { Account, MailServerAdapter, MailFetchOptions, Email, Draft } from "./mod.ts";

// 環境変数から認証情報を取得
const CLIENT_ID = Deno.env.get("GOOGLE_CLIENT_ID");
const CLIENT_SECRET = Deno.env.get("GOOGLE_CLIENT_SECRET");
const REDIRECT_URI = "http://localhost:8080/callback";

// 実際のGmail APIを使用するアダプター
class RealGmailAdapter implements MailServerAdapter {
  private accessToken?: string;
  
  async authenticate(account: Account): Promise<{ success: boolean; error?: string }> {
    // ここでOAuth2フローを実行
    // 実際の実装では @n8n/client-oauth2 などのライブラリを使用
    console.log("🔐 認証が必要です。ブラウザで以下のURLを開いてください:");
    console.log(this.getAuthUrl());
    
    // 簡易的な実装：環境変数からトークンを取得
    this.accessToken = Deno.env.get("GMAIL_ACCESS_TOKEN");
    if (!this.accessToken) {
      return { 
        success: false, 
        error: "GMAIL_ACCESS_TOKEN環境変数が設定されていません" 
      };
    }
    
    return { success: true };
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
    const params = new URLSearchParams({
      client_id: CLIENT_ID || "",
      redirect_uri: REDIRECT_URI,
      response_type: "code",
      scope: "https://www.googleapis.com/auth/gmail.readonly",
      access_type: "offline",
      prompt: "consent"
    });
    
    return `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
  }
}

// メイン処理
async function main() {
  const args = Deno.args;
  
  if (args.length === 0) {
    console.log(`
Gmail CLI - 実際のGmail APIを使用

使用方法:
  deno run --allow-all cli_real.ts auth              # 認証フローを開始
  deno run --allow-all cli_real.ts fetch [options]   # メールを取得
  
必要な環境変数:
  GOOGLE_CLIENT_ID      # Google OAuth2 クライアントID
  GOOGLE_CLIENT_SECRET  # Google OAuth2 クライアントシークレット
  GMAIL_ACCESS_TOKEN    # アクセストークン（認証後に取得）

オプション:
  --unread              # 未読メールのみ
  --limit <number>      # 取得件数制限
  --since <date>        # 指定日以降のメール

例:
  export GOOGLE_CLIENT_ID="your-client-id"
  export GOOGLE_CLIENT_SECRET="your-client-secret"
  export GMAIL_ACCESS_TOKEN="your-access-token"
  
  deno run --allow-all cli_real.ts fetch --unread --limit 10
`);
    return;
  }
  
  const command = args[0];
  const db = new InMemoryDatabaseAdapter();
  const mailServer = new RealGmailAdapter();
  const mailService = new MailService(db, mailServer);
  
  // テスト用アカウント
  const account: Account = {
    id: "real-gmail",
    email: Deno.env.get("GMAIL_ACCOUNT") || "user@gmail.com",
    provider: "gmail",
    authType: "oauth2",
    createdAt: new Date(),
    updatedAt: new Date()
  };
  await db.saveAccount(account);
  
  switch (command) {
    case "auth": {
      console.log("🔐 Gmail認証を開始します...");
      const result = await mailServer.authenticate(account);
      if (result.success) {
        console.log("✅ 認証に成功しました");
      } else {
        console.error("❌ 認証に失敗しました:", result.error);
      }
      break;
    }
    
    case "fetch": {
      try {
        // 認証
        const authResult = await mailServer.authenticate(account);
        if (!authResult.success) {
          console.error("❌ 認証に失敗しました:", authResult.error);
          return;
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
        
        console.log("📧 メールを取得中...");
        const emails = await mailService.fetchEmails(options);
        
        console.log(`\n取得したメール: ${emails.length}件\n`);
        
        for (const email of emails) {
          console.log(`----------------------------------------`);
          console.log(`件名: ${email.subject}`);
          console.log(`差出人: ${email.fromAddress}`);
          console.log(`日時: ${email.receivedAt.toLocaleString("ja-JP")}`);
          console.log(`既読: ${email.isRead ? "✓" : "✗"}`);
          if (email.bodyText) {
            console.log(`\n本文:\n${email.bodyText.substring(0, 200)}...`);
          }
        }
      } catch (error) {
        console.error("❌ エラー:", error);
      }
      break;
    }
    
    default:
      console.error(`不明なコマンド: ${command}`);
  }
}

// 実行
if (import.meta.main) {
  main();
}