#!/usr/bin/env -S deno run --allow-net --allow-read --allow-write --allow-env --allow-run

/**
 * 完全自動認証Gmail CLI
 * ブラウザを自動で開いてコードも自動取得
 */

import { AutoAuthManager } from "./infrastructure/auto_auth_manager.ts";
import { GmailOfficialClient } from "./infrastructure/gmail_official_client.ts";
import type { MailFetchOptions } from "./types.ts";

/**
 * コールバックサーバーを起動して認証コードを自動取得
 */
async function getAuthCodeAutomatically(authUrl: string): Promise<string | null> {
  let resolveCode: (code: string | null) => void;
  const codePromise = new Promise<string | null>((resolve) => {
    resolveCode = resolve;
  });
  
  const server = Deno.serve({ port: 8080 }, async (req) => {
    const url = new URL(req.url);
    
    if (url.pathname === "/callback") {
      const code = url.searchParams.get("code");
      const error = url.searchParams.get("error");
      
      if (error) {
        const html = `
          <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
              <h1>❌ 認証エラー</h1>
              <p>${error}</p>
            </body>
          </html>
        `;
        resolveCode(null);
        setTimeout(() => server.shutdown(), 100);
        return new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8" } });
      }
      
      if (code) {
        const html = `
          <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
              <h1>✅ 認証成功！</h1>
              <p>このタブは閉じて構いません。</p>
              <script>setTimeout(() => window.close(), 2000);</script>
            </body>
          </html>
        `;
        resolveCode(code);
        setTimeout(() => server.shutdown(), 100);
        return new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8" } });
      }
    }
    
    return new Response("Not found", { status: 404 });
  });
  
  console.log("\n🌐 ブラウザを開いています...");
  
  // ブラウザを自動で開く
  const openCommand = Deno.build.os === "darwin" ? "open" : 
                     Deno.build.os === "windows" ? "start" : "xdg-open";
  
  try {
    const command = new Deno.Command(openCommand, { args: [authUrl] });
    await command.output();
  } catch (e) {
    console.log("\n⚠️  ブラウザを自動で開けませんでした。");
    console.log("以下のURLを手動で開いてください:");
    console.log(authUrl);
  }
  
  console.log("\n⏳ 認証を待っています...");
  
  // コードを待つ
  const code = await codePromise;
  await server.shutdown();
  
  return code;
}

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
  
  // 自動認証を試みる
  const authenticated = await authManager.authenticate();
  if (!authenticated) {
    console.log("\n🔐 初回認証を開始します...");
    
    // 認証URLを取得
    const authUrl = authManager.getAuthUrl();
    
    // ブラウザを開いてコードを自動取得
    const code = await getAuthCodeAutomatically(authUrl);
    
    if (!code) {
      console.error("❌ 認証がキャンセルされました");
      Deno.exit(1);
    }
    
    // トークンを保存
    await authManager.performInitialAuth(code);
    console.log("\n✅ 認証完了！メールを取得します...\n");
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