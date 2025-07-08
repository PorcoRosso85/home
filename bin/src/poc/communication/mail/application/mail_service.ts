/**
 * メールサービス実装
 * Application層：ビジネスロジックの実装
 */

import type { Email, MailFetchOptions, DatabaseAdapter, MailServerAdapter } from "../mod.ts";
import { filterEmails } from "../core.ts";

export class MailService {
  constructor(
    private db: DatabaseAdapter,
    private mailServer: MailServerAdapter
  ) {}
  
  /**
   * メールを取得
   */
  async fetchEmails(options: MailFetchOptions): Promise<Email[]> {
    // アカウント情報を取得
    const account = await this.db.getAccount(options.account);
    if (!account) {
      throw new Error(`Account not found: ${options.account}`);
    }
    
    try {
      // サーバーからメールを取得
      const emails = await this.mailServer.fetchEmails(account, options);
      
      // ローカルDBに保存
      if (emails.length > 0) {
        await this.db.saveEmails(emails);
      }
      
      // コアロジックでフィルタリング
      return filterEmails(emails, {
        unreadOnly: options.unreadOnly,
        since: options.since
      });
    } catch (error) {
      // オフライン時はキャッシュから取得
      console.error("Failed to fetch from server:", error);
      const cachedEmails = await this.db.getEmails(account.id, { limit: options.limit });
      
      return filterEmails(cachedEmails, {
        unreadOnly: options.unreadOnly,
        since: options.since
      });
    }
  }
}