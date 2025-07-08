#!/usr/bin/env -S deno run --allow-net --allow-read --allow-write --allow-env

/**
 * 自動認証対応Gmail CLI
 * 初回のみ認証、以降は完全自動
 */

import { AutoAuthManager } from "./infrastructure/auto_auth_manager.ts";
import { GmailOfficialClient } from "./infrastructure/gmail_official_client.ts";
import type { MailFetchOptions } from "./types.ts";

async function main() {
  const args = Deno.args;
  
  // 設定
  const config = {
    clientId: Deno.env.get("GOOGLE_CLIENT_ID") || "",
    clientSecret: Deno.env.get("GOOGLE_CLIENT_SECRET") || "",
    redirectUri: "http://localhost:8080/callback",
    scopes: ['https://www.googleapis.com/auth/gmail.readonly'],
    tokenFile: ".gmail_tokens.json"
  };
  
  if (!config.clientId || !config.clientSecret) {
    console.error("❌ 環境変数 GOOGLE_CLIENT_ID と GOOGLE_CLIENT_SECRET を設定してください");
    Deno.exit(1);
  }
  
  const authManager = new AutoAuthManager(config);
  
  // 初回認証コマンド
  if (args[0] === "auth" && args[1]) {
    await authManager.performInitialAuth(args[1]);
    return;
  }
  
  // 自動認証を試みる
  const authenticated = await authManager.authenticate();
  if (!authenticated) {
    console.log("\n初回認証の手順:");
    console.log("1. 上記URLをブラウザで開く");
    console.log("2. Googleアカウントでログイン");
    console.log("3. 認証後、URLから code=XXX の部分をコピー");
    console.log("4. 実行: nix run .#gmail-auto auth <コード>");
    return;
  }
  
  // メール取得（認証は自動）
  const gmail = new GmailOfficialClient(authManager.getClient());
  
  const options: MailFetchOptions = {
    account: "me",
    unreadOnly: args.includes("--unread"),
    limit: 10
  };
  
  console.log("📧 メールを取得中...");
  const emails = await gmail.fetchEmails(options);
  
  console.log(`\n取得したメール: ${emails.length}件\n`);
  
  for (const email of emails) {
    console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
    console.log(`📧 ${email.subject}`);
    console.log(`👤 ${email.fromAddress}`);
    console.log(`📅 ${email.receivedAt.toLocaleString("ja-JP")}`);
    
    if (email.bodyText) {
      const preview = email.bodyText.substring(0, 100).replace(/\n/g, " ");
      console.log(`\n${preview}${email.bodyText.length > 100 ? "..." : ""}`);
    }
  }
}

if (import.meta.main) {
  main().catch(console.error);
}