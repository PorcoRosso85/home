/**
 * メールサービス実装
 * Application層：ビジネスロジックの実装
 */

import type { Email, MailFetchOptions, DatabaseAdapter, MailServerAdapter } from "../mod.ts";
import { filterEmails } from "../core.ts";
import { Result } from "../utils/result.ts";
import { Logger } from "../utils/logger.ts";

export class MailService {
  private logger: Logger;

  constructor(
    private db: DatabaseAdapter,
    private mailServer: MailServerAdapter
  ) {
    this.logger = new Logger("MailService");
  }
  
  /**
   * メールを取得
   */
  async fetchEmails(options: MailFetchOptions): Promise<Result<Email[]>> {
    this.logger.info("Fetching emails", { account: options.account, options });

    // アカウント情報を取得
    const account = await this.db.getAccount(options.account);
    if (!account) {
      this.logger.error("Account not found", undefined, { account: options.account });
      return Result.error(
        "ACCOUNT_NOT_FOUND",
        `Account not found: ${options.account}`
      );
    }

    // サーバーからメールを取得
    const fetchResult = await this.fetchFromServer(account, options);
    
    if (fetchResult.ok) {
      // 成功時はローカルDBに保存
      const emails = fetchResult.data;
      if (emails.length > 0) {
        const saveResult = await this.saveEmailsToCache(emails);
        if (!saveResult.ok) {
          this.logger.warn("Failed to save emails to cache", { error: saveResult.error });
        }
      }

      // コアロジックでフィルタリング
      const filtered = filterEmails(emails, {
        unreadOnly: options.unreadOnly,
        since: options.since
      });

      this.logger.info("Emails fetched successfully", { 
        total: emails.length,
        filtered: filtered.length 
      });

      return Result.ok(filtered);
    }

    // エラー時はキャッシュから取得を試みる
    this.logger.warn("Failed to fetch from server, trying cache", { 
      error: fetchResult.error 
    });

    return this.fetchFromCache(account.id, options);
  }

  private async fetchFromServer(
    account: any,
    options: MailFetchOptions
  ): Promise<Result<Email[]>> {
    try {
      const emails = await this.mailServer.fetchEmails(account, options);
      return Result.ok(emails);
    } catch (error) {
      return Result.error(
        "FETCH_ERROR",
        "Failed to fetch emails from server",
        error
      );
    }
  }

  private async saveEmailsToCache(emails: Email[]): Promise<Result<void>> {
    try {
      await this.db.saveEmails(emails);
      return Result.ok(undefined);
    } catch (error) {
      return Result.error(
        "CACHE_SAVE_ERROR",
        "Failed to save emails to cache",
        error
      );
    }
  }

  private async fetchFromCache(
    accountId: string,
    options: MailFetchOptions
  ): Promise<Result<Email[]>> {
    try {
      const cachedEmails = await this.db.getEmails(accountId, { 
        limit: options.limit 
      });

      const filtered = filterEmails(cachedEmails, {
        unreadOnly: options.unreadOnly,
        since: options.since
      });

      this.logger.info("Emails fetched from cache", { 
        total: cachedEmails.length,
        filtered: filtered.length 
      });

      return Result.ok(filtered);
    } catch (error) {
      return Result.error(
        "CACHE_FETCH_ERROR",
        "Failed to fetch emails from cache",
        error
      );
    }
  }
}