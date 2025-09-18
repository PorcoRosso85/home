/**
 * メールCLIの実装
 * コマンドライン引数を処理してサービスを呼び出す
 */

import { MailService } from "./application/mail_service.ts";
import { InMemoryDatabaseAdapter, MockMailServerAdapter } from "./infrastructure/mock_adapters.ts";
import type { Account } from "./types.ts";

// グローバルインスタンス（テスト用）
const db = new InMemoryDatabaseAdapter();
const mailServer = new MockMailServerAdapter();
const mailService = new MailService(db, mailServer);

// テスト用アカウントを事前に追加
await db.saveAccount({
  id: "test-account",
  email: "test@gmail.com",
  provider: "gmail",
  authType: "oauth2",
  createdAt: new Date(),
  updatedAt: new Date()
});

/**
 * CLIコマンドを実行
 */
export async function runMailCommand(args: string[]): Promise<{
  success: boolean;
  output: string;
  error?: string;
}> {
  try {
    const [command, subcommand, ...options] = args;
    
    if (command === "fetch") {
      // オプションをパース
      const opts: Record<string, string | boolean> = {};
      for (let i = 0; i < options.length; i++) {
        if (options[i].startsWith("--")) {
          const key = options[i].substring(2);
          if (i + 1 < options.length && !options[i + 1].startsWith("--")) {
            opts[key] = options[i + 1];
            i++;
          } else {
            opts[key] = true;
          }
        }
      }
      
      // メール取得
      const emails = await mailService.fetchEmails({
        account: opts.account as string || "test@gmail.com",
        unreadOnly: !!opts.unread,
        since: opts.since ? new Date(opts.since as string) : undefined,
        limit: opts.limit ? parseInt(opts.limit as string) : undefined
      });
      
      // 出力フォーマット
      let output = `取得したメール: ${emails.length}件\n`;
      if (opts.unread) {
        output = `未読メール: ${emails.length}件\n`;
      }
      
      for (const email of emails) {
        output += `- ${email.subject} (${email.fromAddress})\n`;
      }
      
      return { success: true, output };
    }
    
    return { 
      success: false, 
      output: "", 
      error: `Unknown command: ${command}` 
    };
  } catch (error) {
    return { 
      success: false, 
      output: "", 
      error: error instanceof Error ? error.message : String(error) 
    };
  }
}