/**
 * Gmail公式APIクライアント
 * googleapis（Apache 2.0）を使用した実装
 */

import { google, gmail_v1 } from "npm:googleapis@144.0.0";
import type { OAuth2Client } from "npm:google-auth-library@9.14.2";
import type { Email, MailFetchOptions } from "../types.ts";

export class GmailOfficialClient {
  private gmail: gmail_v1.Gmail;
  
  constructor(auth: OAuth2Client) {
    this.gmail = google.gmail({ version: 'v1', auth });
  }
  
  /**
   * メール一覧を取得
   */
  async fetchEmails(options: MailFetchOptions): Promise<Email[]> {
    const query: string[] = [];
    
    if (options.unreadOnly) {
      query.push('is:unread');
    }
    
    if (options.since) {
      const dateStr = options.since.toISOString().split('T')[0];
      query.push(`after:${dateStr}`);
    }
    
    // メッセージ一覧を取得
    const response = await this.gmail.users.messages.list({
      userId: 'me',
      q: query.join(' '),
      maxResults: options.limit
    });
    
    if (!response.data.messages) {
      return [];
    }
    
    // 各メッセージの詳細を取得
    const emails: Email[] = [];
    for (const message of response.data.messages) {
      if (!message.id) continue;
      
      const detail = await this.gmail.users.messages.get({
        userId: 'me',
        id: message.id,
        format: 'full'
      });
      
      if (detail.data) {
        const email = this.convertToEmail(detail.data);
        emails.push(email);
      }
    }
    
    return emails;
  }
  
  /**
   * Gmailメッセージを内部Email型に変換
   */
  private convertToEmail(message: gmail_v1.Schema$Message): Email {
    const headers = this.extractHeaders(message);
    const body = this.extractBody(message);
    
    return {
      id: message.id || '',
      accountId: 'gmail',
      messageId: message.id || '',
      subject: headers['subject'] || '(no subject)',
      fromAddress: headers['from'] || '',
      toAddresses: headers['to'] ? headers['to'].split(',').map(s => s.trim()) : [],
      ccAddresses: headers['cc'] ? headers['cc'].split(',').map(s => s.trim()) : undefined,
      bodyText: body.text,
      bodyHtml: body.html,
      headers: headers,
      isRead: !message.labelIds?.includes('UNREAD'),
      receivedAt: new Date(parseInt(message.internalDate || '0'))
    };
  }
  
  /**
   * ヘッダーを抽出
   */
  private extractHeaders(message: gmail_v1.Schema$Message): Record<string, string> {
    const headers: Record<string, string> = {};
    
    if (message.payload?.headers) {
      for (const header of message.payload.headers) {
        if (header.name && header.value) {
          headers[header.name.toLowerCase()] = header.value;
        }
      }
    }
    
    return headers;
  }
  
  /**
   * メール本文を抽出
   */
  private extractBody(message: gmail_v1.Schema$Message): { text?: string; html?: string } {
    const body: { text?: string; html?: string } = {};
    
    const findParts = (part: gmail_v1.Schema$MessagePart): void => {
      if (part.mimeType === 'text/plain' && part.body?.data) {
        body.text = Buffer.from(part.body.data, 'base64').toString();
      } else if (part.mimeType === 'text/html' && part.body?.data) {
        body.html = Buffer.from(part.body.data, 'base64').toString();
      }
      
      if (part.parts) {
        for (const subPart of part.parts) {
          findParts(subPart);
        }
      }
    };
    
    if (message.payload) {
      findParts(message.payload);
    }
    
    return body;
  }
}