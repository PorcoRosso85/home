/**
 * テスト用のモックアダプター実装
 * Infrastructure層：テスト用の実装
 */

import type { Account, Email, Draft, MailFetchOptions, DatabaseAdapter, MailServerAdapter } from "../mod.ts";

/**
 * インメモリデータベースアダプター
 */
export class InMemoryDatabaseAdapter implements DatabaseAdapter {
  private accounts = new Map<string, Account>();
  private emails = new Map<string, Email[]>();
  private drafts = new Map<string, Draft>();
  
  async saveAccount(account: Account): Promise<void> {
    this.accounts.set(account.email, account);
  }
  
  async getAccount(email: string): Promise<Account | null> {
    return this.accounts.get(email) || null;
  }
  
  async listAccounts(): Promise<Account[]> {
    return Array.from(this.accounts.values());
  }
  
  async deleteAccount(email: string): Promise<void> {
    this.accounts.delete(email);
  }
  
  async saveEmails(emails: Email[]): Promise<void> {
    for (const email of emails) {
      const accountEmails = this.emails.get(email.accountId) || [];
      accountEmails.push(email);
      this.emails.set(email.accountId, accountEmails);
    }
  }
  
  async getEmails(accountId: string, options?: { limit?: number }): Promise<Email[]> {
    const emails = this.emails.get(accountId) || [];
    if (options?.limit) {
      return emails.slice(0, options.limit);
    }
    return emails;
  }
  
  async markEmailAsRead(emailId: string): Promise<void> {
    for (const accountEmails of this.emails.values()) {
      const email = accountEmails.find(e => e.id === emailId);
      if (email) {
        email.isRead = true;
        break;
      }
    }
  }
  
  async saveDraft(draft: Draft): Promise<void> {
    this.drafts.set(draft.id, draft);
  }
  
  async getDraft(draftId: string): Promise<Draft | null> {
    return this.drafts.get(draftId) || null;
  }
  
  async listDrafts(accountId: string): Promise<Draft[]> {
    return Array.from(this.drafts.values()).filter(d => d.accountId === accountId);
  }
  
  async deleteDraft(draftId: string): Promise<void> {
    this.drafts.delete(draftId);
  }
  
  async updateDraft(draftId: string, updates: Partial<Draft>): Promise<void> {
    const draft = this.drafts.get(draftId);
    if (draft) {
      Object.assign(draft, updates, { updatedAt: new Date() });
    }
  }
}

/**
 * モックメールサーバーアダプター
 */
export class MockMailServerAdapter implements MailServerAdapter {
  private mockEmails: Email[] = [
    {
      id: "1",
      accountId: "test-account",
      messageId: "msg-1",
      subject: "Test Email 1",
      fromAddress: "sender1@example.com",
      toAddresses: ["test@gmail.com"],
      bodyText: "This is test email 1",
      headers: {
        "subject": "Test Email 1",
        "from": "sender1@example.com",
        "to": "test@gmail.com"
      },
      isRead: false,
      receivedAt: new Date("2024-01-01")
    },
    {
      id: "2",
      accountId: "test-account",
      messageId: "msg-2",
      subject: "Test Email 2",
      fromAddress: "sender2@example.com",
      toAddresses: ["test@gmail.com"],
      bodyText: "This is test email 2",
      headers: {
        "subject": "Test Email 2",
        "from": "sender2@example.com",
        "to": "test@gmail.com"
      },
      isRead: true,
      receivedAt: new Date("2024-01-02")
    }
  ];
  
  async authenticate(account: Account): Promise<{ success: boolean; error?: string }> {
    // モックなので常に成功
    return { success: true };
  }
  
  async fetchEmails(account: Account, options: MailFetchOptions): Promise<Email[]> {
    // アカウントIDを設定
    const emails = this.mockEmails.map(e => ({ ...e, accountId: account.id }));
    
    // フィルタリング
    let filtered = emails;
    
    if (options.unreadOnly) {
      filtered = filtered.filter(e => !e.isRead);
    }
    
    if (options.since) {
      filtered = filtered.filter(e => e.receivedAt >= options.since!);
    }
    
    if (options.limit) {
      filtered = filtered.slice(0, options.limit);
    }
    
    return filtered;
  }
  
  async sendEmail(account: Account, draft: Draft): Promise<{ success: boolean; messageId?: string }> {
    return { success: true, messageId: `sent-${Date.now()}` };
  }
}